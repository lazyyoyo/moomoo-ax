#!/usr/bin/env bash
# clean 탐지 스캔. ax-clean 1단계.
#
# 사용법: clean-scan.sh [--scope 경로]
# 프로젝트 루트에서 실행.
#
# 출력: 카테고리별 후보 목록

set -euo pipefail

SCOPE="."
if [[ "${1:-}" == "--scope" && -n "${2:-}" ]]; then
  SCOPE="$2"
fi

echo "=== clean 탐지 스캔 ==="
echo "날짜: $(date +%Y-%m-%d)"
echo "범위: $SCOPE"
echo ""

# 워크트리 활성 여부 (ax-build 중이면 중단)
if [[ -d .claude/worktrees ]]; then
  WT=$(find .claude/worktrees -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$WT" -gt 0 ]]; then
    echo "⚠️  워크트리 ${WT}개 활성 — ax-build 진행 중. 스캔 중단 권고."
    exit 1
  fi
fi

# A-3. 빈 디렉토리
echo "## A-3. 빈 디렉토리"
find "$SCOPE" -type d -empty \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './.next/*' \
  2>/dev/null | head -20 || true
echo ""

# A-4. 캐시/잔재
echo "## A-4. 캐시/잔재"
find "$SCOPE" \( -name '.DS_Store' -o -name '*.log' -o -name 'npm-debug.log*' \) \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  2>/dev/null | head -20 || true
echo ""

# B-3. 60일+ versions
echo "## B-3. 60일+ versions (archive 후보)"
if [[ -d versions ]]; then
  find versions -mindepth 1 -maxdepth 1 -type d -mtime +60 2>/dev/null || true
fi
echo ""

# B-4. 미아카이브 레퍼런스
echo "## B-4. reference/v* (archive 미이동)"
if [[ -d reference ]]; then
  find reference -mindepth 1 -maxdepth 1 -type d -name 'v*' 2>/dev/null || true
fi
echo ""

# C-1. 루트 스크린샷
echo "## C-1. 루트 스크린샷"
find . -maxdepth 1 \( -name '*.png' -o -name '*.jpg' \) 2>/dev/null || true
echo ""

# C-2. 임시 파일
echo "## C-2. 임시 파일 (.ax-*, HANDOFF.md)"
find . -maxdepth 2 \( -name '.ax-status' -o -name '.ax-brief.md' -o -name 'HANDOFF.md' \) \
  -not -path './.git/*' \
  2>/dev/null || true
echo ""

# C-3. env 백업
echo "## C-3. .env 백업"
find . -maxdepth 2 \( -name '.env.bak' -o -name '.env.old' -o -name '.env.*.backup' -o -name '.env.local.old' \) \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  2>/dev/null || true
echo ""

# C-4. 빌드 아티팩트 (git-tracked 여부 체크)
echo "## C-4. 빌드 아티팩트 (git-tracked)"
if git rev-parse --git-dir > /dev/null 2>&1; then
  for d in dist build out .next; do
    if git ls-files "$d" 2>/dev/null | head -1 | grep -q .; then
      echo "  $d/ — git-tracked (실수 커밋?)"
    fi
  done
fi
echo ""

# 용량 추정 (macOS: du -sh, 대략)
echo "## 용량 (상위 후보)"
du -sh .DS_Store 2>/dev/null || true
du -sh *.log 2>/dev/null || true
du -sh *.png 2>/dev/null | head -5 || true

echo ""
echo "=== 스캔 완료 ==="
echo ""
echo "힌트: 코드 참조 0건 기반 미사용 컴포넌트 탐지는 별도 (SKILL.md A-1 참조)"
