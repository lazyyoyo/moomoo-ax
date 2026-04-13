#!/usr/bin/env bash
# 유일 blocking review gate.
# 순서: gitleaks detect → eslint (changed files) → arch_compliance.py
# 미설치 → exit 2 (setup failure). red 하나라도 → exit 1. 전부 green → exit 0.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH_PY="${ARCH_COMPLIANCE_PATH:-$SCRIPT_DIR/arch_compliance.py}"

ensure_cmd() {
  if ! command -v "$1" >/dev/null; then
    printf '{"status":"setup_failure","missing":"%s"}\n' "$1" >&2
    exit 2
  fi
}

ensure_cmd git
ensure_cmd gitleaks
ensure_cmd npx
ensure_cmd python3
ensure_cmd jq

[[ -f "$ARCH_PY" ]] || {
  printf '{"status":"setup_failure","missing":"arch_compliance.py","path":"%s"}\n' "$ARCH_PY" >&2
  exit 2
}

RESULTS_JSON="["
OVERALL_STATUS="pass"

record() {
  local name="$1" code="$2" out="$3"
  local entry
  entry=$(jq -n --arg name "$name" --argjson code "$code" --arg out "$out" \
    '{name:$name, exit_code:$code, output:($out|.[:800])}')
  RESULTS_JSON="$RESULTS_JSON$entry,"
  if [[ $code -ne 0 ]]; then
    OVERALL_STATUS="fail"
  fi
}

# 1) gitleaks
echo "=== gitleaks detect ===" >&2
out=$(gitleaks detect --no-banner --redact 2>&1)
code=$?
record gitleaks "$code" "$out"

# 2) eslint — changed TS/JS files
echo "=== eslint ===" >&2
CHANGED=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(ts|tsx|js|jsx|mjs|cjs)$' || true)
if [[ -z "$CHANGED" ]]; then
  record eslint 0 "no changed JS/TS files; skip"
else
  # shellcheck disable=SC2086
  out=$(npx --no-install eslint --max-warnings 0 $CHANGED 2>&1)
  code=$?
  record eslint "$code" "$out"
fi

# 3) arch_compliance.py
echo "=== arch_compliance ===" >&2
out=$(python3 "$ARCH_PY" 2>&1)
code=$?
record arch_compliance "$code" "$out"

RESULTS_JSON="${RESULTS_JSON%,}]"
printf '{"status":"%s","checks":%s}\n' "$OVERALL_STATUS" "$RESULTS_JSON"

[[ "$OVERALL_STATUS" == "pass" ]] && exit 0
exit 1
