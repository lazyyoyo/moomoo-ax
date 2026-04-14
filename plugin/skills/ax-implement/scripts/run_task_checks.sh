#!/usr/bin/env bash
# task 단위 deterministic checks 실행기.
# conductor 가 필요한 step만 선택해 JSON summary 로 저장한다.
set -euo pipefail

CMD="${PKG_MANAGER:-npm}"
OUTPUT=""
declare -a STEPS=()

usage() {
  cat <<'EOF'
run_task_checks.sh --step <lint|typecheck|test|build> [--step ...] [--output <path>]

Runs only the requested package.json scripts and prints JSON summary.
Missing scripts are recorded as skip.
EOF
}

require_arg() {
  local flag="$1"
  local value="${2:-}"
  if [[ -z "$value" ]]; then
    echo "[run_task_checks] missing value for $flag" >&2
    usage >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --step)
      require_arg "$1" "${2:-}"
      STEPS+=("$2")
      shift 2
      ;;
    --output)
      require_arg "$1" "${2:-}"
      OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[run_task_checks] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -f package.json ]] || { printf '{"status":"setup_failure","reason":"package.json not found"}\n' >&2; exit 2; }
command -v jq >/dev/null || { printf '{"status":"setup_failure","reason":"jq not installed"}\n' >&2; exit 2; }
command -v "$CMD" >/dev/null || { printf '{"status":"setup_failure","reason":"%s not installed"}\n' "$CMD" >&2; exit 2; }
[[ ${#STEPS[@]} -gt 0 ]] || { printf '{"status":"setup_failure","reason":"no steps requested"}\n' >&2; exit 2; }

has_script() {
  jq -e --arg s "$1" '.scripts[$s] // empty' package.json >/dev/null
}

RESULTS_JSON="["
OVERALL_STATUS="pass"
FAILED_STEP=""

for step in "${STEPS[@]}"; do
  if has_script "$step"; then
    echo "=== $CMD run $step ===" >&2
    if "$CMD" run "$step" >&2; then
      RESULTS_JSON="${RESULTS_JSON}{\"step\":\"$step\",\"result\":\"pass\"},"
    else
      RESULTS_JSON="${RESULTS_JSON}{\"step\":\"$step\",\"result\":\"fail\"},"
      OVERALL_STATUS="fail"
      FAILED_STEP="$step"
      break
    fi
  else
    RESULTS_JSON="${RESULTS_JSON}{\"step\":\"$step\",\"result\":\"skip\"},"
  fi
done

RESULTS_JSON="${RESULTS_JSON%,}]"
PAYLOAD=$(printf '{"status":"%s","failed_step":"%s","results":%s}\n' "$OVERALL_STATUS" "$FAILED_STEP" "$RESULTS_JSON")

if [[ -n "$OUTPUT" ]]; then
  mkdir -p "$(dirname "$OUTPUT")"
  printf '%s' "$PAYLOAD" >"$OUTPUT"
fi

printf '%s' "$PAYLOAD"

[[ "$OVERALL_STATUS" == "pass" ]] && exit 0
exit 1
