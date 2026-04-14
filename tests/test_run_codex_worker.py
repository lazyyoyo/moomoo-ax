"""plugin/skills/ax-implement/scripts/run_codex_worker.sh tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "plugin" / "skills" / "ax-implement" / "scripts" / "run_codex_worker.sh"


def _write_fake_codex(bin_dir: Path) -> None:
    script = bin_dir / "codex"
    script.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--version" ]]; then
  echo "codex 0.0.test"
  exit 0
fi

if [[ "${1:-}" == "exec" ]]; then
  last_message=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o)
        last_message="$2"
        shift 2
        ;;
      *)
        shift
        ;;
    esac
  done

  cat >/dev/null

  cat >"$last_message" <<'EOF'
{"role":"executor","status":"ok","summary":"done","task_id":"T-001","changed_files":["src/app/(dashboard)/projects/page.tsx"],"checks_run":[],"commit_sha":null,"notes":[]}
EOF
  exit 0
fi

echo "unexpected codex args: $*" >&2
exit 2
""",
        encoding="utf-8",
    )
    os.chmod(script, 0o755)


def _run_wrapper(tmp_path: Path, extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_codex(bin_dir)

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    task_file = tmp_path / "task.md"
    task_file.write_text("executor task", encoding="utf-8")
    log_dir = tmp_path / "logs"

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    return subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--role",
            "executor",
            "--task-id",
            "T-001",
            "--task-summary",
            "dashboard latest run metadata",
            "--cd",
            str(work_dir),
            "--task-file",
            str(task_file),
            "--log-dir",
            str(log_dir),
            *extra_args,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_run_codex_worker_auto_routing_handles_empty_arrays(tmp_path):
    proc = _run_wrapper(tmp_path, [])

    assert proc.returncode == 0, proc.stderr
    result = json.loads((tmp_path / "logs" / "result.json").read_text(encoding="utf-8"))
    selection = json.loads((tmp_path / "logs" / "model-selection.json").read_text(encoding="utf-8"))

    assert result["status"] == "ok"
    assert selection["task_id"] == "T-001"


def test_run_codex_worker_explicit_override_handles_empty_arrays(tmp_path):
    proc = _run_wrapper(tmp_path, ["--model", "gpt-5.4"])

    assert proc.returncode == 0, proc.stderr
    result = json.loads((tmp_path / "logs" / "result.json").read_text(encoding="utf-8"))
    selection = json.loads((tmp_path / "logs" / "model-selection.json").read_text(encoding="utf-8"))

    assert result["status"] == "ok"
    assert selection["tier"] == "explicit"
    assert selection["model"] == "gpt-5.4"
