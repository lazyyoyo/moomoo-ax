#!/usr/bin/env bash
# paperwork 인벤토리 스캔. ax-paperwork 1단계.
#
# 사용법: paperwork-inventory.sh
# 프로젝트 루트에서 실행.
#
# 출력: 문서별 메타 (경로, 수정일, 줄 수)

set -euo pipefail

echo "=== paperwork 인벤토리 ==="
echo "날짜: $(date +%Y-%m-%d)"
echo ""

scan_files() {
  local label="$1"
  shift
  local patterns=("$@")
  local count=0
  local lines=()
  for pat in "${patterns[@]}"; do
    while IFS= read -r -d '' f; do
      count=$((count + 1))
      local mtime
      mtime=$(git log -1 --format=%cs -- "$f" 2>/dev/null || date -r "$f" +%Y-%m-%d 2>/dev/null || echo "?")
      local numlines
      numlines=$(wc -l < "$f" | tr -d ' ')
      lines+=("  ${f} — ${mtime} — ${numlines}줄")
    done < <(find . -path ./node_modules -prune -o -type f -name "$pat" -print0 2>/dev/null)
  done
  echo "## ${label} (${count}건)"
  for l in "${lines[@]}"; do
    echo "$l"
  done
  echo ""
}

# 스펙
if [[ -d docs/specs ]]; then
  echo "## 스펙 (docs/specs/)"
  find docs/specs -type f -name "*.md" | while read -r f; do
    mtime=$(git log -1 --format=%cs -- "$f" 2>/dev/null || echo "?")
    numlines=$(wc -l < "$f" | tr -d ' ')
    echo "  ${f} — ${mtime} — ${numlines}줄"
  done
  echo ""
fi

# 단건 문서
for doc in docs/ARCHITECTURE.md docs/DESIGN_SYSTEM.md BACKLOG.md CHANGELOG.md CLAUDE.md AGENTS.md README.md; do
  if [[ -f "$doc" ]]; then
    mtime=$(git log -1 --format=%cs -- "$doc" 2>/dev/null || echo "?")
    numlines=$(wc -l < "$doc" | tr -d ' ')
    echo "- ${doc} — ${mtime} — ${numlines}줄"
  fi
done
echo ""

# flows
if [[ -d docs/flows ]]; then
  echo "## UX 플로우 (docs/flows/)"
  find docs/flows -type f -name "*.md" | while read -r f; do
    mtime=$(git log -1 --format=%cs -- "$f" 2>/dev/null || echo "?")
    echo "  ${f} — ${mtime}"
  done
  echo ""
fi

# ⏳ planned 마커 카운트
if [[ -d docs/specs ]]; then
  PLANNED_COUNT=$(grep -rl '⏳ planned' docs/specs/ 2>/dev/null | wc -l | tr -d ' ')
  echo "⏳ planned 마커: ${PLANNED_COUNT}개 파일"
fi

# BACKLOG 상태
if [[ -f BACKLOG.md ]]; then
  INBOX=$(awk '/^## inbox/,/^## [a-z]/' BACKLOG.md | grep -c '^- \[' || echo 0)
  READY=$(awk '/^## ready/,/^## [a-z]/' BACKLOG.md | grep -c '^- \[' || echo 0)
  DONE=$(awk '/^## done/,/^## [a-z]/' BACKLOG.md | grep -c '^- \[' || echo 0)
  echo "BACKLOG: inbox ${INBOX} / ready ${READY} / done ${DONE}"
fi

# 워크트리 활성 여부 (ax-build 중인지)
if [[ -d .claude/worktrees ]]; then
  WT=$(find .claude/worktrees -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$WT" -gt 0 ]]; then
    echo ""
    echo "⚠️  워크트리 ${WT}개 활성 — ax-build 진행 중. paperwork 중단 권고."
  fi
fi

echo ""
echo "=== 인벤토리 완료 ==="
