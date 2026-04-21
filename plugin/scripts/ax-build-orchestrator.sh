#!/usr/bin/env bash
# ax-build 오케스트레이터
#
# 병렬 엔진: 단일 브랜치 + Codex 워커 + 파일 whitelist 격리.
# 워커는 **백그라운드 프로세스**로 실행되며 stdout/stderr은 로그 파일로 저장된다.
# tmux 의존 없음. 모든 터미널에서 동작.
#
# 사용법:
#   ax-build-orchestrator.sh precheck
#   ax-build-orchestrator.sh init <version>        — version branch 생성 + 폴더 승격
#   ax-build-orchestrator.sh spawn <version> <task_id> [model]
#                                                  — codex exec 워커를 백그라운드로 기동, stdout→stdout.log, pid 저장
#   ax-build-orchestrator.sh status                — pid + result.json 집계
#   ax-build-orchestrator.sh logs <task_id>        — 워커 stdout.log 출력 (tail -f용: `logs <id> -f`)
#   ax-build-orchestrator.sh cleanup               — 남은 워커 프로세스 kill
#
# 전제:
#   - codex CLI 설치 + 로그인 (precheck 확인)
#   - .ax/plan.json 이 이미 생성됨 (planner 산출)
#   - .ax/workers/<task_id>/inbox.md 가 미리 기록됨 (lead가 생성)
#
# 모델:
#   - 기본: codex CLI 자체 기본값 (~/.codex/config.toml) 사용
#   - 오버라이드: 3번째 인자 또는 AX_CODEX_MODEL env

set -euo pipefail

WORKERS_DIR=".ax/workers"

COMMAND="${1:?사용법: ax-build-orchestrator.sh <precheck|init|spawn|status|logs|cleanup> [args]}"

# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------

die() {
  echo "ERROR: $*" >&2
  exit 1
}

# pid가 살아있는지
is_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

# -----------------------------------------------------------------------------
# precheck
# -----------------------------------------------------------------------------

cmd_precheck() {
  local fail=0

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
      echo "? codex login: 상태 확인 불가. 호출 시 인증 에러 나면 'codex login' 실행"
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
# spawn — 백그라운드 codex 워커 기동
# -----------------------------------------------------------------------------
#
# 각 워커는 `codex exec`를 백그라운드로 돌리고:
#   - stdout/stderr → .ax/workers/<task_id>/stdout.log
#   - pid          → .ax/workers/<task_id>/pid
#   - 종료 코드     → .ax/workers/<task_id>/exit_code (nohup wrapper가 기록)
#
# 워커 종료 후에도 로그가 파일로 남아 디버깅 가능.

cmd_spawn() {
  local version="${1:?사용법: spawn <version> <task_id> [model]}"
  local task_id="${2:?task_id 필요}"
  local model="${3:-${AX_CODEX_MODEL:-}}"   # 빈 값이면 codex 기본 모델
  local worker_dir=".ax/workers/${task_id}"
  local inbox="${worker_dir}/inbox.md"
  local log="${worker_dir}/stdout.log"
  local pid_file="${worker_dir}/pid"
  local exit_file="${worker_dir}/exit_code"

  [[ -f "$inbox" ]] || die "inbox 없음: ${inbox}
  → lead가 .ax/plan.json 기반으로 inbox.md를 먼저 생성해야 함"

  mkdir -p "$worker_dir"

  # 이미 살아있는 pid가 있으면 skip
  if [[ -f "$pid_file" ]]; then
    local existing
    existing=$(cat "$pid_file" 2>/dev/null || echo "")
    if is_alive "$existing"; then
      echo "worker 이미 실행 중: ${task_id} (pid=${existing})"
      return 0
    fi
  fi

  local model_arg=""
  if [[ -n "$model" ]]; then
    model_arg="-c model=${model}"
  fi

  # 백그라운드 실행 + 로그 redirect + exit code 캡처
  # subshell에서 codex 실행 → 종료 코드를 exit_code 파일로 남김
  (
    codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write ${model_arg} \
      "\$ax-execute ${inbox}" >"$log" 2>&1
    echo $? > "$exit_file"
  ) &

  local pid=$!
  echo "$pid" > "$pid_file"
  # 이전 exit_code 제거 (재스폰 대비)
  rm -f "$exit_file"

  echo "spawn: ${task_id} (pid=${pid}, model=${model:-codex 기본})"
  echo "  inbox: ${inbox}"
  echo "  log:   ${log}"
}

# -----------------------------------------------------------------------------
# status — 워커 pid + result.json 집계
# -----------------------------------------------------------------------------

cmd_status() {
  if [[ ! -d "$WORKERS_DIR" ]]; then
    echo "(워커 디렉토리 없음: ${WORKERS_DIR})"
    return 0
  fi

  local done_count=0 blocked_count=0 error_count=0 running_count=0 pending_count=0 total=0

  echo "=== 워커 상태 ==="
  for worker_dir in "$WORKERS_DIR"/*/; do
    [[ -d "$worker_dir" ]] || continue
    local task_id
    task_id=$(basename "$worker_dir")
    local result="${worker_dir}result.json"
    local pid_file="${worker_dir}pid"
    local exit_file="${worker_dir}exit_code"
    total=$((total + 1))

    local pid=""
    [[ -f "$pid_file" ]] && pid=$(cat "$pid_file" 2>/dev/null || echo "")

    local alive="no"
    is_alive "$pid" && alive="yes"

    if [[ -f "$result" ]]; then
      local status
      status=$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' "$result" | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
      local summary
      summary=$(grep -o '"summary"[[:space:]]*:[[:space:]]*"[^"]*"' "$result" | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
      case "$status" in
        done)    done_count=$((done_count+1)) ;;
        blocked) blocked_count=$((blocked_count+1)) ;;
        error)   error_count=$((error_count+1)) ;;
        *)       pending_count=$((pending_count+1)) ;;
      esac
      echo "  ${task_id}: ${status:-?} (pid=${pid:-?} alive=${alive}) — ${summary:-}"
    else
      # result.json 없음
      if [[ "$alive" == "yes" ]]; then
        running_count=$((running_count+1))
        echo "  ${task_id}: running (pid=${pid})"
      elif [[ -f "$exit_file" ]]; then
        # 프로세스 죽었는데 result.json 없음 = 비정상 종료
        local code
        code=$(cat "$exit_file" 2>/dev/null || echo "?")
        error_count=$((error_count+1))
        echo "  ${task_id}: ✗ 비정상 종료 (exit=${code}, result.json 없음 — 로그 확인: logs ${task_id})"
      else
        pending_count=$((pending_count+1))
        echo "  ${task_id}: (대기 중 — 스폰 안 됨)"
      fi
    fi
  done

  echo "---"
  echo "total=${total} done=${done_count} blocked=${blocked_count} error=${error_count} running=${running_count} pending=${pending_count}"
}

# -----------------------------------------------------------------------------
# logs — 워커 stdout.log 출력
# -----------------------------------------------------------------------------

cmd_logs() {
  local task_id="${1:?사용법: logs <task_id> [-f]}"
  local follow="${2:-}"
  local log=".ax/workers/${task_id}/stdout.log"

  [[ -f "$log" ]] || die "로그 없음: ${log}"

  if [[ "$follow" == "-f" ]]; then
    tail -f "$log"
  else
    cat "$log"
  fi
}

# -----------------------------------------------------------------------------
# cleanup — 살아있는 워커 프로세스 전부 kill
# -----------------------------------------------------------------------------

cmd_cleanup() {
  if [[ ! -d "$WORKERS_DIR" ]]; then
    echo "(워커 디렉토리 없음)"
    return 0
  fi

  local killed=0
  for worker_dir in "$WORKERS_DIR"/*/; do
    [[ -d "$worker_dir" ]] || continue
    local task_id
    task_id=$(basename "$worker_dir")
    local pid_file="${worker_dir}pid"
    [[ -f "$pid_file" ]] || continue
    local pid
    pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if is_alive "$pid"; then
      if kill "$pid" 2>/dev/null; then
        echo "kill: ${task_id} (pid=${pid})"
        killed=$((killed+1))
      fi
    fi
  done

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
  logs)      shift; cmd_logs "$@" ;;
  cleanup)   cmd_cleanup ;;
  # 레거시 서브커맨드 — no-op (하위 호환)
  prepare-window)
    echo "prepare-window: deprecated. spawn이 백그라운드로 직접 기동합니다."
    ;;
  *)
    die "알 수 없는 명령: ${COMMAND}
사용법: $(basename "$0") <precheck|init|spawn|status|logs|cleanup> [args]"
    ;;
esac
