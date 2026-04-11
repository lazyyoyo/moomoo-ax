#!/usr/bin/env python3
"""
ax_feedback.py — /ax-feedback CLI

오너가 자유 서술 피드백을 feedback_backlog 에 남기는 명시적 채널.
team-ax 사용 중 아무 때나 호출 가능. 북극성 지표의 정성 채널.

사용:
    ax_feedback.py "design 단계에서 폰트 선택이 튐"
    ax_feedback.py --priority high "빌드 깨지는 스펙 빠짐"
    ax_feedback.py --stage ax-implement "타입 오류 반복 생성"
    ax_feedback.py --project haru "뭔가 이상함"
    echo "파이프 입력" | ax_feedback.py --priority low

기본값:
- project: 현재 git repo 의 최상위 디렉토리 이름 (없으면 None)
- stage: 없음 (stage 와 무관한 일반 피드백)
- priority: medium
- user_name: MOOMOO_AX_USER 환경변수 → git user.name 매핑 → 'yoyo' 폴백

환경:
- __file__ 기반으로 moomoo-ax 루트 자동 해석 → src/db.py .env 로딩 재사용
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

MOOMOO_AX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MOOMOO_AX_ROOT / "src"))


def _git(*args, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        return ""


# 환경 / 유저 / 프로젝트 컨텍스트 자동 추출
# ────────────────────────────────────────────────────────

GIT_USER_TO_AX_USER = {
    "lazyyoyo": "yoyo",
    "yoyo": "yoyo",
    # 추후 jojo 추가 예정
}


def infer_user() -> str:
    """MOOMOO_AX_USER > git user.name 매핑 > 'yoyo' 폴백."""
    env_user = os.environ.get("MOOMOO_AX_USER")
    if env_user:
        return env_user
    git_user = _git("config", "user.name")
    if git_user:
        return GIT_USER_TO_AX_USER.get(git_user, git_user)
    return "yoyo"


def infer_project() -> str | None:
    """현재 cwd 의 git toplevel 디렉토리 이름. 저장소 밖이면 None."""
    top = _git("rev-parse", "--show-toplevel")
    if not top:
        return None
    return Path(top).name


# ────────────────────────────────────────────────────────


def read_content(arg_content: str | None) -> str:
    """arg 로 들어온 내용 우선, 없으면 stdin. 빈 문자열이면 오류."""
    if arg_content and arg_content.strip():
        return arg_content.strip()
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return data
    return ""


def main():
    parser = argparse.ArgumentParser(
        prog="ax-feedback",
        description="team-ax 자유 서술 피드백을 feedback_backlog 에 기록",
    )
    parser.add_argument(
        "content",
        nargs="?",
        help="피드백 본문 (생략 시 stdin 에서 읽음)",
    )
    parser.add_argument(
        "--priority", "-p",
        choices=["high", "medium", "low"],
        default="medium",
        help="우선순위 (기본: medium)",
    )
    parser.add_argument(
        "--stage", "-s",
        help="관련 stage (예: ax-implement). 생략 가능.",
    )
    parser.add_argument(
        "--project",
        help="관련 프로젝트 이름. 기본은 현재 git repo 이름.",
    )
    parser.add_argument(
        "--user", "-u",
        help="user_name. 기본은 MOOMOO_AX_USER / git user.name 매핑.",
    )

    args = parser.parse_args()

    content = read_content(args.content)
    if not content:
        print("ERROR: 피드백 본문이 비었음. arg 로 넘기거나 stdin 으로 파이프.",
              file=sys.stderr)
        sys.exit(1)

    user_name = args.user or infer_user()
    project = args.project if args.project is not None else infer_project()
    stage = args.stage

    # db 로더 import (늦게 해서 .env 로딩이 MOOMOO_AX_ROOT 기반으로 되도록)
    from db import log_feedback

    ok, row_id = log_feedback(
        user_name=user_name,
        content=content,
        priority=args.priority,
        project=project,
        stage=stage,
    )

    if not ok:
        print("FAILED: feedback_backlog insert 실패", file=sys.stderr)
        sys.exit(2)

    # 확인 메시지
    preview = content if len(content) <= 60 else content[:57] + "..."
    print(f"✓ feedback 기록됨")
    print(f"  id       : {row_id}")
    print(f"  user     : {user_name}")
    print(f"  priority : {args.priority}")
    if project:
        print(f"  project  : {project}")
    if stage:
        print(f"  stage    : {stage}")
    print(f"  content  : {preview}")


if __name__ == "__main__":
    main()
