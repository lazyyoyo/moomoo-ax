#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLUGIN_RUNNER="$REPO_ROOT/plugin/scripts/codex/run_worker.sh"

if [[ ! -x "$PLUGIN_RUNNER" ]]; then
  echo "[codex-worker] plugin runner not found: $PLUGIN_RUNNER" >&2
  exit 2
fi

exec "$PLUGIN_RUNNER" "$@"
