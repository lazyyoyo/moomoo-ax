"""Codex worker log normalization for v0.4 Track B.

Converts one-shot Codex worker logs into stable executor/reviewer result.json
contracts that Claude conductor can consume.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def parse_events(path: Path) -> tuple[list[dict], list[str]]:
    if not path.exists():
        return [], []

    events: list[dict] = []
    invalid: list[str] = []
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                invalid.append(line)
    return events, invalid


def load_meta(path: Path) -> dict:
    if not path.exists():
        return {
            "status": "incomplete",
            "partial": True,
            "exit_code": None,
            "duration_sec": None,
            "codex_version": None,
        }
    return read_json(path)


def extract_json_object(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            data = json.loads(fenced.group(1))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    return None


def extract_agent_messages(events: list[dict]) -> list[str]:
    messages: list[str] = []
    for evt in events:
        if evt.get("type") != "item.completed":
            continue
        item = evt.get("item") or {}
        if item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            messages.append(text.strip())
    return messages


def summarize_log(log_dir: Path) -> dict:
    meta_path = log_dir / "meta.json"
    events_path = log_dir / "events.jsonl"
    last_message_path = log_dir / "last-message.txt"

    meta = load_meta(meta_path)
    events, invalid = parse_events(events_path)
    last_message = read_text(last_message_path) if last_message_path.exists() else ""
    agent_messages = extract_agent_messages(events)
    combined_text = "\n".join([*agent_messages, last_message]).lower()
    sandbox_block = "sandbox blocked" in combined_text

    thread_id = None
    usage = None
    for evt in events:
        if evt.get("type") == "thread.started":
            thread_id = evt.get("thread_id")
        if evt.get("type") == "turn.completed":
            usage = evt.get("usage")

    status = meta.get("status") or "success"
    if status in {"stopped", "incomplete"}:
        pass
    elif meta.get("exit_code") is None:
        status = "incomplete"
    elif meta.get("exit_code") != 0:
        status = "error"
    elif sandbox_block:
        status = "sandbox_block"
    else:
        status = "success"

    return {
        "status": status,
        "exit_code": meta.get("exit_code"),
        "duration_sec": meta.get("duration_sec"),
        "codex_version": meta.get("codex_version"),
        "partial": bool(meta.get("partial", False)),
        "thread_id": thread_id,
        "usage": usage,
        "event_count": len(events),
        "invalid_event_lines": len(invalid),
        "event_types": dict(Counter(evt.get("type", "<missing>") for evt in events)),
        "sandbox_block": sandbox_block,
        "last_message": last_message,
    }


def _executor_error(task_id: str, summary: str) -> dict:
    return {
        "role": "executor",
        "status": "infra_error",
        "summary": summary,
        "task_id": task_id,
        "changed_files": [],
        "checks_run": [],
        "commit_sha": None,
        "notes": [],
    }


def _reviewer_error(task_id: str, summary: str) -> dict:
    return {
        "role": "reviewer",
        "verdict": "ERROR",
        "summary": summary,
        "task_id": task_id,
        "blocking_issues": [],
        "non_blocking_issues": [],
    }


def normalize_result(role: str, task_id: str, log_dir: Path) -> dict:
    summary = summarize_log(log_dir)
    parsed = extract_json_object(summary["last_message"])

    if role == "executor":
        if isinstance(parsed, dict) and parsed.get("role") == "executor":
            result = {
                "role": "executor",
                "status": parsed.get("status", "infra_error"),
                "summary": parsed.get("summary", ""),
                "task_id": parsed.get("task_id", task_id),
                "changed_files": parsed.get("changed_files", []),
                "checks_run": parsed.get("checks_run", []),
                "commit_sha": parsed.get("commit_sha"),
                "notes": parsed.get("notes", []),
            }
            if result["status"] not in {"ok", "failed", "infra_error"}:
                return _executor_error(task_id, "invalid executor status in result payload")
            return result

        if summary["sandbox_block"]:
            return _executor_error(task_id, "sandbox blocked worker action")
        if summary["status"] in {"stopped", "incomplete", "error"}:
            return _executor_error(task_id, "executor worker did not produce a valid structured result")
        return _executor_error(task_id, "missing or malformed executor JSON result")

    if role == "reviewer":
        if isinstance(parsed, dict) and parsed.get("role") == "reviewer":
            result = {
                "role": "reviewer",
                "verdict": parsed.get("verdict", "ERROR"),
                "summary": parsed.get("summary", ""),
                "task_id": parsed.get("task_id", task_id),
                "blocking_issues": parsed.get("blocking_issues", []),
                "non_blocking_issues": parsed.get("non_blocking_issues", []),
            }
            if result["verdict"] not in {"APPROVE", "REQUEST_CHANGES", "ERROR"}:
                return _reviewer_error(task_id, "invalid reviewer verdict in result payload")
            return result

        if summary["sandbox_block"]:
            return _reviewer_error(task_id, "sandbox blocked reviewer action")
        if summary["status"] in {"stopped", "incomplete", "error"}:
            return _reviewer_error(task_id, "reviewer worker did not produce a valid structured result")
        return _reviewer_error(task_id, "missing or malformed reviewer JSON result")

    raise ValueError(f"unsupported role: {role}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Codex worker logs into result.json")
    parser.add_argument("--role", required=True, choices=["executor", "reviewer"])
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--result-path", required=True)
    args = parser.parse_args()

    result = normalize_result(args.role, args.task_id, Path(args.log_dir).resolve())
    result_path = Path(args.result_path).resolve()
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
