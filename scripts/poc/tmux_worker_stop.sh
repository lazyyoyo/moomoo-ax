#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
tmux_worker_stop.sh --socket <path> --session <name> [--log-dir <dir>]

Stop a detached tmux worker session.
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[tmux-worker-stop] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

SOCKET=""
SESSION=""
LOG_DIR=""

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
    --log-dir)
      require_arg "$1" "${2:-}"
      LOG_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[tmux-worker-stop] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SOCKET" || -z "$SESSION" ]]; then
  echo "[tmux-worker-stop] --socket and --session are required" >&2
  usage >&2
  exit 2
fi

tmux -S "$SOCKET" kill-session -t "$SESSION"

if [[ -n "$LOG_DIR" ]]; then
  mkdir -p "$LOG_DIR"

  META_PATH="$LOG_DIR/meta.json"
  EVENTS_PATH="$LOG_DIR/events.jsonl"
  STDERR_PATH="$LOG_DIR/stderr.log"
  LAST_MESSAGE_PATH="$LOG_DIR/last-message.txt"
  STOPPED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  if [[ ! -f "$META_PATH" ]]; then
    python3 - <<'PY' "$META_PATH" "$STOPPED_AT" "$SOCKET" "$SESSION" \
      "$EVENTS_PATH" "$STDERR_PATH" "$LAST_MESSAGE_PATH"
import json
import sys

meta_path = sys.argv[1]
stopped_at = sys.argv[2]
socket = sys.argv[3]
session = sys.argv[4]
events_path = sys.argv[5]
stderr_path = sys.argv[6]
last_message_path = sys.argv[7]

payload = {
    "status": "stopped",
    "partial": True,
    "exit_code": None,
    "duration_sec": None,
    "stopped_at_utc": stopped_at,
    "socket": socket,
    "session": session,
    "events_path": events_path,
    "stderr_path": stderr_path,
    "last_message_path": last_message_path,
}

with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY
  fi
fi

echo "[tmux-worker-stop] stopped session=$SESSION"
