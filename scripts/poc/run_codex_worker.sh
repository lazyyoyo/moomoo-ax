#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
run_codex_worker.sh --cd <dir> --task-file <file> --log-dir <dir> [options]

One-shot Codex worker wrapper for PoC only.
This script is intentionally isolated from the main v0.3 runtime.

Required:
  --cd <dir>              Working directory passed to `codex exec --cd`
  --task-file <file>      Prompt file fed to Codex via stdin
  --log-dir <dir>         Output directory for logs and metadata

Optional:
  --sandbox <mode>        Sandbox mode (default: workspace-write)
  --add-dir <dir>         Additional writable directory (repeatable)
  --last-message <file>   Override last message output path
  -h, --help              Show this help

Behavior:
  - Always uses `codex exec --json`
  - Always adds `--skip-git-repo-check`
  - Always adds `--ephemeral`
  - Writes:
      events.jsonl
      stderr.log
      last-message.txt
      meta.json
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[codex-worker] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

WORK_DIR=""
TASK_FILE=""
LOG_DIR=""
SANDBOX="workspace-write"
LAST_MESSAGE=""
declare -a ADD_DIRS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
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
      echo "[codex-worker] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$WORK_DIR" || -z "$TASK_FILE" || -z "$LOG_DIR" ]]; then
  echo "[codex-worker] --cd, --task-file, --log-dir are required" >&2
  usage >&2
  exit 2
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "[codex-worker] codex CLI not found in PATH" >&2
  exit 127
fi

if [[ ! -d "$WORK_DIR" ]]; then
  echo "[codex-worker] working directory not found: $WORK_DIR" >&2
  exit 2
fi

if [[ ! -f "$TASK_FILE" ]]; then
  echo "[codex-worker] task file not found: $TASK_FILE" >&2
  exit 2
fi

mkdir -p "$LOG_DIR"

EVENTS_PATH="$LOG_DIR/events.jsonl"
STDERR_PATH="$LOG_DIR/stderr.log"
LAST_MESSAGE_PATH="${LAST_MESSAGE:-$LOG_DIR/last-message.txt}"
META_PATH="$LOG_DIR/meta.json"

CODEx_VERSION="$(codex --version 2>&1 | tr -d '\r')"
START_EPOCH="$(python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"
START_ISO="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

CMD=(
  codex exec
  --json
  --cd "$WORK_DIR"
  --sandbox "$SANDBOX"
  --skip-git-repo-check
  --ephemeral
  -o "$LAST_MESSAGE_PATH"
)

if [[ ${#ADD_DIRS[@]} -gt 0 ]]; then
  for dir in "${ADD_DIRS[@]}"; do
    CMD+=(--add-dir "$dir")
  done
fi

CMD+=(-)

if "${CMD[@]}" <"$TASK_FILE" >"$EVENTS_PATH" 2>"$STDERR_PATH"; then
  EXIT_CODE=0
else
  EXIT_CODE=$?
fi

END_EPOCH="$(python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"
END_ISO="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

python3 - <<'PY' "$META_PATH" "$EXIT_CODE" "$START_EPOCH" "$END_EPOCH" \
  "$START_ISO" "$END_ISO" "$CODEx_VERSION" "$WORK_DIR" "$TASK_FILE" \
  "$EVENTS_PATH" "$STDERR_PATH" "$LAST_MESSAGE_PATH" "$SANDBOX" "${CMD[@]}"
import json
import sys

meta_path = sys.argv[1]
exit_code = int(sys.argv[2])
start_epoch = float(sys.argv[3])
end_epoch = float(sys.argv[4])
start_iso = sys.argv[5]
end_iso = sys.argv[6]
codex_version = sys.argv[7]
work_dir = sys.argv[8]
task_file = sys.argv[9]
events_path = sys.argv[10]
stderr_path = sys.argv[11]
last_message_path = sys.argv[12]
sandbox = sys.argv[13]
command = sys.argv[14:]

payload = {
    "exit_code": exit_code,
    "start_time_utc": start_iso,
    "end_time_utc": end_iso,
    "duration_sec": round(end_epoch - start_epoch, 3),
    "codex_version": codex_version,
    "work_dir": work_dir,
    "task_file": task_file,
    "events_path": events_path,
    "stderr_path": stderr_path,
    "last_message_path": last_message_path,
    "sandbox": sandbox,
    "command": command,
}

with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY

echo "[codex-worker] exit_code=$EXIT_CODE"
echo "[codex-worker] events=$EVENTS_PATH"
echo "[codex-worker] stderr=$STDERR_PATH"
echo "[codex-worker] last_message=$LAST_MESSAGE_PATH"
echo "[codex-worker] meta=$META_PATH"

exit "$EXIT_CODE"
