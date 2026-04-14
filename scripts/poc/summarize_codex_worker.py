#!/usr/bin/env python3
"""Summarize one-shot Codex worker logs for PoC only.

Reads:
  - meta.json
  - events.jsonl
  - last-message.txt

Outputs a compact JSON summary to stdout.
This helper is intentionally decoupled from the main runtime.
"""

from __future__ import annotations

import argparse
import json
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


def extract_agent_messages(events: list[dict]) -> list[str]:
    messages: list[str] = []
    for evt in events:
        if evt.get("type") != "item.completed":
            continue
        item = evt.get("item") or {}
        if item.get("type") == "agent_message":
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                messages.append(text.strip())
    return messages


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


def summarize(log_dir: Path) -> dict:
    meta_path = log_dir / "meta.json"
    events_path = log_dir / "events.jsonl"
    last_message_path = log_dir / "last-message.txt"

    meta = load_meta(meta_path)
    events, invalid = parse_events(events_path)
    last_message = read_text(last_message_path) if last_message_path.exists() else ""
    event_types = Counter(evt.get("type", "<missing>") for evt in events)

    thread_id = None
    usage = None
    for evt in events:
        if evt.get("type") == "thread.started":
            thread_id = evt.get("thread_id")
        if evt.get("type") == "turn.completed":
            usage = evt.get("usage")

    agent_messages = extract_agent_messages(events)
    combined_text = "\n".join([*agent_messages, last_message]).lower()
    sandbox_block = "sandbox blocked" in combined_text

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
        "thread_id": thread_id,
        "codex_version": meta.get("codex_version"),
        "partial": bool(meta.get("partial", False)),
        "event_count": len(events),
        "invalid_event_lines": len(invalid),
        "event_types": dict(event_types),
        "sandbox_block": sandbox_block,
        "last_message": last_message,
        "usage": usage,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize PoC codex worker logs from a log directory",
    )
    parser.add_argument(
        "--log-dir",
        required=True,
        help="Directory containing meta.json, events.jsonl, last-message.txt",
    )
    args = parser.parse_args()

    log_dir = Path(args.log_dir).resolve()
    summary = summarize(log_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
