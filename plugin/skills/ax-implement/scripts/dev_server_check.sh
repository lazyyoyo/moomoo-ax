#!/usr/bin/env bash
# dev server 가 돌고 있고 주어진 URL 이 HTTP 200 반환하는지 확인.
# usage: dev_server_check.sh <url>
# env DEV_SERVER_PATTERN 으로 pgrep 패턴 override 가능
set -euo pipefail

URL="${1:-}"
[[ -n "$URL" ]] || { printf '{"status":"setup_failure","reason":"missing url arg"}\n' >&2; exit 2; }
command -v curl >/dev/null || { printf '{"status":"setup_failure","reason":"curl not installed"}\n' >&2; exit 2; }
command -v pgrep >/dev/null || { printf '{"status":"setup_failure","reason":"pgrep not installed"}\n' >&2; exit 2; }

PATTERN="${DEV_SERVER_PATTERN:-next dev|bun dev|vite}"
if ! pgrep -f "$PATTERN" >/dev/null 2>&1; then
  printf '{"status":"fail","reason":"no dev server process","pattern":"%s"}\n' "$PATTERN"
  exit 1
fi

HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 "$URL" || echo "000")
if [[ "$HTTP_CODE" != "200" ]]; then
  printf '{"status":"fail","reason":"http %s","url":"%s"}\n' "$HTTP_CODE" "$URL"
  exit 1
fi

printf '{"status":"pass","url":"%s","http_code":"%s"}\n' "$URL" "$HTTP_CODE"
exit 0
