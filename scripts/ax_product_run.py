#!/usr/bin/env python3
"""product loop 실행 드라이버.

`src/loop.py` (levelup harness) 를 경유하지 않음. 단발 `claude -p` 호출을
fixture 의 worktree 에서 수행하고 stdout 을 `.harness/runs/<run_id>.ndjson`
으로 저장한다. 판정은 수동 (v0.3).

Usage:
    scripts/ax_product_run.py --fixture <path> [--plugin-dir <path>]
                              [--prompt <text>] [--project <name>] [--timeout <sec>]
    scripts/ax_product_run.py --target-subdir <path> [--repo-root <path>]
                              [--plugin-dir <path>] [--prompt <text>]
"""
from __future__ import annotations

import argparse
from collections import Counter
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
import db  # noqa: E402


DEFAULT_PROMPT = "/team-ax:ax-implement"
DEFAULT_PLUGIN_DIR = REPO_ROOT / "plugin"
SELF_EDIT_DENY_ROOTS = (
    "plugin",
    "src",
    "scripts",
    "tests",
    "labs",
    ".harness",
)

BASE_ALLOWED_TOOLS = [
    "Read",
    "Grep",
    "Glob",
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


def _to_absolute_permission_path(path: Path) -> str:
    """Claude absolute path rule 형식(`//abs/path`)으로 변환."""
    return f"//{path.resolve().as_posix().lstrip('/')}"


def build_allowed_tools(plugin_dir: Path, *, editable_root: Path | None = None) -> list[str]:
    """plugin_dir 기반 scripts 절대경로 패턴을 BASE 에 합쳐 반환.

    permission rule 은 env 변수 치환을 하지 않으므로 `${CLAUDE_SKILL_DIR}` 같은
    심볼릭 경로 대신 해석된 절대경로 패턴을 사용한다.
    """
    scripts_dir = plugin_dir / "skills" / "ax-implement" / "scripts"
    abs_pattern = str(scripts_dir) + "/*"
    edit_rules = ["Write", "Edit"]
    if editable_root is not None:
        editable_pattern = _to_absolute_permission_path(editable_root) + "/**"
        edit_rules = [
            f"Write({editable_pattern})",
            f"Edit({editable_pattern})",
        ]
    return [
        *BASE_ALLOWED_TOOLS,
        *edit_rules,
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


def _infer_stage(prompt: str) -> str | None:
    if prompt.startswith("/team-ax:"):
        return prompt.split(":", 1)[1]
    return None


def _infer_project(fixture_root: Path) -> str:
    return fixture_root.name


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def _resolve_target_subdir(repo_root: Path, raw_target_subdir: str) -> Path:
    raw_path = Path(raw_target_subdir)
    target_root = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()

    if not target_root.exists():
        raise ValueError(f"target-subdir not found: {raw_target_subdir}")
    if not target_root.is_dir():
        raise ValueError(f"target-subdir must be a directory: {raw_target_subdir}")
    if not _is_relative_to(target_root, repo_root):
        raise ValueError(f"target-subdir must stay inside repo-root: {raw_target_subdir}")
    if target_root == repo_root:
        raise ValueError("target-subdir must not be repo root")

    relative = target_root.relative_to(repo_root)
    for deny_root in SELF_EDIT_DENY_ROOTS:
        deny_path = repo_root / deny_root
        if target_root == deny_path or _is_relative_to(target_root, deny_path):
            raise ValueError(
                "target-subdir is reserved for harness/self-edit protection: "
                f"{relative.as_posix()}"
            )

    return target_root


def _build_target_subdir_prompt(prompt: str, *, target_subdir: Path) -> str:
    relative = target_subdir.as_posix()
    return (
        f"{prompt}\n\n"
        "[TARGET_SUBDIR]\n"
        f"{relative}\n"
        "[/TARGET_SUBDIR]\n\n"
        "Target-subdir mode is active.\n"
        f"- Current working directory is already `{relative}`.\n"
        f"- You may modify only files under `{relative}/**`.\n"
        "- Treat the current dirty working tree inside this subtree as baseline, not blocker.\n"
        "- Treat unrelated git changes outside this subtree as existing baseline, not blocker.\n"
        "- Keep `plan.md` and `.harness/` inside the current working directory.\n"
        "- Never edit parent harness paths such as `../plugin`, `../src`, `../scripts`, or `../labs`.\n"
    )


def _capture_outside_target_state(repo_root: Path, *, target_subdir: Path) -> dict[str, str]:
    """target-subdir 밖 git 상태 스냅샷. run 전후 동일해야 외부 오염이 없다고 본다."""
    relative = target_subdir.as_posix()
    exclude = f":(exclude){relative}"
    tracked = _run(
        ["git", "diff", "--no-ext-diff", "--binary", "--", ".", exclude],
        cwd=repo_root,
    ).stdout
    staged = _run(
        ["git", "diff", "--no-ext-diff", "--cached", "--binary", "--", ".", exclude],
        cwd=repo_root,
    ).stdout
    untracked = _run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", ".", exclude],
        cwd=repo_root,
    ).stdout
    return {
        "tracked": tracked,
        "staged": staged,
        "untracked": untracked,
    }


def _summarize_tool_calls(tool_events: list[dict]) -> dict:
    tool_counts: Counter[str] = Counter()
    subagent_counts: Counter[str] = Counter()

    for event in tool_events:
        tool_name = event.get("tool_name") or "unknown"
        tool_counts[tool_name] += 1

        if tool_name in {"Task", "Agent"}:
            tool_input = event.get("tool_input") or {}
            subagent_type = tool_input.get("subagent_type") or tool_input.get("agent_type")
            if subagent_type:
                subagent_counts[subagent_type] += 1

    return {
        "tool_counts": dict(tool_counts),
        "task_subagent_counts": dict(subagent_counts),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--fixture", help="fixture repo path (readonly template)")
    target_group.add_argument("--target-subdir",
                              help="repo-root 하위 dogfooding 대상 subdir")
    parser.add_argument("--repo-root", default=str(REPO_ROOT),
                        help="--target-subdir 기준 repo root (기본: 현재 moomoo-ax root)")
    parser.add_argument("--plugin-dir", default=str(DEFAULT_PLUGIN_DIR))
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--project", default=None,
                        help="product_runs.project override (기본: fixture명 또는 repo-root명)")
    parser.add_argument("--timeout", type=int, default=1800,
                        help="subprocess timeout seconds (default 1800 = 30min)")
    parser.add_argument("--log-dir", default=str(REPO_ROOT / ".harness" / "runs"))
    parser.add_argument("--keep", action="store_true",
                        help="run_dir 를 제거하지 않고 보존 (디버깅용)")
    args = parser.parse_args()

    fixture_root = Path(args.fixture).resolve() if args.fixture else None
    repo_root = Path(args.repo_root).resolve()
    plugin_dir = Path(args.plugin_dir).resolve()
    log_dir = Path(args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    if not plugin_dir.exists():
        print(f"[ERROR] plugin-dir not found: {plugin_dir}", file=sys.stderr)
        return 2
    if args.target_subdir and not repo_root.exists():
        print(f"[ERROR] repo-root not found: {repo_root}", file=sys.stderr)
        return 2
    if fixture_root is not None:
        if not fixture_root.exists():
            print(f"[ERROR] fixture not found: {fixture_root}", file=sys.stderr)
            return 2
        if (fixture_root / ".git").exists():
            print(f"[ERROR] fixture should be a plain directory (no .git): {fixture_root}",
                  file=sys.stderr)
            return 2

    run_id = uuid.uuid4().hex[:12]
    product_run_id = str(uuid.uuid4())
    run_dir = Path(tempfile.gettempdir()) / f"ax-run-{run_id}"
    ndjson_path = log_dir / f"{run_id}.ndjson"
    stage = _infer_stage(args.prompt)
    target_root: Path | None = None
    fixture_mode = fixture_root is not None
    output_path: str | None = None
    guard_before: dict[str, str] | None = None

    if fixture_mode:
        prompt = args.prompt
        project = args.project or _infer_project(fixture_root)
        run_cwd = run_dir
        allowed_tools = build_allowed_tools(plugin_dir)
        fixture_id = fixture_root.name
    else:
        try:
            target_root = _resolve_target_subdir(repo_root, args.target_subdir)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 2
        relative_target = target_root.relative_to(repo_root)
        prompt = _build_target_subdir_prompt(args.prompt, target_subdir=relative_target)
        project = args.project or repo_root.name
        run_cwd = target_root
        allowed_tools = build_allowed_tools(plugin_dir, editable_root=target_root)
        output_path = relative_target.as_posix()
        fixture_id = None
        try:
            guard_before = _capture_outside_target_state(repo_root, target_subdir=relative_target)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] target-subdir guard snapshot 실패: {e}", file=sys.stderr)
            if e.stderr:
                print(e.stderr.strip(), file=sys.stderr)
            return 2

    print(f"[ax_product_run] run_id={run_id}")
    print(f"[ax_product_run] product_run_id={product_run_id}")
    if fixture_mode:
        print(f"[ax_product_run] fixture={fixture_root}")
    else:
        print(f"[ax_product_run] repo_root={repo_root}")
        print(f"[ax_product_run] target_subdir={output_path}")
    print(f"[ax_product_run] plugin_dir={plugin_dir}")
    print(f"[ax_product_run] run_dir={run_dir if fixture_mode else run_cwd}")
    print(f"[ax_product_run] log={ndjson_path}")

    exit_code = 0
    finish_logged = False
    run_started = db.start_product_run(
        product_run_id=product_run_id,
        user_name=os.environ.get("MOOMOO_AX_USER", "yoyo"),
        project=project,
        command=prompt,
        stage=stage,
        fixture_id=fixture_id,
        output_path=output_path,
    )
    if not run_started:
        print(
            "[ax_product_run] ERROR product_runs start insert 실패 — "
            "runtime 관찰 인프라가 없으므로 실행 중단",
            file=sys.stderr,
        )
        return 3

    result: dict | None = None
    try:
        if fixture_mode:
            # 1) fixture 복사 + 격리 git init
            shutil.copytree(fixture_root, run_dir)
            _run(["git", "init", "-q"], cwd=run_dir)
            _run(["git", "-c", "user.email=ax-run@moomoo-ax",
                  "-c", "user.name=ax-run",
                  "add", "-A"], cwd=run_dir)
            _run(["git", "-c", "user.email=ax-run@moomoo-ax",
                  "-c", "user.name=ax-run",
                  "commit", "-q", "-m", "seed"], cwd=run_dir)

        # 2) claude call
        result = claude.call(
            prompt=prompt,
            output_format="stream-json",
            timeout=args.timeout,
            allowed_tools=allowed_tools,
            permission_mode="acceptEdits",
            plugin_dir=plugin_dir,
            setting_sources="project,local",
            include_hook_events=True,
            cwd=run_cwd,
            stdout_path=ndjson_path,
        )

        print(f"[ax_product_run] success={result['success']} "
              f"cost=${result.get('cost_usd', 0):.4f} "
              f"turns={result.get('num_turns', 0)} "
              f"duration={result.get('duration_sec', 0)}s")
        if not result["success"]:
            print(f"[ax_product_run] error={result.get('error')}", file=sys.stderr)
            exit_code = 1
    except subprocess.CalledProcessError as e:
        exit_code = e.returncode or 1
        print(f"[ax_product_run] subprocess failed: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr)
    except Exception as e:
        exit_code = 1
        print(f"[ax_product_run] error={e}", file=sys.stderr)
    finally:
        if run_started:
            final_status = "done" if exit_code == 0 else "failed"
            finish_kwargs = {
                "product_run_id": product_run_id,
                "status": final_status,
                "stage": stage,
                "output_path": output_path,
            }
            if result:
                finish_kwargs["duration_sec"] = result.get("duration_sec")
                finish_kwargs["cost_usd"] = result.get("cost_usd")
                finish_kwargs["num_turns"] = result.get("num_turns")
                finish_kwargs["session_id"] = result.get("session_id")
                finish_kwargs["tool_call_stats"] = _summarize_tool_calls(
                    result.get("tool_events", [])
                )
            finish_logged = db.finish_product_run(**finish_kwargs)
            if not finish_logged:
                print(
                    "[ax_product_run] ERROR product_runs finish update 실패",
                    file=sys.stderr,
                )
                if exit_code == 0:
                    exit_code = 3

        if fixture_mode:
            # 3) cleanup — fixture 원본은 건드리지 않음. run_dir 만 제거
            if run_dir.exists() and not args.keep:
                shutil.rmtree(run_dir, ignore_errors=True)

            issues = _verify_cleanup(fixture_root, run_dir if not args.keep else Path("/nonexistent"))
            if issues:
                print("[ax_product_run] WARN cleanup issues:", file=sys.stderr)
                for issue in issues:
                    print(f"  - {issue}", file=sys.stderr)
        elif target_root is not None and guard_before is not None:
            guard_after = _capture_outside_target_state(
                repo_root,
                target_subdir=target_root.relative_to(repo_root),
            )
            if guard_before != guard_after:
                print(
                    "[ax_product_run] ERROR target-subdir 밖 변경 감지 — "
                    "dogfooding run 을 실패로 처리",
                    file=sys.stderr,
                )
                if exit_code == 0:
                    exit_code = 1

    print(f"[ax_product_run] log saved: {ndjson_path}")
    if args.keep:
        print(f"[ax_product_run] --keep: run_dir preserved at {run_dir}")
    print("[ax_product_run] ---- next: manual check ----")
    print(f"  run_dir ({'preserved' if args.keep else 'removed'}): {run_dir}")
    print(f"  ndjson:                           {ndjson_path}")
    print("  inspect:")
    print(f"    grep -E '\"type\":\"assistant\"' {ndjson_path} | jq .")
    if args.keep:
        print(f"    find {run_dir} -path '*/.harness/codex/*/logs/result.json' -print")
    else:
        print("    - worker result 로그 확인이 필요하면 --keep 로 재실행")
    print("  verify:")
    print("    - plan.md 의 - [ ] 가 모두 - [x] 로 전환됐는가?")
    print("    - executor/reviewer result.json 이 생성되고 verdict/status 가 일관적인가?")
    print("    - run_review_checks.sh 호출이 있고 exit 0 인가?")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
