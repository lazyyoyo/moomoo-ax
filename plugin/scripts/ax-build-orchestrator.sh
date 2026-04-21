#!/usr/bin/env bash
# ax-build 오케스트레이터 (v0.8)
#
# 병렬 엔진 재설계: worktree 제거 + Codex 워커 + 파일 whitelist 격리 + 단일 브랜치.
# 스크립트는 원시 도구(브랜치/pane/상태 수집)만 제공하고, 태스크 선택·커밋 등의 로직은 lead(Claude)의 SKILL.md가 담당한다.
#
# 사용법:
#   ax-build-orchestrator.sh precheck
#   ax-build-orchestrator.sh init <version>                — version branch 생성 + 폴더 승격
#   ax-build-orchestrator.sh prepare-window                — tmux 'ax-workers' 윈도우 준비 (tiled)
#   ax-build-orchestrator.sh spawn <version> <task_id> [model]
#                                                          — 워커 pane 하나 스폰 (codex exec '$ax-execute <inbox>')
#   ax-build-orchestrator.sh status                        — .ax/workers/*/result.json 집계
#   ax-build-orchestrator.sh cleanup                       — 'ax-workers' 윈도우 닫기 + (옵션) .ax 아카이브
#
# 전제:
#   - 메인 세션이 tmux 안에서 기동 (precheck 확인)
#   - codex CLI 설치 + 로그인 (precheck 확인)
#   - .ax/plan.json 이 이미 생성됨 (planner 산출)
#   - .ax/workers/<task_id>/inbox.md 가 미리 기록됨 (lead가 생성)

set -euo pipefail

WORKERS_DIR=".ax/workers"
WORKERS_WINDOW="ax-workers"
DEFAULT_MODEL="${AX_CODEX_MODEL:-gpt-5-codex}"

COMMAND="${1:?사용법: ax-build-orchestrator.sh <precheck|init|prepare-window|spawn|status|cleanup> [args]}"

# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------

die() {
  echo "ERROR: $*" >&2
  exit 1
}

need_tmux() {
  if [[ -z "${TMUX:-}" ]]; then
    die "tmux 세션 밖에서 실행 중. ax-build는 tmux 안에서만 동작.
  → tmux new-session -s ax
  → 그 안에서 claude 세션 시작 → /ax-build 재실행"
  fi
}

ensure_workers_window() {
  if tmux list-windows -F '#{window_name}' 2>/dev/null | grep -qx "$WORKERS_WINDOW"; then
    return 0
  fi
  # 백그라운드로 새 윈도우 — 메인 포커스 유지
  tmux new-window -d -n "$WORKERS_WINDOW" "echo 'ax-workers ready'; exec $SHELL -l"
  tmux select-layout -t "$WORKERS_WINDOW" tiled 2>/dev/null || true
}

# -----------------------------------------------------------------------------
# precheck
# -----------------------------------------------------------------------------

cmd_precheck() {
  local fail=0

  # tmux
  if [[ -z "${TMUX:-}" ]]; then
    echo "✗ tmux: 세션 밖에서 실행 중"
    echo "  → tmux new-session -s ax  → 그 안에서 claude 시작"
    fail=1
  else
    echo "✓ tmux: $(tmux display-message -p '#S')"
  fi

  # codex 설치
  if ! command -v codex >/dev/null 2>&1; then
    echo "✗ codex CLI: 미설치"
    echo "  → npm install -g @openai/codex"
    fail=1
  else
    echo "✓ codex: $(codex --version 2>/dev/null || echo unknown)"
  fi

  # codex 로그인 (0.120 기준: login status 또는 exec smoke)
  if command -v codex >/dev/null 2>&1; then
    if codex login status >/dev/null 2>&1; then
      echo "✓ codex login: OK"
    else
      # 일부 버전은 login status 서브커맨드 없음. 그냥 경고만.
      echo "? codex login: 상태 확인 불가 (codex login status 지원 안 함). 실제 호출 시 인증 에러 나면 'codex login' 실행"
    fi
  fi

  # git
  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "✗ git: 리포가 아님"
    fail=1
  else
    echo "✓ git: $(git rev-parse --show-toplevel)"
  fi

  # ax-execute 스킬 codex 설치 확인
  if [[ -f "$HOME/.codex/skills/ax-execute/SKILL.md" ]]; then
    echo "✓ codex skill ax-execute: $HOME/.codex/skills/ax-execute/"
  else
    echo "✗ codex skill ax-execute: 미설치"
    echo "  → /ax-codex install (또는 bash plugin/scripts/ax-codex.sh install)"
    fail=1
  fi

  [[ $fail -eq 0 ]] || exit 1
  echo "---"
  echo "precheck OK"
}

# -----------------------------------------------------------------------------
# init — version branch 생성 + 폴더 승격
# -----------------------------------------------------------------------------

cmd_init() {
  local version="${1:?사용법: init <version> (예: v0.8.0)}"
  local branch="version/${version}"

  # Phase A 산출물 커밋 + 폴더 승격
  if [[ -d "versions/undefined" ]]; then
    git add versions/undefined/ || true
    git commit -m "Phase A 완료 — ${version} scope 확정" 2>/dev/null || echo "Phase A 산출물 이미 커밋됨"
    mv "versions/undefined" "versions/${version}"
    git add "versions/"
    git commit -m "${version} 폴더 승격"
  fi

  # version branch
  if git show-ref --verify --quiet "refs/heads/${branch}"; then
    echo "version branch 이미 존재: ${branch}"
    git checkout "${branch}"
  else
    git checkout -b "${branch}"
    echo "version branch 생성: ${branch}"
  fi

  mkdir -p "${WORKERS_DIR}"
  echo "---"
  echo "version: ${version}"
  echo "branch: ${branch}"
  echo "workers dir: ${WORKERS_DIR}"
}

# -----------------------------------------------------------------------------
# prepare-window — ax-workers 윈도우 준비
# -----------------------------------------------------------------------------

cmd_prepare_window() {
  need_tmux
  # 워커 비정상 종료 시 pane 보존 (디버깅용)
  tmux set-option remain-on-exit on 2>/dev/null || true
  ensure_workers_window
  echo "tmux window: ${WORKERS_WINDOW} ready"
}

# -----------------------------------------------------------------------------
# spawn — 워커 pane 하나 스폰
# -----------------------------------------------------------------------------

cmd_spawn() {
  local version="${1:?사용법: spawn <version> <task_id> [model]}"
  local task_id="${2:?task_id 필요}"
  local model="${3:-$DEFAULT_MODEL}"
  local inbox=".ax/workers/${task_id}/inbox.md"

  need_tmux

  [[ -f "$inbox" ]] || die "inbox 없음: ${inbox}
  → lead가 .ax/plan.json 기반으로 inbox.md를 먼저 생성해야 함"

  ensure_workers_window

  # 이미 pane이 있는지 — pane title로 태스크 id 매칭
  if tmux list-panes -t "$WORKERS_WINDOW" -F '#{pane_title}' 2>/dev/null | grep -qx "$task_id"; then
    echo "pane 이미 존재: ${task_id} (건너뜀)"
    return 0
  fi

  # pane 목록이 비어있으면(방금 만든 윈도우) 그 첫 pane을 사용, 아니면 split
  local pane_count
  pane_count=$(tmux list-panes -t "$WORKERS_WINDOW" | wc -l | tr -d ' ')

  local repo_root
  repo_root=$(git rev-parse --show-toplevel)

  local spawn_cmd="cd '${repo_root}' && codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write -c model='${model}' '\$ax-execute ${inbox}'"

  if [[ "$pane_count" == "1" ]]; then
    # 첫 pane: send-keys로 명령 주입
    tmux send-keys -t "${WORKERS_WINDOW}.0" "$spawn_cmd" Enter
    tmux select-pane -t "${WORKERS_WINDOW}.0" -T "$task_id"
  else
    # 추가 pane split — tiled 유지
    tmux split-window -d -t "$WORKERS_WINDOW" -c "$repo_root" "$spawn_cmd"
    tmux select-layout -t "$WORKERS_WINDOW" tiled 2>/dev/null || true
    # 마지막 pane에 title 부착
    local last_pane
    last_pane=$(tmux list-panes -t "$WORKERS_WINDOW" -F '#{pane_id}' | tail -1)
    tmux select-pane -t "$last_pane" -T "$task_id"
  fi

  echo "spawn: ${task_id} (model=${model})"
  echo "  inbox: ${inbox}"
}

# -----------------------------------------------------------------------------
# status — 워커 result.json 집계
# -----------------------------------------------------------------------------

cmd_status() {
  if [[ ! -d "$WORKERS_DIR" ]]; then
    echo "(워커 디렉토리 없음: ${WORKERS_DIR})"
    return 0
  fi

  local done_count=0 blocked_count=0 error_count=0 inprogress_count=0 total=0

  echo "=== 워커 상태 ==="
  for worker_dir in "$WORKERS_DIR"/*/; do
    [[ -d "$worker_dir" ]] || continue
    local task_id
    task_id=$(basename "$worker_dir")
    local result="${worker_dir}result.json"
    total=$((total + 1))

    if [[ -f "$result" ]]; then
      local status
      status=$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' "$result" | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
      local summary
      summary=$(grep -o '"summary"[[:space:]]*:[[:space:]]*"[^"]*"' "$result" | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
      case "$status" in
        done)    done_count=$((done_count+1)) ;;
        blocked) blocked_count=$((blocked_count+1)) ;;
        error)   error_count=$((error_count+1)) ;;
        *)       inprogress_count=$((inprogress_count+1)) ;;
      esac
      echo "  ${task_id}: ${status:-?} — ${summary:-}"
    else
      inprogress_count=$((inprogress_count+1))
      echo "  ${task_id}: (진행 중 — result.json 없음)"
    fi
  done

  echo "---"
  echo "total=${total} done=${done_count} blocked=${blocked_count} error=${error_count} in-progress=${inprogress_count}"
}

# -----------------------------------------------------------------------------
# cleanup — ax-workers 윈도우 닫기
# -----------------------------------------------------------------------------

cmd_cleanup() {
  need_tmux
  if tmux list-windows -F '#{window_name}' 2>/dev/null | grep -qx "$WORKERS_WINDOW"; then
    tmux kill-window -t "$WORKERS_WINDOW" 2>/dev/null || true
    echo "윈도우 제거: ${WORKERS_WINDOW}"
  else
    echo "윈도우 없음: ${WORKERS_WINDOW}"
  fi
}

# -----------------------------------------------------------------------------
# dispatch
# -----------------------------------------------------------------------------

case "$COMMAND" in
  precheck)        cmd_precheck ;;
  init)            shift; cmd_init "$@" ;;
  prepare-window)  cmd_prepare_window ;;
  spawn)           shift; cmd_spawn "$@" ;;
  status)          cmd_status ;;
  cleanup)         cmd_cleanup ;;
  *)
    die "알 수 없는 명령: ${COMMAND}
사용법: $(basename "$0") <precheck|init|prepare-window|spawn|status|cleanup> [args]"
    ;;
esac
