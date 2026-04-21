#!/usr/bin/env bash
# ax-build 오케스트레이터
#
# 병렬 엔진: 단일 브랜치 + Codex 워커 + 파일 whitelist 격리. 워커는 메인 window를 split한 pane에 떠서 오너가 한 화면에서 관찰 가능.
# 스크립트는 원시 도구(브랜치/pane/상태 수집)만 제공하고, 태스크 선택·커밋 등의 로직은 lead(Claude)의 SKILL.md가 담당한다.
#
# 사용법:
#   ax-build-orchestrator.sh precheck
#   ax-build-orchestrator.sh init <version>        — version branch 생성 + 폴더 승격
#   ax-build-orchestrator.sh spawn <version> <task_id> [model]
#                                                  — 메인 window에 pane split + codex exec '$ax-execute <inbox>' 기동
#   ax-build-orchestrator.sh status                — .ax/workers/*/result.json 집계
#   ax-build-orchestrator.sh cleanup               — 워커 pane 전부 kill
#
# 전제:
#   - 메인 세션이 tmux 안에서 기동 (precheck 확인)
#   - codex CLI 설치 + 로그인 (precheck 확인)
#   - .ax/plan.json 이 이미 생성됨 (planner 산출)
#   - .ax/workers/<task_id>/inbox.md 가 미리 기록됨 (lead가 생성)
#
# 모델:
#   - 기본: codex CLI 자체 기본값 (~/.codex/config.toml 설정) 사용
#   - 오버라이드: 3번째 인자 또는 AX_CODEX_MODEL env

set -euo pipefail

WORKERS_DIR=".ax/workers"
WORKER_TAG_PREFIX="ax:"   # pane title prefix — 워커 pane 식별용

COMMAND="${1:?사용법: ax-build-orchestrator.sh <precheck|init|spawn|status|cleanup> [args]}"

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

# 현재 window에서 첫 워커 pane을 찾음 (추가 스폰의 split 기준)
find_first_worker_pane() {
  tmux list-panes -F '#{pane_id} #{pane_title}' 2>/dev/null \
    | awk -v tag="^${WORKER_TAG_PREFIX}" '$2 ~ tag {print $1; exit}'
}

# -----------------------------------------------------------------------------
# precheck
# -----------------------------------------------------------------------------

cmd_precheck() {
  local fail=0

  if [[ -z "${TMUX:-}" ]]; then
    echo "✗ tmux: 세션 밖에서 실행 중"
    echo "  → tmux new-session -s ax  → 그 안에서 claude 시작"
    fail=1
  else
    echo "✓ tmux: $(tmux display-message -p '#S')"
  fi

  if ! command -v codex >/dev/null 2>&1; then
    echo "✗ codex CLI: 미설치"
    echo "  → npm install -g @openai/codex"
    fail=1
  else
    echo "✓ codex: $(codex --version 2>/dev/null || echo unknown)"
  fi

  if command -v codex >/dev/null 2>&1; then
    if codex login status >/dev/null 2>&1; then
      echo "✓ codex login: OK"
    else
      echo "? codex login: 상태 확인 불가 (codex login status 지원 안 함). 호출 시 인증 에러 나면 'codex login' 실행"
    fi
  fi

  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "✗ git: 리포가 아님"
    fail=1
  else
    echo "✓ git: $(git rev-parse --show-toplevel)"
  fi

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

  if [[ -d "versions/undefined" ]]; then
    git add versions/undefined/ || true
    git commit -m "Phase A 완료 — ${version} scope 확정" 2>/dev/null || echo "Phase A 산출물 이미 커밋됨"
    mv "versions/undefined" "versions/${version}"
    git add "versions/"
    git commit -m "${version} 폴더 승격"
  fi

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
# spawn — 메인 window에 워커 pane split + codex 기동
# -----------------------------------------------------------------------------
#
# 레이아웃:
#   첫 워커 스폰 → 현재 window를 수직 split (왼쪽 메인 60%, 오른쪽 워커 40%)
#   추가 워커 스폰 → 첫 워커 pane을 수평 split (워커 영역 안에서 나눔)
#
# 메인 pane은 건드리지 않고, 워커 pane만 title로 식별한다.

cmd_spawn() {
  local version="${1:?사용법: spawn <version> <task_id> [model]}"
  local task_id="${2:?task_id 필요}"
  local model="${3:-${AX_CODEX_MODEL:-}}"   # 빈 값이면 codex CLI 기본 모델 사용
  local inbox=".ax/workers/${task_id}/inbox.md"
  local pane_tag="${WORKER_TAG_PREFIX}${task_id}"

  need_tmux
  [[ -f "$inbox" ]] || die "inbox 없음: ${inbox}
  → lead가 .ax/plan.json 기반으로 inbox.md를 먼저 생성해야 함"

  # 중복 방지 — 현재 window에 이미 같은 tag의 pane이 있으면 skip
  if tmux list-panes -F '#{pane_title}' 2>/dev/null | grep -qx "$pane_tag"; then
    echo "pane 이미 존재: ${task_id} (건너뜀)"
    return 0
  fi

  # 워커 비정상 종료 시 pane 보존 (디버깅용)
  tmux set-option remain-on-exit on 2>/dev/null || true

  local repo_root
  repo_root=$(git rev-parse --show-toplevel)

  # 모델 옵션 — 비우면 codex 기본
  local model_arg=""
  if [[ -n "$model" ]]; then
    model_arg="-c model=${model}"
  fi

  # 스폰 명령 문자열
  local spawn_cmd="codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write ${model_arg} \"\$ax-execute ${inbox}\""

  local first_worker
  first_worker=$(find_first_worker_pane)

  if [[ -z "$first_worker" ]]; then
    # 첫 워커: 현재 window를 수직 split. 왼쪽 메인(60%), 오른쪽 워커(40%)
    tmux split-window -h -l 40% -c "$repo_root" "$spawn_cmd"
  else
    # 추가 워커: 첫 워커 pane을 수평 split (워커 영역 안에서 나눔)
    tmux split-window -v -t "$first_worker" -c "$repo_root" "$spawn_cmd"
  fi

  # 새로 만든 pane에 title 부착 (`{last}` = 마지막으로 생성된 pane)
  tmux select-pane -t '{last}' -T "$pane_tag"

  # 포커스를 메인으로 복귀
  tmux last-pane 2>/dev/null || true

  echo "spawn: ${task_id} (model=${model:-codex 기본})"
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
# cleanup — 워커 pane 전부 kill
# -----------------------------------------------------------------------------

cmd_cleanup() {
  need_tmux
  local worker_panes
  worker_panes=$(tmux list-panes -a -F '#{pane_id} #{pane_title}' 2>/dev/null \
    | awk -v tag="^${WORKER_TAG_PREFIX}" '$2 ~ tag {print $1}')

  if [[ -z "$worker_panes" ]]; then
    echo "워커 pane 없음"
    return 0
  fi

  local killed=0
  while IFS= read -r pane; do
    [[ -z "$pane" ]] && continue
    if tmux kill-pane -t "$pane" 2>/dev/null; then
      echo "kill pane: $pane"
      killed=$((killed+1))
    fi
  done <<<"$worker_panes"
  echo "---"
  echo "killed: ${killed}"
}

# -----------------------------------------------------------------------------
# dispatch
# -----------------------------------------------------------------------------

case "$COMMAND" in
  precheck)  cmd_precheck ;;
  init)      shift; cmd_init "$@" ;;
  spawn)     shift; cmd_spawn "$@" ;;
  status)    cmd_status ;;
  cleanup)   cmd_cleanup ;;
  # prepare-window 는 v0.8.0의 레거시 서브커맨드. 이제 spawn이 알아서 처리하므로 nop으로 허용 (하위 호환).
  prepare-window)
    need_tmux
    tmux set-option remain-on-exit on 2>/dev/null || true
    echo "prepare-window: 이제 spawn이 메인 window split으로 처리합니다 (no-op)."
    ;;
  *)
    die "알 수 없는 명령: ${COMMAND}
사용법: $(basename "$0") <precheck|init|spawn|status|cleanup> [args]"
    ;;
esac
