#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
tmux_worker_capture.sh --socket <path> --session <name> [--lines <n>]

Capture recent pane output from a detached tmux worker session.
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[tmux-worker-capture] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

SOCKET=""
SESSION=""
LINES="200"

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
    --lines)
      require_arg "$1" "${2:-}"
      LINES="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[tmux-worker-capture] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SOCKET" || -z "$SESSION" ]]; then
  echo "[tmux-worker-capture] --socket and --session are required" >&2
  usage >&2
  exit 2
fi

tmux -S "$SOCKET" capture-pane -p -t "$SESSION" -S "-$LINES"
