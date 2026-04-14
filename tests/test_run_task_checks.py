"""plugin/skills/ax-implement/scripts/run_task_checks.sh tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugin" / "skills" / "ax-implement" / "scripts" / "run_task_checks.sh"


def _write_package_json(path: Path, scripts: dict[str, str]) -> None:
    path.write_text(
        json.dumps({"name": "task-checks-fixture", "private": True, "scripts": scripts}),
        encoding="utf-8",
    )


def test_run_task_checks_pass_and_skip(tmp_path):
    _write_package_json(
        tmp_path / "package.json",
        {
            "lint": "node -e \"process.exit(0)\"",
            "typecheck": "node -e \"process.exit(0)\"",
        },
    )
    output_path = tmp_path / "checks.json"

    proc = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--step",
            "lint",
            "--step",
            "typecheck",
            "--step",
            "test",
            "--output",
            str(output_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "pass"
    assert payload["failed_step"] == ""
    assert payload["results"] == [
        {"step": "lint", "result": "pass"},
        {"step": "typecheck", "result": "pass"},
        {"step": "test", "result": "skip"},
    ]
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_run_task_checks_stops_at_first_failure(tmp_path):
    _write_package_json(
        tmp_path / "package.json",
        {
            "lint": "node -e \"process.exit(0)\"",
            "typecheck": "node -e \"process.exit(1)\"",
            "build": "node -e \"process.exit(0)\"",
        },
    )

    proc = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--step",
            "lint",
            "--step",
            "typecheck",
            "--step",
            "build",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["status"] == "fail"
    assert payload["failed_step"] == "typecheck"
    assert payload["results"] == [
        {"step": "lint", "result": "pass"},
        {"step": "typecheck", "result": "fail"},
    ]
