#!/usr/bin/env bash
# 디자인 게이트 ①② — DS 준수 린트 + 레이아웃 규칙 체크.
# ax-design 7단계 게이트 (①② 통과 후에만 ③④ 실행).
#
# 사용법: design-gate.sh <시안 디렉토리>
#   예: design-gate.sh src/app/\(mockup\)/v1.7-profile-a/
#
# 종료 코드: 0 = 통과, 1 = 미통과 (위반 항목 stdout 출력)

set -euo pipefail

TARGET_DIR="${1:?사용법: design-gate.sh <시안 디렉토리>}"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "ERROR: $TARGET_DIR 없음" >&2
  exit 1
fi

VIOLATIONS=()

# ① DS 준수 린트 — 하드코딩된 색상/간격/폰트 탐지
echo "=== 게이트 ① DS 준수 린트 ==="

# 하드코딩 색상 (#hex, rgb(), hsl() 직접 사용)
HARDCODED_COLORS=$(grep -rnE '(#[0-9a-fA-F]{3,8}|rgb\(|rgba\(|hsl\(|hsla\()' "$TARGET_DIR" --include="*.tsx" --include="*.css" --include="*.ts" 2>/dev/null | grep -v 'node_modules' | grep -v '.next' | grep -v '// ds-exception' || true)

if [[ -n "$HARDCODED_COLORS" ]]; then
  COUNT=$(echo "$HARDCODED_COLORS" | wc -l | tr -d ' ')
  VIOLATIONS+=("① 하드코딩 색상 ${COUNT}건")
  echo "FAIL: 하드코딩 색상 ${COUNT}건"
  echo "$HARDCODED_COLORS" | head -10
  echo ""
fi

# 하드코딩 간격 (인라인 px 값 — tailwind arbitrary values [16px] 등)
HARDCODED_SPACING=$(grep -rnE '\[[0-9]+(px|rem|em)\]' "$TARGET_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v 'node_modules' | grep -v '// ds-exception' || true)

if [[ -n "$HARDCODED_SPACING" ]]; then
  COUNT=$(echo "$HARDCODED_SPACING" | wc -l | tr -d ' ')
  VIOLATIONS+=("① 하드코딩 간격 ${COUNT}건")
  echo "FAIL: 하드코딩 간격 (arbitrary value) ${COUNT}건"
  echo "$HARDCODED_SPACING" | head -10
  echo ""
fi

# ② 레이아웃 규칙 — max-width, container 존재 확인
echo "=== 게이트 ② 레이아웃 규칙 ==="

# 레이아웃 파일에 max-width 또는 container 클래스 존재 확인
HAS_CONTAINER=$(grep -rlE '(max-w-|container|max-width)' "$TARGET_DIR" --include="*.tsx" 2>/dev/null || true)

if [[ -z "$HAS_CONTAINER" ]]; then
  VIOLATIONS+=("② max-width/container 미사용 — 레이아웃 제한 없음")
  echo "FAIL: max-width 또는 container 클래스 미사용"
  echo ""
fi

# 결과 출력
echo "=== 결과 ==="
if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
  echo "PASS: 게이트 ①② 통과 — ③④ 실행 가능"
  exit 0
else
  echo "FAIL: 게이트 ①② 미통과 — ${#VIOLATIONS[@]}건"
  echo "---"
  for v in "${VIOLATIONS[@]}"; do
    echo "- $v"
  done
  echo ""
  echo "③④ 게이트는 ①② 통과 후 실행."
  exit 1
fi
