#!/bin/bash
# Anthropic OAuth API에서 계정 quota를 조회해 캐시 파일로 저장.
#
# 출처: lazyyoyo/my-agent-office의 statusline 플러그인 fetch-usage.sh를 이식.
#       원본 위치: plugins/statusline/scripts/fetch-usage.sh
#
# 동작:
# - 캐시 신선(120초 이내)이면 즉시 0 exit
# - macOS keychain에서 Claude Code OAuth 토큰 조회
# - GET https://api.anthropic.com/api/oauth/usage
# - 정상 JSON만 캐시에 저장. 실패 시 mtime만 touch (rate limit 악순환 방지)
#
# 의존성: macOS `security` / `python3` / `curl` / `jq`. 없으면 조용히 1 exit.
# 호출: statusline.sh가 매 refresh마다 백그라운드(`&`)로 실행 — exit code는 statusline 표시에 영향 없음.

set -u

CACHE_FILE="/tmp/claude-usage-cache.json"
CACHE_MAX_AGE=120  # seconds

# 캐시가 신선하면 스킵
if [ -f "$CACHE_FILE" ]; then
  AGE=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE") ))
  [ "$AGE" -lt "$CACHE_MAX_AGE" ] && exit 0
fi

# 의존성 체크 — 없으면 조용히 1 exit (statusline은 캐시 없이 정상 동작)
command -v security >/dev/null 2>&1 || exit 1
command -v python3  >/dev/null 2>&1 || exit 1
command -v curl     >/dev/null 2>&1 || exit 1
command -v jq       >/dev/null 2>&1 || exit 1

TOKEN=$(security find-generic-password -s "Claude Code-credentials" -a "$(whoami)" -w 2>/dev/null \
  | python3 -c "
import sys, json, subprocess

raw_bytes = sys.stdin.buffer.read()

def extract_token(text):
    idx = text.find('{')
    if idx < 0: return None
    for end in range(idx+1, len(text)+1):
        try:
            obj = json.loads(text[idx:end])
            if 'claudeAiOauth' in obj:
                return obj['claudeAiOauth'].get('accessToken', '')
            return obj.get('accessToken', '')
        except: continue
    return None

# 평문 JSON 시도
token = extract_token(raw_bytes.decode('utf-8', errors='ignore'))

# hex 인코딩 폴백
if not token:
    try:
        decoded = subprocess.run(['xxd', '-r', '-p'], input=raw_bytes, capture_output=True)
        if decoded.returncode == 0:
            token = extract_token(decoded.stdout.decode('utf-8', errors='ignore'))
    except: pass

if token:
    print(token)
    sys.exit(0)
sys.exit(1)
" 2>/dev/null)
[ -z "$TOKEN" ] && exit 1

RESP=$(curl -s --max-time 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "anthropic-beta: oauth-2025-04-20" \
  https://api.anthropic.com/api/oauth/usage 2>/dev/null)

[ -z "$RESP" ] && { touch "$CACHE_FILE"; exit 1; }

# 유효한 JSON인지 검증 — 에러 응답(HTML/텍스트)이면 캐시 덮어쓰기 건너뜀
if ! echo "$RESP" | python3 -c "import json, sys; json.loads(sys.stdin.read())" 2>/dev/null; then
  touch "$CACHE_FILE"; exit 1
fi

# API 에러 응답(rate_limit_error 등)이면 캐시에 저장하지 않음
if echo "$RESP" | jq -e '.error' >/dev/null 2>&1; then
  touch "$CACHE_FILE"; exit 1
fi

echo "$RESP" > "$CACHE_FILE"
