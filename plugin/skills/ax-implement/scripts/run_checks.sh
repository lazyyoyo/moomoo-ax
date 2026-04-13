#!/usr/bin/env bash
# package.json 의 scripts 에서 lint / typecheck / test / build 를 자동 감지해 순차 실행
# 실패 즉시 exit. stdout 에 JSON summary.
set -euo pipefail

CMD="${PKG_MANAGER:-npm}"
[[ -f package.json ]] || { printf '{"status":"setup_failure","reason":"package.json not found"}\n' >&2; exit 2; }
command -v jq >/dev/null || { printf '{"status":"setup_failure","reason":"jq not installed"}\n' >&2; exit 2; }
command -v "$CMD" >/dev/null || { printf '{"status":"setup_failure","reason":"%s not installed"}\n' "$CMD" >&2; exit 2; }

STEPS=(lint typecheck test build)
RESULTS_JSON="["

has_script() {
  jq -e --arg s "$1" '.scripts[$s] // empty' package.json >/dev/null
}

for step in "${STEPS[@]}"; do
  if has_script "$step"; then
    echo "=== $CMD run $step ===" >&2
    if "$CMD" run "$step" >&2; then
      RESULTS_JSON="${RESULTS_JSON}{\"step\":\"$step\",\"result\":\"pass\"},"
    else
      RESULTS_JSON="${RESULTS_JSON}{\"step\":\"$step\",\"result\":\"fail\"}]"
      printf '{"status":"fail","failed_step":"%s","results":%s}\n' "$step" "$RESULTS_JSON"
      exit 1
    fi
  else
    RESULTS_JSON="${RESULTS_JSON}{\"step\":\"$step\",\"result\":\"skip\"},"
  fi
done

RESULTS_JSON="${RESULTS_JSON%,}]"
printf '{"status":"pass","results":%s}\n' "$RESULTS_JSON"
exit 0
