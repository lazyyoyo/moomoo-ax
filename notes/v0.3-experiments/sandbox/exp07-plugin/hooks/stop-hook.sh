#!/bin/bash
# exp-07 Stop hook — logs each invocation, blocks first call to prove the loop mechanism works
set -euo pipefail

LOG_FILE="${EXP07_LOG:-/tmp/exp07-hook-log.txt}"
COUNT_FILE="${EXP07_COUNT:-/tmp/exp07-hook-count.txt}"

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Increment counter
if [[ -f "$COUNT_FILE" ]]; then
  COUNT=$(($(cat "$COUNT_FILE") + 1))
else
  COUNT=1
fi
echo "$COUNT" > "$COUNT_FILE"

# Log invocation
{
  echo "=== Stop hook fired #$COUNT at $(date -u +%FT%TZ) ==="
  echo "HOOK_INPUT: $HOOK_INPUT"
  echo ""
} >> "$LOG_FILE"

# On first invocation, block and inject a follow-up prompt
if [[ $COUNT -eq 1 ]]; then
  jq -n '{
    "decision": "block",
    "reason": "Now output exactly: EXP07_AFTER_HOOK",
    "systemMessage": "[exp07] Stop hook blocked exit; re-prompting"
  }'
  exit 0
fi

# Second and beyond — allow exit
exit 0
