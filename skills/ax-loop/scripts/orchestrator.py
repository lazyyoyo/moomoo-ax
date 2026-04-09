#!/usr/bin/env python3
"""
ax-loop 오케스트레이터 (MVP v0.1)

Phase 2(Build) 루프만 지원: 워커 → 정적 게이트 → pass/crash → 반복
커맨드: run, status
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── 상수 ──────────────────────────────────────────────

MAX_ITERATIONS = 10
SCRIPTS_DIR = Path(__file__).resolve().parent
GATE_STATIC = SCRIPTS_DIR / "gate_static.sh"
WORKER = SCRIPTS_DIR / "worker.py"


def find_project_root() -> Path:
    """프로젝트 루트 탐색 — .harness/ 또는 package.json 기준."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".harness").is_dir() or (parent / "package.json").is_file():
            return parent
    return cwd


def harness_dir(project_root: Path) -> Path:
    d = project_root / ".harness"
    d.mkdir(parents=True, exist_ok=True)
    return d


def checkpoints_dir(project_root: Path) -> Path:
    d = harness_dir(project_root) / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir(project_root: Path) -> Path:
    d = harness_dir(project_root) / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def history_dir(project_root: Path) -> Path:
    d = checkpoints_dir(project_root) / "history"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── 체크포인트 ────────────────────────────────────────

def load_checkpoint(project_root: Path, name: str) -> dict | None:
    path = checkpoints_dir(project_root) / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_checkpoint(project_root: Path, name: str, data: dict):
    path = checkpoints_dir(project_root) / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def save_log(project_root: Path, iteration: int, data: dict):
    path = logs_dir(project_root) / f"iteration_{iteration:03d}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    # history에도 복사
    hist = history_dir(project_root) / f"build_{iteration:03d}.json"
    hist.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── git 유틸 ──────────────────────────────────────────

def git_ref(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=project_root, capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def git_stash_or_reset(project_root: Path):
    """crash 시 워커 변경사항 되돌리기."""
    subprocess.run(
        ["git", "checkout", "."],
        cwd=project_root, capture_output=True,
    )


# ── 워커 호출 ────────────────────────────────────────

def call_worker(
    project_root: Path,
    task: str,
    rework_prompt: str | None = None,
) -> dict:
    """worker.py 호출 → 결과 dict 반환."""
    cmd = [
        sys.executable, str(WORKER),
        "--project-root", str(project_root),
        "--task", task,
    ]
    if rework_prompt:
        cmd.extend(["--rework", rework_prompt])

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=project_root,
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip() or "워커 실행 실패",
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"success": True, "raw": result.stdout.strip()}


# ── 게이트 호출 ──────────────────────────────────────

def call_gate_static(project_root: Path) -> dict:
    """gate_static.sh 호출 → {pass, errors, duration_ms}."""
    start = time.monotonic()
    result = subprocess.run(
        ["bash", str(GATE_STATIC)],
        cwd=project_root, capture_output=True, text=True,
    )
    duration_ms = int((time.monotonic() - start) * 1000)

    passed = result.returncode == 0
    errors = ""
    if not passed:
        errors = result.stdout.strip() or result.stderr.strip()

    return {
        "pass": passed,
        "errors": errors,
        "duration_ms": duration_ms,
    }


# ── 메인 루프 (run) ─────────────────────────────────

def cmd_run(args):
    project_root = find_project_root()
    task = args.task or "CPS 기반 구현"
    max_iter = args.max_iterations or MAX_ITERATIONS

    print(f"[ax] 프로젝트: {project_root}")
    print(f"[ax] 태스크: {task}")
    print(f"[ax] 최대 반복: {max_iter}")
    print(f"[ax] 게이트: ① 정적")
    print()

    best = load_checkpoint(project_root, "build_best")
    rework_prompt = None
    consecutive_crashes = 0

    for i in range(1, max_iter + 1):
        print(f"── iteration {i}/{max_iter} ──────────────────────")

        # 1) 워커 호출
        print("[워커] Claude 호출 중...")
        worker_result = call_worker(project_root, task, rework_prompt)

        if not worker_result.get("success", True):
            print(f"[워커] 실패: {worker_result.get('error', '알 수 없음')}")
            consecutive_crashes += 1
            if consecutive_crashes >= 3:
                print("[ax] 연속 3회 crash — 오너 에스컬레이션 필요")
                break
            rework_prompt = f"워커 실행 실패: {worker_result.get('error', '')}"
            continue

        # 2) 정적 게이트
        print("[게이트] 정적 검사 중...")
        gate = call_gate_static(project_root)

        ref = git_ref(project_root)
        now = datetime.now(timezone.utc).isoformat()

        log_entry = {
            "iteration": i,
            "timestamp": now,
            "worker": "claude",
            "git_ref": ref,
            "gates": {
                "static": {
                    "pass": gate["pass"],
                    "duration_ms": gate["duration_ms"],
                },
            },
            "verdict": "",
            "rework_prompt": None,
        }

        if gate["pass"]:
            # ── keep ──
            log_entry["verdict"] = "keep"
            save_log(project_root, i, log_entry)

            best_data = {
                "stage": "build",
                "timestamp": now,
                "git_ref": ref,
                "iteration": i,
                "gate_results": {"static": True},
            }
            save_checkpoint(project_root, "build_best", best_data)

            print(f"[판정] keep ✓  (git: {ref})")
            print(f"[ax] 정적 게이트 통과 — 루프 종료")
            print()
            cmd_status_print(project_root)
            return
        else:
            # ── crash ──
            log_entry["verdict"] = "crash"
            rework_prompt = _build_rework_prompt(gate["errors"])
            log_entry["rework_prompt"] = rework_prompt
            save_log(project_root, i, log_entry)

            consecutive_crashes += 1
            print(f"[판정] crash ✗  — 정적 게이트 실패")
            if gate["errors"]:
                # 에러 앞 10줄만 출력
                lines = gate["errors"].split("\n")[:10]
                for line in lines:
                    print(f"  {line}")
                if len(gate["errors"].split("\n")) > 10:
                    print(f"  ... (총 {len(gate['errors'].split(chr(10)))}줄)")

            if consecutive_crashes >= 3:
                print()
                print("[ax] 연속 3회 crash — 오너 에스컬레이션 필요")
                break

            # 워커 변경사항은 유지 (다음 워커가 이어서 수정)
            print(f"[ax] 재작업 프롬프트 생성 → 다음 반복")
            print()

    # 예산 초과
    print()
    print(f"[ax] {max_iter}회 반복 완료 — best 결과 유지")
    cmd_status_print(project_root)


def _build_rework_prompt(errors: str) -> str:
    """게이트 에러에서 재작업 프롬프트 생성."""
    return (
        "이전 시도에서 정적 게이트(lint/typecheck/build) 실패. "
        "아래 에러를 수정해:\n\n"
        f"{errors[:3000]}"
    )


# ── status ───────────────────────────────────────────

def cmd_status(args):
    project_root = find_project_root()
    cmd_status_print(project_root)


def cmd_status_print(project_root: Path):
    print(f"[ax status] 프로젝트: {project_root}")
    print()

    # Phase 2 (Build)
    best = load_checkpoint(project_root, "build_best")
    if best:
        print(f"  Build best:")
        print(f"    git ref   : {best.get('git_ref', '-')}")
        print(f"    iteration : {best.get('iteration', '-')}")
        print(f"    timestamp : {best.get('timestamp', '-')}")
        print(f"    gates     : static={'✓' if best.get('gate_results', {}).get('static') else '✗'}")
    else:
        print("  Build best: 없음")

    # 로그 요약
    log_path = logs_dir(project_root)
    log_files = sorted(log_path.glob("iteration_*.json"))
    if log_files:
        print()
        print(f"  로그: {len(log_files)}개 iteration")
        # 최근 5개
        for lf in log_files[-5:]:
            entry = json.loads(lf.read_text())
            verdict = entry.get("verdict", "?")
            icon = "✓" if verdict == "keep" else "✗"
            print(f"    #{entry['iteration']:03d} {icon} {verdict}  (gate_static: {entry['gates']['static']['duration_ms']}ms)")
    else:
        print("  로그: 없음")

    print()


# ── CLI ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="ax",
        description="ax-loop 오케스트레이터 (MVP v0.1)",
    )
    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="Phase 2 빌드 루프 실행")
    p_run.add_argument("--task", "-t", help="태스크 설명")
    p_run.add_argument("--max-iterations", "-n", type=int, help=f"최대 반복 (기본: {MAX_ITERATIONS})")
    p_run.set_defaults(func=cmd_run)

    # status
    p_status = sub.add_parser("status", help="체크포인트 + 로그 현황")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
