#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

usage() {
  cat <<'EOF'
run_codex_worker.sh [root-wrapper options] [routing options]

Skill-facing wrapper for ax-implement. If --model/--profile are omitted,
the wrapper picks a model via select_codex_model.py and writes
<log-dir>/model-selection.json.

Routing options:
  --task-summary <text>       Task summary used for model routing
  --relevant-file <path>      Relevant file hint (repeatable)
  --changed-file <path>       Changed file hint (repeatable)
  --model <model>             Explicit model override
  --profile <profile>         Explicit profile override
  -h, --help                  Show help
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[ax-codex-worker] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

ROLE=""
TASK_ID=""
TASK_SUMMARY=""
LOG_DIR=""
MODEL=""
PROFILE=""
declare -a RELEVANT_FILES=()
declare -a CHANGED_FILES=()
declare -a FORWARD=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --role)
      require_arg "$1" "${2:-}"
      ROLE="$2"
      FORWARD+=("$1" "$2")
      shift 2
      ;;
    --task-id)
      require_arg "$1" "${2:-}"
      TASK_ID="$2"
      FORWARD+=("$1" "$2")
      shift 2
      ;;
    --task-summary)
      require_arg "$1" "${2:-}"
      TASK_SUMMARY="$2"
      shift 2
      ;;
    --relevant-file)
      require_arg "$1" "${2:-}"
      RELEVANT_FILES+=("$2")
      shift 2
      ;;
    --changed-file)
      require_arg "$1" "${2:-}"
      CHANGED_FILES+=("$2")
      shift 2
      ;;
    --log-dir)
      require_arg "$1" "${2:-}"
      LOG_DIR="$2"
      FORWARD+=("$1" "$2")
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
    --cd|--task-file|--sandbox|--add-dir|--last-message|--result-path)
      require_arg "$1" "${2:-}"
      FORWARD+=("$1" "$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ax-codex-worker] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$ROLE" || -z "$TASK_ID" || -z "$LOG_DIR" ]]; then
  echo "[ax-codex-worker] --role, --task-id, and --log-dir are required" >&2
  usage >&2
  exit 2
fi

mkdir -p "$LOG_DIR"
SELECTION_PATH="$LOG_DIR/model-selection.json"

if [[ -z "$MODEL" && -z "$PROFILE" ]]; then
  SELECT_CMD=(
    python3 "$SCRIPT_DIR/select_codex_model.py"
    --role "$ROLE"
    --task-id "$TASK_ID"
    --task-summary "$TASK_SUMMARY"
    --output "$SELECTION_PATH"
  )

  if [[ ${#RELEVANT_FILES[@]} -gt 0 ]]; then
    for path in "${RELEVANT_FILES[@]}"; do
      SELECT_CMD+=(--relevant-file "$path")
    done
  fi
  if [[ ${#CHANGED_FILES[@]} -gt 0 ]]; then
    for path in "${CHANGED_FILES[@]}"; do
      SELECT_CMD+=(--changed-file "$path")
    done
  fi

  "${SELECT_CMD[@]}" >/dev/null

  MODEL="$(python3 - <<'PY' "$SELECTION_PATH"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    payload = json.load(f)
print(payload.get("model") or "")
PY
)"
  PROFILE="$(python3 - <<'PY' "$SELECTION_PATH"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    payload = json.load(f)
print(payload.get("profile") or "")
PY
)"
else
  SCOPE_PATH="$LOG_DIR/explicit-scope-files.txt"
  : >"$SCOPE_PATH"
  if [[ ${#RELEVANT_FILES[@]} -gt 0 ]]; then
    for path in "${RELEVANT_FILES[@]}"; do
      printf '%s\n' "$path" >>"$SCOPE_PATH"
    done
  fi
  if [[ ${#CHANGED_FILES[@]} -gt 0 ]]; then
    for path in "${CHANGED_FILES[@]}"; do
      printf '%s\n' "$path" >>"$SCOPE_PATH"
    done
  fi

  python3 - <<'PY' "$SELECTION_PATH" "$ROLE" "$TASK_ID" "$MODEL" "$PROFILE" "$SCOPE_PATH"
import json
import sys

selection_path = sys.argv[1]
role = sys.argv[2]
task_id = sys.argv[3]
model = sys.argv[4] or None
profile = sys.argv[5] or None
scope_path = sys.argv[6]

with open(scope_path, encoding="utf-8") as f:
    scope_files = [line.strip() for line in f if line.strip()]

payload = {
    "role": role,
    "task_id": task_id,
    "tier": "explicit",
    "model": model,
    "profile": profile,
    "risk": "explicit_override",
    "reasons": ["explicit model/profile override via wrapper args"],
    "scope_files": scope_files,
}

with open(selection_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY
fi

if [[ -n "$MODEL" ]]; then
  FORWARD+=(--model "$MODEL")
fi

if [[ -n "$PROFILE" ]]; then
  FORWARD+=(--profile "$PROFILE")
fi

RUNNER_PATH="$PLUGIN_ROOT/scripts/codex/run_worker.sh"

if [[ ! -x "$RUNNER_PATH" ]]; then
  echo "[ax-codex-worker] bundled codex runner not found: $RUNNER_PATH" >&2
  exit 2
fi

exec "$RUNNER_PATH" "${FORWARD[@]}"
