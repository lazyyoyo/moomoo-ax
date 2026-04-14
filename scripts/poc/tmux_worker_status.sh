#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
tmux_worker_status.sh --socket <path> --session <name>

Show basic status for a detached tmux worker session.
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[tmux-worker-status] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

SOCKET=""
SESSION=""

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
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[tmux-worker-status] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SOCKET" || -z "$SESSION" ]]; then
  echo "[tmux-worker-status] --socket and --session are required" >&2
  usage >&2
  exit 2
fi

if tmux -S "$SOCKET" has-session -t "$SESSION" 2>/dev/null; then
  echo "session_exists=true"
  tmux -S "$SOCKET" list-panes -t "$SESSION" \
    -F 'pane_id=#{pane_id} pane_dead=#{pane_dead} pane_exit_status=#{pane_exit_status} pane_current_command=#{pane_current_command}'
else
  echo "session_exists=false"
fi
