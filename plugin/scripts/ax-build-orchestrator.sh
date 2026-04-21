#!/usr/bin/env bash
# ax-build 오케스트레이터: version branch + 워크트리 + tmux 세션 + 완료 수집 + 머지.
#
# 사용법: ax-build-orchestrator.sh <command> [args]
#   init <version>          — version branch 생성 + 폴더 승격
#   worktree <version> <작업명> <포트>  — 워크트리 생성 + tmux 세션 오픈
#   status                  — 전체 워크트리 .ax-status 확인
#   merge <version>         — merge-ready 워크트리를 version branch에 순차 머지
#
# 전제: build-plan.md가 승인된 상태. 메인 세션에서 호출.

set -euo pipefail

COMMAND="${1:?사용법: ax-build-orchestrator.sh <init|worktree|status|merge> [args]}"
WORKTREE_BASE=".claude/worktrees"

case "$COMMAND" in

  init)
    VERSION="${2:?사용법: ax-build-orchestrator.sh init <version> (예: v1.9.0)}"
    BRANCH_NAME="version/${VERSION}"

    # Phase A 산출물 커밋
    if [[ -d "versions/undefined" ]]; then
      git add versions/undefined/
      git commit -m "Phase A 완료 — ${VERSION} scope 확정" || echo "Phase A 산출물 이미 커밋됨"

      # 폴더 승격
      mv "versions/undefined" "versions/${VERSION}"
      git add "versions/"
      git commit -m "${VERSION} 폴더 승격"
    fi

    # version branch 생성
    if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
      echo "version branch 이미 존재: ${BRANCH_NAME}"
      git checkout "${BRANCH_NAME}"
    else
      git checkout -b "${BRANCH_NAME}"
      echo "version branch 생성: ${BRANCH_NAME}"
    fi

    echo "---"
    echo "version: ${VERSION}"
    echo "branch: ${BRANCH_NAME}"
    ;;

  worktree)
    VERSION="${2:?사용법: ax-build-orchestrator.sh worktree <version> <작업명> <포트>}"
    WORK_NAME="${3:?작업명 필요}"
    PORT="${4:?포트 번호 필요}"
    BRANCH_NAME="version/${VERSION}"
    WT_PATH="${WORKTREE_BASE}/${WORK_NAME}"
    WT_BRANCH="${BRANCH_NAME}-${WORK_NAME}"

    if [[ -d "$WT_PATH" ]]; then
      echo "워크트리 이미 존재: ${WT_PATH}"
    else
      mkdir -p "$WORKTREE_BASE"
      git worktree add "$WT_PATH" -b "$WT_BRANCH" "$BRANCH_NAME"
      echo "워크트리 생성: ${WT_PATH} (${WT_BRANCH})"
    fi

    # .ax-status 초기화
    echo '{"status":"building"}' > "${WT_PATH}/.ax-status"

    # .ax-brief.md 존재 확인
    if [[ ! -f "${WT_PATH}/.ax-brief.md" ]]; then
      echo "ERROR: ${WT_PATH}/.ax-brief.md 없음. 메인 세션에서 먼저 생성 필요." >&2
      exit 1
    fi

    # 메인 세션이 tmux 안에서 구동 중이어야 함. 밖이면 무음 스킵 대신 ERROR로 중단.
    if [[ -z "${TMUX:-}" ]]; then
      echo "ERROR: tmux 세션 밖에서 실행 중. ax-build 3-b(병렬)는 tmux 안에서만 동작합니다." >&2
      echo "  → tmux new-session -s ax-build" >&2
      echo "  → 그 안에서 claude 세션 시작 → /ax-build 재실행" >&2
      exit 1
    fi

    # 워커 비정상 종료 시 윈도우가 사라지면 디버깅 흔적이 증발하므로 현재 세션 remain-on-exit on.
    tmux set-option remain-on-exit on 2>/dev/null || true

    if tmux list-windows -F '#{window_name}' 2>/dev/null | grep -q "^${WORK_NAME}$"; then
      echo "tmux 윈도우 이미 존재: ${WORK_NAME}"
    else
      # -d: 포커스를 메인에 유지 (자동 전환으로 오너 키 입력이 워커로 새는 것 방지)
      # -p 제거: claude는 기본 인터랙티브 TUI. -p를 주면 응답 1회 출력 후 종료하여 워커가 조용히 죽음.
      # positional prompt: TUI 시작과 동시에 brief 참조 지시 주입.
      tmux new-window -d -n "${WORK_NAME}" \
        "cd $(pwd)/${WT_PATH} && claude 'Read .ax-brief.md and follow the instructions.'"
      echo "tmux 윈도우 생성: ${WORK_NAME} (백그라운드, 포커스 유지)"
    fi

    echo "---"
    echo "worktree: ${WT_PATH}"
    echo "branch: ${WT_BRANCH}"
    echo "port: ${PORT}"
    ;;

  status)
    echo "=== 워크트리 상태 ==="
    for wt in ${WORKTREE_BASE}/*/; do
      NAME=$(basename "$wt")
      if [[ -f "${wt}.ax-status" ]]; then
        STATUS=$(cat "${wt}.ax-status")
        echo "${NAME}: ${STATUS}"
      else
        echo "${NAME}: (상태 파일 없음)"
      fi
    done
    ;;

  merge)
    VERSION="${2:?사용법: ax-build-orchestrator.sh merge <version>}"
    BRANCH_NAME="version/${VERSION}"

    echo "=== version branch 머지 ==="
    git checkout "${BRANCH_NAME}"

    for wt in ${WORKTREE_BASE}/*/; do
      NAME=$(basename "$wt")
      STATUS_FILE="${wt}.ax-status"

      if [[ ! -f "$STATUS_FILE" ]]; then
        echo "SKIP: ${NAME} — 상태 파일 없음"
        continue
      fi

      STATUS=$(cat "$STATUS_FILE" | grep -o '"status":"[^"]*"' | head -1 | sed 's/"status":"//;s/"//')

      if [[ "$STATUS" == "merge-ready" ]]; then
        WT_BRANCH="${BRANCH_NAME}-${NAME}"
        echo "머지: ${WT_BRANCH} → ${BRANCH_NAME}"
        git merge "$WT_BRANCH" -m "머지: ${NAME} → ${BRANCH_NAME}" || {
          echo "ERROR: ${NAME} 머지 충돌 — 수동 해소 필요"
          exit 1
        }
      else
        echo "SKIP: ${NAME} — 상태: ${STATUS} (merge-ready 아님)"
      fi
    done

    echo "---"
    echo "머지 완료. version branch: ${BRANCH_NAME}"
    ;;

  *)
    echo "ERROR: 알 수 없는 명령: ${COMMAND}" >&2
    echo "사용법: ax-build-orchestrator.sh <init|worktree|status|merge> [args]" >&2
    exit 1
    ;;
esac
