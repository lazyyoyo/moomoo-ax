#!/usr/bin/env bash
# DEPRECATED — v0.7.1부터 /ax-codex install 스킬로 대체.
# 호환성을 위해 ax-codex.sh install로 위임만 수행.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "⚠️  install-local-skills.sh는 deprecated — /ax-codex install 권장" >&2
exec bash "$SCRIPT_DIR/ax-codex.sh" install
