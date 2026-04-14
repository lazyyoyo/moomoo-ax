#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

usage() {
  cat <<'EOF'
run_worker.sh --role <executor|reviewer> --cd <dir> --task-id <id> --task-file <file> --log-dir <dir> [options]

Plugin-bundled Codex worker wrapper.

Required:
  --role <executor|reviewer>
  --task-id <id>
  --cd <dir>
  --task-file <file>
  --log-dir <dir>

Optional:
  --sandbox <mode>        Sandbox mode (default: workspace-write)
  --add-dir <dir>         Additional writable directory (repeatable)
  --model <model>         Override Codex model for this worker run
  --profile <profile>     Override Codex config profile for this worker run
  --last-message <file>   Override last-message output path
  --result-path <file>    Override normalized result path (default: <log-dir>/result.json)
  -h, --help              Show help
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

ROLE=""
TASK_ID=""
WORK_DIR=""
TASK_FILE=""
LOG_DIR=""
SANDBOX="workspace-write"
MODEL=""
PROFILE=""
LAST_MESSAGE=""
RESULT_PATH=""
declare -a ADD_DIRS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --role)
      require_arg "$1" "${2:-}"
      ROLE="$2"
      shift 2
      ;;
    --task-id)
      require_arg "$1" "${2:-}"
      TASK_ID="$2"
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
    --model)
      require_arg "$1" "${2:-}"
      MODEL="$2"
      shift 2
      ;;
    --profile)
      require_arg "$1" "${2:-}"
      PROFILE="$2"
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
    --result-path)
      require_arg "$1" "${2:-}"
      RESULT_PATH="$2"
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

if [[ -z "$ROLE" || -z "$TASK_ID" || -z "$WORK_DIR" || -z "$TASK_FILE" || -z "$LOG_DIR" ]]; then
  echo "[codex-worker] missing required arguments" >&2
  usage >&2
  exit 2
fi

if [[ "$ROLE" != "executor" && "$ROLE" != "reviewer" ]]; then
  echo "[codex-worker] --role must be executor or reviewer" >&2
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
RESULT_JSON_PATH="${RESULT_PATH:-$LOG_DIR/result.json}"
NORMALIZER_PATH="$SCRIPT_DIR/normalize_codex_result.py"

CODEX_VERSION="$(codex --version 2>&1 | tr -d '\r')"
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

if [[ -n "$MODEL" ]]; then
  CMD+=(--model "$MODEL")
fi

if [[ -n "$PROFILE" ]]; then
  CMD+=(--profile "$PROFILE")
fi

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
  "$START_ISO" "$END_ISO" "$CODEX_VERSION" "$WORK_DIR" "$TASK_FILE" \
  "$EVENTS_PATH" "$STDERR_PATH" "$LAST_MESSAGE_PATH" "$SANDBOX" "$MODEL" "$PROFILE" "${CMD[@]}"
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
model = sys.argv[14] or None
profile = sys.argv[15] or None
command = sys.argv[16:]

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
    "model": model,
    "profile": profile,
    "command": command,
}

with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY

python3 "$NORMALIZER_PATH" \
  --role "$ROLE" \
  --task-id "$TASK_ID" \
  --log-dir "$LOG_DIR" \
  --result-path "$RESULT_JSON_PATH" >/dev/null

echo "[codex-worker] role=$ROLE"
echo "[codex-worker] task_id=$TASK_ID"
echo "[codex-worker] exit_code=$EXIT_CODE"
echo "[codex-worker] events=$EVENTS_PATH"
echo "[codex-worker] stderr=$STDERR_PATH"
echo "[codex-worker] last_message=$LAST_MESSAGE_PATH"
echo "[codex-worker] meta=$META_PATH"
