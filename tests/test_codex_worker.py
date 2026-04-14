"""src/codex_worker.py normalization tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import codex_worker  # noqa: E402


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_extract_json_object_supports_fenced_json():
    text = """Here is the result:

```json
{"role":"reviewer","verdict":"APPROVE","summary":"ok","task_id":"T-1","blocking_issues":[],"non_blocking_issues":[]}
```
"""
    parsed = codex_worker.extract_json_object(text)
    assert parsed is not None
    assert parsed["verdict"] == "APPROVE"


def test_normalize_executor_ok_from_last_message_json(tmp_path):
    log_dir = tmp_path / "logs"
    _write(log_dir / "meta.json", json.dumps({"exit_code": 0, "duration_sec": 10.2}))
    _write(log_dir / "events.jsonl", "")
    _write(
        log_dir / "last-message.txt",
        json.dumps(
            {
                "role": "executor",
                "status": "ok",
                "summary": "done",
                "task_id": "T-001",
                "changed_files": ["src/a.ts"],
                "checks_run": ["npm run lint"],
                "commit_sha": None,
                "notes": [],
            }
        ),
    )

    result = codex_worker.normalize_result("executor", "T-001", log_dir)

    assert result["role"] == "executor"
    assert result["status"] == "ok"
    assert result["task_id"] == "T-001"
    assert result["changed_files"] == ["src/a.ts"]


def test_normalize_reviewer_request_changes_from_last_message_json(tmp_path):
    log_dir = tmp_path / "logs"
    _write(log_dir / "meta.json", json.dumps({"exit_code": 0, "duration_sec": 6.1}))
    _write(log_dir / "events.jsonl", "")
    _write(
        log_dir / "last-message.txt",
        json.dumps(
            {
                "role": "reviewer",
                "verdict": "REQUEST_CHANGES",
                "summary": "1 blocking issue",
                "task_id": "T-002",
                "blocking_issues": [{"file": "src/a.ts", "reason": "spec mismatch"}],
                "non_blocking_issues": [],
            }
        ),
    )

    result = codex_worker.normalize_result("reviewer", "T-002", log_dir)

    assert result["role"] == "reviewer"
    assert result["verdict"] == "REQUEST_CHANGES"
    assert result["blocking_issues"][0]["file"] == "src/a.ts"


def test_normalize_executor_sandbox_block_maps_to_infra_error(tmp_path):
    log_dir = tmp_path / "logs"
    _write(log_dir / "meta.json", json.dumps({"exit_code": 0, "duration_sec": 8.0}))
    _write(log_dir / "events.jsonl", "")
    _write(log_dir / "last-message.txt", "Sandbox blocked the write. EXPECTED_BLOCK")

    result = codex_worker.normalize_result("executor", "T-003", log_dir)

    assert result["role"] == "executor"
    assert result["status"] == "infra_error"
    assert "sandbox" in result["summary"]


def test_normalize_reviewer_stopped_meta_maps_to_error(tmp_path):
    log_dir = tmp_path / "logs"
    _write(log_dir / "meta.json", json.dumps({"status": "stopped", "partial": True}))
    _write(log_dir / "events.jsonl", "")
    _write(log_dir / "last-message.txt", "")

    result = codex_worker.normalize_result("reviewer", "T-004", log_dir)

    assert result["role"] == "reviewer"
    assert result["verdict"] == "ERROR"


def test_summarize_log_extracts_thread_id_and_usage(tmp_path):
    log_dir = tmp_path / "logs"
    _write(log_dir / "meta.json", json.dumps({"exit_code": 0, "duration_sec": 4.0}))
    _write(
        log_dir / "events.jsonl",
        "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "th-1"}),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}),
            ]
        ),
    )
    _write(log_dir / "last-message.txt", "{}")

    summary = codex_worker.summarize_log(log_dir)

    assert summary["thread_id"] == "th-1"
    assert summary["usage"] == {"input_tokens": 10, "output_tokens": 5}
