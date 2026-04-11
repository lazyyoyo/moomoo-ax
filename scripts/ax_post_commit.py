#!/usr/bin/env python3
"""
ax_post_commit.py — post-commit hook 본체

대상 프로젝트에서 git commit 이 발생하면 이 스크립트가 호출된다.
.ax-generated.jsonl 매니페스트 와 이번 커밋의 변경 파일을 대조해서,
team-ax 가 생성한 파일 중 수정된 것이 있으면 diff 를 측정하고 interventions
row 를 Supabase 에 insert 한다.

설치:
    scripts/install_ax_diff_hook.sh <target_project_root>

수동 실행:
    MOOMOO_AX_DRY_RUN=1 python scripts/ax_post_commit.py <target_project_root>

환경:
- `__file__` 기준으로 moomoo-ax 루트 자동 해석 → src/db.py 의 .env 로딩 재사용
- cwd 는 대상 프로젝트 루트 (git hook 은 repo root 에서 실행됨)
- MOOMOO_AX_DRY_RUN=1 이면 Supabase insert 없이 stdout 에 payload 만 출력
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# moomoo-ax 루트 = 이 파일의 parent.parent
MOOMOO_AX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MOOMOO_AX_ROOT / "src"))
sys.path.insert(0, str(MOOMOO_AX_ROOT / "scripts"))

from ax_generated import lookup, read_artifact, reconcile, all_tracked_paths  # noqa: E402


def _git(*args, cwd: Path) -> str:
    """git 명령 실행, stdout 반환. 실패 시 빈 문자열."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except FileNotFoundError:
        return ""


def get_changed_files(project_root: Path) -> list[str]:
    """HEAD 커밋에서 변경된 파일 목록 (상대 경로)."""
    out = _git(
        "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD",
        cwd=project_root,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def get_head_sha(project_root: Path) -> str:
    return _git("rev-parse", "HEAD", cwd=project_root).strip()


def get_file_content_at_head(project_root: Path, rel_path: str) -> str:
    """HEAD 시점의 파일 내용 (읽기 실패 시 현재 디스크 내용으로 폴백)."""
    content = _git("show", f"HEAD:{rel_path}", cwd=project_root)
    if content:
        return content
    # git show 실패 (binary, 또는 신규 untracked) — 디스크에서 직접
    p = project_root / rel_path
    if p.exists():
        return p.read_text(errors="replace")
    return ""


def compute_diff_stats(baseline: str, current: str) -> dict:
    """
    단순 라인 기반 diff 통계. hunks 는 연속된 변경 그룹 수로 근사.

    Returns: {hunks_added, hunks_deleted, lines_added, lines_deleted}
    """
    import difflib

    baseline_lines = baseline.splitlines()
    current_lines = current.splitlines()

    matcher = difflib.SequenceMatcher(None, baseline_lines, current_lines)
    lines_added = 0
    lines_deleted = 0
    hunks_added = 0
    hunks_deleted = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        deleted_span = i2 - i1
        added_span = j2 - j1
        if tag == "delete":
            lines_deleted += deleted_span
            hunks_deleted += 1
        elif tag == "insert":
            lines_added += added_span
            hunks_added += 1
        elif tag == "replace":
            lines_deleted += deleted_span
            lines_added += added_span
            hunks_deleted += 1
            hunks_added += 1

    return {
        "hunks_added": hunks_added,
        "hunks_deleted": hunks_deleted,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
    }


def process_commit(project_root: Path, dry_run: bool = False) -> list[dict]:
    """
    커밋 처리의 본체. 변경 파일과 매니페스트 교집합을 대상으로 intervention 기록.

    Returns: 기록된 intervention payload 리스트 (dry-run 여부와 무관하게)
    """
    project_root = Path(project_root).resolve()
    tracked = all_tracked_paths(project_root)
    if not tracked:
        return []

    changed = get_changed_files(project_root)
    if not changed:
        return []

    touched = [p for p in changed if p in tracked]
    if not touched:
        return []

    head_sha = get_head_sha(project_root)
    project_name = project_root.name

    # DB 로거 (dry-run 이면 import 건너뜀)
    log_intervention = None
    if not dry_run:
        try:
            from db import log_intervention as _log
            log_intervention = _log
        except Exception as e:
            print(f"[ax-post-commit] db 로더 실패 — dry 모드로 진행: {e}",
                  file=sys.stderr)

    records = []
    for rel in touched:
        entry = lookup(project_root, rel)
        if not entry:
            continue

        baseline = read_artifact(project_root, rel)
        if baseline is None:
            # artifact 유실 — 매니페스트만 정리하고 건너뜀
            reconcile(project_root, rel)
            continue

        current = get_file_content_at_head(project_root, rel)
        stats = compute_diff_stats(baseline, current)

        payload = {
            "user_name": entry.get("user_name", "unknown"),
            "project": project_name,
            "stage": entry.get("stage", "unknown"),
            "original_path": rel,
            "final_commit": head_sha,
            **stats,
            "files_changed": 1,
        }
        records.append(payload)

        if log_intervention:
            log_intervention(**payload)
            print(f"[ax-post-commit] {rel} → intervention 기록 "
                  f"({stats['lines_added']}+ / {stats['lines_deleted']}-, "
                  f"hunks {stats['hunks_added']}/{stats['hunks_deleted']})",
                  file=sys.stderr)
        else:
            print(f"[ax-post-commit:dry] {json.dumps(payload, ensure_ascii=False)}",
                  file=sys.stderr)

        # 베이스라인 리셋
        reconcile(project_root, rel)

    return records


def main():
    # 인자로 대상 프로젝트 루트 받음. 없으면 cwd (git hook 기본).
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path.cwd().resolve()

    dry_run = os.environ.get("MOOMOO_AX_DRY_RUN") == "1"

    try:
        records = process_commit(project_root, dry_run=dry_run)
        if not records:
            # 추적 파일 없음 — 조용히 종료
            return 0
        return 0
    except Exception as e:
        # hook 실패는 커밋 자체를 깨면 안 됨 → 에러만 로그
        print(f"[ax-post-commit] ERROR: {e}", file=sys.stderr)
        return 0  # git hook 은 non-zero 여도 문제 없지만 안전하게 0 리턴


if __name__ == "__main__":
    sys.exit(main())
