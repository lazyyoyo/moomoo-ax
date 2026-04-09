#!/usr/bin/env python3
"""
ax-loop 오케스트레이터 (MVP v0.1)

Phase 2(Build) 루프만 지원: 워커 → 정적 게이트 → keep/discard → 반복
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
CONSECUTIVE_FAIL_LIMIT = 3
SCRIPTS_DIR = Path(__file__).resolve().parent
GATE_STATIC = SCRIPTS_DIR / "gate_static.sh"
WORKER = SCRIPTS_DIR / "worker.py"


# ── 디렉토리 헬퍼 ────────────────────────────────────

def harness_dir(project: Path) -> Path:
    d = project / ".harness"
    d.mkdir(parents=True, exist_ok=True)
    return d


def checkpoints_dir(project: Path) -> Path:
    d = harness_dir(project) / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def history_dir(project: Path) -> Path:
    d = checkpoints_dir(project) / "history"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir(project: Path) -> Path:
    d = harness_dir(project) / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── 체크포인트 ────────────────────────────────────────

def load_checkpoint(project: Path, name: str) -> dict | None:
    path = checkpoints_dir(project) / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_checkpoint(project: Path, name: str, data: dict):
    path = checkpoints_dir(project) / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def save_log(project: Path, iteration: int, data: dict):
    path = logs_dir(project) / f"iteration_{iteration:03d}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    # history 복사
    hist = history_dir(project) / f"build_{iteration:03d}.json"
    hist.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── CPS/PRD 탐색 ─────────────────────────────────────

def find_cps_or_prd(project: Path) -> str | None:
    """CPS 또는 PRD 파일 탐색. 내용 반환."""
    candidates = [
        project / ".harness" / "checkpoints" / "define_latest.json",
        project / ".harness" / "checkpoints" / "plan_latest.json",
    ]
    # docs/specs/ 안의 md 파일도 탐색
    specs_dir = project / "docs" / "specs"
    if specs_dir.is_dir():
        candidates.extend(sorted(specs_dir.glob("*.md")))

    # BACKLOG.md, README.md 도 후보
    for name in ["CPS.md", "PRD.md", "BACKLOG.md"]:
        candidates.append(project / name)

    for path in candidates:
        if path.exists() and path.stat().st_size > 0:
            return path.read_text()[:5000]

    return None


# ── git 유틸 ──────────────────────────────────────────

def git_ref(project: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=project, capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def git_commit(project: Path, message: str) -> str:
    """변경사항 커밋. 커밋 해시 반환."""
    subprocess.run(["git", "add", "-A"], cwd=project, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project, capture_output=True,
    )
    return git_ref(project)


def git_discard(project: Path):
    """워커 변경사항 전부 되돌리기."""
    subprocess.run(["git", "checkout", "--", "."], cwd=project, capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=project, capture_output=True)


# ── 워커 호출 ────────────────────────────────────────

def call_worker(
    project: Path,
    cps_content: str,
    prev_errors: list | None = None,
) -> dict:
    """worker.py 호출 → 결과 dict 반환."""
    cmd = [
        sys.executable, str(WORKER),
        "--project", str(project),
        "--cps", cps_content,
    ]
    if prev_errors:
        cmd.extend(["--prev-errors", json.dumps(prev_errors, ensure_ascii=False)])

    start = time.monotonic()
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=project, timeout=360,
    )
    duration = time.monotonic() - start

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip() or "워커 실행 실패",
            "duration_sec": round(duration, 1),
            "tokens": {"input": 0, "output": 0},
        }

    try:
        data = json.loads(result.stdout)
        data["duration_sec"] = round(duration, 1)
        return data
    except json.JSONDecodeError:
        return {
            "success": True,
            "raw": result.stdout.strip()[:500],
            "duration_sec": round(duration, 1),
            "tokens": {"input": 0, "output": 0},
        }


# ── 게이트 호출 ──────────────────────────────────────

def call_gate_static(project: Path) -> dict:
    """gate_static.sh 호출 → {passed, errors, duration_ms}."""
    result_file = harness_dir(project) / "gate_result.json"

    start = time.monotonic()
    result = subprocess.run(
        ["bash", str(GATE_STATIC), str(project), str(result_file)],
        cwd=project, capture_output=True, text=True,
    )
    duration_ms = int((time.monotonic() - start) * 1000)

    # 결과 파일 파싱
    if result_file.exists():
        try:
            gate_data = json.loads(result_file.read_text())
            gate_data["duration_ms"] = duration_ms
            return gate_data
        except json.JSONDecodeError:
            pass

    # 결과 파일 없으면 stdout/stderr에서 에러 추출
    passed = result.returncode == 0
    errors = []
    if not passed:
        error_text = result.stdout.strip() or result.stderr.strip()
        if error_text:
            errors = [error_text[:2000]]

    return {
        "passed": passed,
        "errors": errors,
        "duration_ms": duration_ms,
    }


# ── 메인 루프 (run) ─────────────────────────────────

def cmd_run(args):
    project = Path(args.project).resolve()
    max_iter = args.max_iter or MAX_ITERATIONS

    if not project.is_dir():
        print(f"[ax] 에러: 프로젝트 경로가 존재하지 않음: {project}")
        sys.exit(1)

    # CPS/PRD 확인
    cps_content = find_cps_or_prd(project)
    if not cps_content:
        print(f"[ax] 에러: CPS/PRD 파일을 찾을 수 없음")
        print(f"  확인 경로: .harness/checkpoints/, docs/specs/, CPS.md, PRD.md")
        sys.exit(1)

    print(f"[ax] 프로젝트: {project}")
    print(f"[ax] 최대 반복: {max_iter}")
    print(f"[ax] 게이트: ① 정적")
    print()

    prev_errors = []
    consecutive_fails = 0
    keep_count = 0
    discard_count = 0

    for i in range(1, max_iter + 1):
        print(f"── iteration {i}/{max_iter} ──────────────────────")

        # 1) 워커 호출
        print("[워커] Claude 호출 중...")
        worker_result = call_worker(
            project, cps_content,
            prev_errors if prev_errors else None,
        )

        if not worker_result.get("success", False):
            print(f"[워커] 실패: {worker_result.get('error', '알 수 없음')}")
            consecutive_fails += 1
            discard_count += 1

            log_entry = _build_log(
                i, "discard", worker_result,
                {"passed": False, "errors": [worker_result.get("error", "")]},
            )
            save_log(project, i, log_entry)

            if consecutive_fails >= CONSECUTIVE_FAIL_LIMIT:
                print(f"\n[ax] 연속 {CONSECUTIVE_FAIL_LIMIT}회 실패 — 오너 에스컬레이션 필요")
                break

            prev_errors = [worker_result.get("error", "워커 실행 실패")]
            continue

        # 2) 정적 게이트
        print("[게이트] 정적 검사 중...")
        gate = call_gate_static(project)

        now = datetime.now(timezone.utc).isoformat()

        if gate["passed"]:
            # ── keep ──
            ref = git_commit(project, f"ax-loop: iteration {i} keep")
            log_entry = _build_log(i, "keep", worker_result, gate)
            save_log(project, i, log_entry)

            best_data = {
                "stage": "build",
                "timestamp": now,
                "git_ref": ref,
                "iteration": i,
                "gate_results": {"static": True},
                "tokens_used": worker_result.get("tokens", {}),
            }
            save_checkpoint(project, "build_best", best_data)

            keep_count += 1
            consecutive_fails = 0
            prev_errors = []

            print(f"[판정] keep (git: {ref})")
            print(f"[ax] 정적 게이트 통과 — 루프 종료")
            print()
            _print_status(project)
            return
        else:
            # ── discard ──
            git_discard(project)

            error_summary = _summarize_errors(gate["errors"])
            log_entry = _build_log(i, "discard", worker_result, gate)
            log_entry["error_summary"] = error_summary
            save_log(project, i, log_entry)

            discard_count += 1
            consecutive_fails += 1

            print(f"[판정] discard — 정적 게이트 실패")
            if error_summary:
                lines = error_summary.split("\n")[:8]
                for line in lines:
                    print(f"  {line}")

            if consecutive_fails >= CONSECUTIVE_FAIL_LIMIT:
                print(f"\n[ax] 연속 {CONSECUTIVE_FAIL_LIMIT}회 실패 — 오너 에스컬레이션 필요")
                break

            prev_errors = gate["errors"]
            print(f"[ax] 에러 피드백 → 다음 반복")
            print()

    # 예산 초과
    print()
    print(f"[ax] {max_iter}회 반복 완료 — keep: {keep_count}, discard: {discard_count}")
    _print_status(project)


def _build_log(
    iteration: int,
    verdict: str,
    worker_result: dict,
    gate_result: dict,
) -> dict:
    return {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker": "claude",
        "model": "claude-sonnet-4-20250514",
        "stage": "build",
        "verdict": verdict,
        "gate_results": {
            "static": {
                "passed": gate_result.get("passed", False),
                "errors": gate_result.get("errors", []),
                "duration_ms": gate_result.get("duration_ms", 0),
            },
        },
        "tokens": worker_result.get("tokens", {"input": 0, "output": 0}),
        "duration_sec": worker_result.get("duration_sec", 0),
        "error_summary": None,
    }


def _summarize_errors(errors: list) -> str:
    if not errors:
        return ""
    return "\n".join(str(e)[:500] for e in errors[:5])


# ── status ───────────────────────────────────────────

def cmd_status(args):
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[ax] 에러: 프로젝트 경로가 존재하지 않음: {project}")
        sys.exit(1)
    _print_status(project)


def _print_status(project: Path):
    print(f"=== moomoo-ax status ===")
    print(f"Project: {project.name}")

    # Build best
    best = load_checkpoint(project, "build_best")
    if best:
        print(f"Phase 2 (Build):")
        print(f"  Best: build_{best.get('iteration', '?'):03d} (commit {best.get('git_ref', '-')})")
        print(f"  Last gate: static {'✓' if best.get('gate_results', {}).get('static') else '✗'}")
        tokens = best.get("tokens_used", {})
        total = sum(v for v in tokens.values() if isinstance(v, (int, float)))
        if total:
            print(f"  Tokens used: {total:,}")
    else:
        print(f"Phase 2 (Build): 아직 keep 없음")

    # 로그 집계
    log_path = logs_dir(project)
    log_files = sorted(log_path.glob("iteration_*.json"))
    if log_files:
        keep_count = 0
        discard_count = 0
        total_tokens = 0
        for lf in log_files:
            try:
                entry = json.loads(lf.read_text())
                if entry.get("verdict") == "keep":
                    keep_count += 1
                else:
                    discard_count += 1
                tokens = entry.get("tokens", {})
                total_tokens += sum(v for v in tokens.values() if isinstance(v, (int, float)))
            except (json.JSONDecodeError, TypeError):
                pass

        print(f"  Iterations: {len(log_files)} ({keep_count} keep / {discard_count} discard)")
        if total_tokens:
            print(f"  Tokens total: claude {total_tokens:,}")

        # 최근 5개
        print(f"  Recent:")
        for lf in log_files[-5:]:
            try:
                entry = json.loads(lf.read_text())
                verdict = entry.get("verdict", "?")
                icon = "✓" if verdict == "keep" else "✗"
                dur = entry.get("duration_sec", 0)
                print(f"    #{entry['iteration']:03d} {icon} {verdict} ({dur}s)")
            except (json.JSONDecodeError, KeyError):
                pass
    else:
        print(f"  Iterations: 0")

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
    p_run.add_argument("--project", "-p", required=True, help="대상 프로젝트 경로")
    p_run.add_argument("--max-iter", "-n", type=int, help=f"최대 반복 (기본: {MAX_ITERATIONS})")
    p_run.set_defaults(func=cmd_run)

    # status
    p_status = sub.add_parser("status", help="체크포인트 + 로그 현황")
    p_status.add_argument("--project", "-p", required=True, help="대상 프로젝트 경로")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
