#!/usr/bin/env python3
"""product loop 실행 드라이버.

`src/loop.py` (levelup harness) 를 경유하지 않음. 단발 `claude -p` 호출을
fixture 의 worktree 에서 수행하고 stdout 을 `.harness/runs/<run_id>.ndjson`
으로 저장한다. 판정은 수동 (v0.3).

Usage:
    scripts/ax_product_run.py --fixture <path> [--plugin-dir <path>]
                              [--prompt <text>] [--timeout <sec>]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import claude  # noqa: E402


DEFAULT_PROMPT = "/team-ax:ax-implement"
DEFAULT_PLUGIN_DIR = REPO_ROOT / "plugin"

BASE_ALLOWED_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Grep",
    "Glob",
    "Task",
    "TodoWrite",
    "Bash(git:*)",
    "Bash(npm:*)",
    "Bash(bun:*)",
    "Bash(npx:*)",
    "Bash(jq:*)",
    "Bash(which:*)",
    "Bash(pgrep:*)",
    "Bash(curl:*)",
    "Bash(gitleaks:*)",
]


def build_allowed_tools(plugin_dir: Path) -> list[str]:
    """plugin_dir 기반 scripts 절대경로 패턴을 BASE 에 합쳐 반환.

    permission rule 은 env 변수 치환을 하지 않으므로 `${CLAUDE_SKILL_DIR}` 같은
    심볼릭 경로 대신 해석된 절대경로 패턴을 사용한다.
    """
    scripts_dir = plugin_dir / "skills" / "ax-implement" / "scripts"
    abs_pattern = str(scripts_dir) + "/*"
    return [
        *BASE_ALLOWED_TOOLS,
        f"Bash(bash {abs_pattern})",
        f"Bash({abs_pattern})",  # shebang 직접 실행 대비
        f"Bash(python {abs_pattern})",
        f"Bash(python3 {abs_pattern})",
    ]


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check,
                          capture_output=True, text=True)


def _verify_cleanup(fixture_root: Path, run_dir: Path) -> list[str]:
    """run 디렉토리 제거 후 fixture 원본이 깨끗한지 확인. 문제 목록 반환."""
    issues: list[str] = []

    # 1) run 디렉토리가 실제로 제거됐어야 함
    if run_dir.exists():
        issues.append(f"run dir still exists: {run_dir}")

    # 2) fixture 템플릿 원본 파일이 변경되지 않았어야 함 (stat mtime 은 run 전후 비교가 맞지만
    #    간접적으로 fixture 가 git repo 가 아닌 평범한 디렉토리인지 확인)
    if (fixture_root / ".git").exists():
        issues.append(f"fixture template should not be a git repo but .git exists at {fixture_root}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, help="fixture repo path (readonly template)")
    parser.add_argument("--plugin-dir", default=str(DEFAULT_PLUGIN_DIR))
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--timeout", type=int, default=1800,
                        help="subprocess timeout seconds (default 1800 = 30min)")
    parser.add_argument("--log-dir", default=str(REPO_ROOT / ".harness" / "runs"))
    parser.add_argument("--keep", action="store_true",
                        help="run_dir 를 제거하지 않고 보존 (디버깅용)")
    args = parser.parse_args()

    fixture_root = Path(args.fixture).resolve()
    plugin_dir = Path(args.plugin_dir).resolve()
    log_dir = Path(args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    if not fixture_root.exists():
        print(f"[ERROR] fixture not found: {fixture_root}", file=sys.stderr)
        return 2
    if (fixture_root / ".git").exists():
        print(f"[ERROR] fixture should be a plain directory (no .git): {fixture_root}",
              file=sys.stderr)
        return 2
    if not plugin_dir.exists():
        print(f"[ERROR] plugin-dir not found: {plugin_dir}", file=sys.stderr)
        return 2

    run_id = uuid.uuid4().hex[:12]
    run_dir = Path(tempfile.gettempdir()) / f"ax-run-{run_id}"
    ndjson_path = log_dir / f"{run_id}.ndjson"

    print(f"[ax_product_run] run_id={run_id}")
    print(f"[ax_product_run] fixture={fixture_root}")
    print(f"[ax_product_run] plugin_dir={plugin_dir}")
    print(f"[ax_product_run] run_dir={run_dir}")
    print(f"[ax_product_run] log={ndjson_path}")

    # 1) fixture 복사 + 격리 git init
    shutil.copytree(fixture_root, run_dir)
    _run(["git", "init", "-q"], cwd=run_dir)
    _run(["git", "-c", "user.email=ax-run@moomoo-ax",
          "-c", "user.name=ax-run",
          "add", "-A"], cwd=run_dir)
    _run(["git", "-c", "user.email=ax-run@moomoo-ax",
          "-c", "user.name=ax-run",
          "commit", "-q", "-m", "seed"], cwd=run_dir)

    exit_code = 0
    try:
        # 2) claude call
        result = claude.call(
            prompt=args.prompt,
            output_format="stream-json",
            timeout=args.timeout,
            allowed_tools=build_allowed_tools(plugin_dir),
            permission_mode="acceptEdits",
            plugin_dir=plugin_dir,
            setting_sources="project,local",
            include_hook_events=True,
            cwd=run_dir,
            stdout_path=ndjson_path,
        )

        print(f"[ax_product_run] success={result['success']} "
              f"cost=${result.get('cost_usd', 0):.4f} "
              f"turns={result.get('num_turns', 0)} "
              f"duration={result.get('duration_sec', 0)}s")
        if not result["success"]:
            print(f"[ax_product_run] error={result.get('error')}", file=sys.stderr)
            exit_code = 1
    finally:
        # 3) cleanup — fixture 원본은 건드리지 않음. run_dir 만 제거
        if run_dir.exists() and not args.keep:
            shutil.rmtree(run_dir, ignore_errors=True)

        issues = _verify_cleanup(fixture_root, run_dir if not args.keep else Path("/nonexistent"))
        if issues:
            print("[ax_product_run] WARN cleanup issues:", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)

    print(f"[ax_product_run] log saved: {ndjson_path}")
    if args.keep:
        print(f"[ax_product_run] --keep: run_dir preserved at {run_dir}")
    print("[ax_product_run] ---- next: manual check ----")
    print(f"  run_dir ({'preserved' if args.keep else 'removed'}): {run_dir}")
    print(f"  ndjson:                           {ndjson_path}")
    print("  inspect:")
    print(f"    grep -E '\"type\":\"assistant\"' {ndjson_path} | jq .")
    print(f"    grep 'subagent_type' {ndjson_path} | jq .")
    print("  verify:")
    print("    - plan.md 의 - [ ] 가 모두 - [x] 로 전환됐는가?")
    print("    - subagent_type 이 team-ax:executor / design-engineer / reviewer 인가?")
    print("    - run_review_checks.sh 호출이 있고 exit 0 인가?")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
