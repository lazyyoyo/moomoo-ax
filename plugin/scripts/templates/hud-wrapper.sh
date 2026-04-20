#!/usr/bin/env bash
# team-ax statusline 래퍼 — 글로벌 ~/.claude/hud/ax-statusline.sh로 설치됨.
#
# 역할:
#   ~/.claude/plugins/installed_plugins.json에서 team-ax 설치 경로를 런타임에 resolve.
#   그 경로의 scripts/ax-statusline.sh로 stdin/stdout 그대로 exec.
#
# 이유:
#   플러그인 cache 경로는 버전마다 다름 (.../team-ax/0.6.0/... → .../team-ax/0.7.0/...)
#   글로벌 settings.json에 고정 경로를 박으면 업데이트 시마다 깨짐.
#   래퍼가 매번 resolve하므로 버전 bump 후 재설치 불필요.
#
# 폴백:
#   team-ax 미설치 / installed_plugins.json 없음 → 조용히 0 exit (statusline 공란).

set -u

INSTALLED_JSON="$HOME/.claude/plugins/installed_plugins.json"
[[ -f "$INSTALLED_JSON" ]] || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# team-ax@<marketplace> 형식 키 — 어느 marketplace에서 설치됐든 첫 항목 사용
INSTALL_PATH=$(jq -r '
  .plugins
  | to_entries[]
  | select(.key | startswith("team-ax@"))
  | .value[0].installPath
' "$INSTALLED_JSON" 2>/dev/null | head -1)

[[ -z "$INSTALL_PATH" || ! -d "$INSTALL_PATH" ]] && exit 0

TARGET="$INSTALL_PATH/scripts/ax-statusline.sh"
[[ -x "$TARGET" ]] || exit 0

exec "$TARGET" "$@"
