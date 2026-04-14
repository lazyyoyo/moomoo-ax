#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
start_codex_tmux_worker.sh --socket <path> --session <name> --cd <dir> \
  --task-file <file> --log-dir <dir> [options]

Detached tmux host wrapper for the PoC Codex worker.

Required:
  --socket <path>         tmux socket path
  --session <name>        tmux session name
  --cd <dir>              Working directory passed through to the worker
  --task-file <file>      Prompt file
  --log-dir <dir>         Worker log directory

Optional:
  --sandbox <mode>        Sandbox mode (default: workspace-write)
  --add-dir <dir>         Additional writable directory (repeatable)
  --last-message <file>   Override last-message path
  -h, --help              Show this help
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[tmux-worker-start] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER_SCRIPT="$SCRIPT_DIR/run_codex_worker.sh"

SOCKET=""
SESSION=""
WORK_DIR=""
TASK_FILE=""
LOG_DIR=""
SANDBOX="workspace-write"
LAST_MESSAGE=""
declare -a ADD_DIRS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --socket)
      require_arg "$1" "${2:-}"
      SOCKET="$2"
      shift 2
      ;;
    --session)
      require_arg "$1" "${2:-}"
      SESSION="$2"
      shift 2
      ;;
    --cd)
      require_arg "$1" "${2:-}"
      WORK_DIR="$2"
      shift 2
      ;;
    --task-file)
      require_arg "$1" "${2:-}"
      TASK_FILE="$2"
      shift 2
      ;;
    --log-dir)
      require_arg "$1" "${2:-}"
      LOG_DIR="$2"
      shift 2
      ;;
    --sandbox)
      require_arg "$1" "${2:-}"
      SANDBOX="$2"
      shift 2
      ;;
    --add-dir)
      require_arg "$1" "${2:-}"
      ADD_DIRS+=("$2")
      shift 2
      ;;
    --last-message)
      require_arg "$1" "${2:-}"
      LAST_MESSAGE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[tmux-worker-start] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SOCKET" || -z "$SESSION" || -z "$WORK_DIR" || -z "$TASK_FILE" || -z "$LOG_DIR" ]]; then
  echo "[tmux-worker-start] required arguments missing" >&2
  usage >&2
  exit 2
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "[tmux-worker-start] tmux not found in PATH" >&2
  exit 127
fi

quote_arg() {
  printf '%q' "$1"
}

CMD=(
  bash "$WORKER_SCRIPT"
  --cd "$WORK_DIR"
  --task-file "$TASK_FILE"
  --log-dir "$LOG_DIR"
  --sandbox "$SANDBOX"
)

if [[ ${#ADD_DIRS[@]} -gt 0 ]]; then
  for dir in "${ADD_DIRS[@]}"; do
    CMD+=(--add-dir "$dir")
  done
fi

if [[ -n "$LAST_MESSAGE" ]]; then
  CMD+=(--last-message "$LAST_MESSAGE")
fi

SESSION_CMD=""
for arg in "${CMD[@]}"; do
  if [[ -n "$SESSION_CMD" ]]; then
    SESSION_CMD+=" "
  fi
  SESSION_CMD+="$(quote_arg "$arg")"
done

mkdir -p "$(dirname "$SOCKET")"
mkdir -p "$LOG_DIR"

tmux -S "$SOCKET" new-session -d -s "$SESSION" -c "$WORK_DIR" "$SESSION_CMD"

echo "[tmux-worker-start] socket=$SOCKET"
echo "[tmux-worker-start] session=$SESSION"
echo "[tmux-worker-start] work_dir=$WORK_DIR"
echo "[tmux-worker-start] log_dir=$LOG_DIR"
