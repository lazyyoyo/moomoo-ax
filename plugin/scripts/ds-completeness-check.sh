#!/usr/bin/env bash
# DS 토큰 완성도 체크. ax-design 1단계 게이트.
#
# 사용법: ds-completeness-check.sh [DESIGN_SYSTEM.md 경로]
# 기본값: ./DESIGN_SYSTEM.md
#
# 종료 코드: 0 = 통과, 1 = 미통과 (누락 항목 stdout 출력)

set -euo pipefail

DS_FILE="${1:-./DESIGN_SYSTEM.md}"

if [[ ! -f "$DS_FILE" ]]; then
  echo "FAIL: $DS_FILE 없음. DS 토큰이 아직 생성되지 않았습니다."
  echo "---"
  echo "missing: color, spacing, typography, components"
  exit 1
fi

MISSING=()

# 색상 토큰
if ! grep -qiE '(색상|color|background|foreground|semantic)' "$DS_FILE"; then
  MISSING+=("color: 색상 토큰 (배경/전경/브랜드/시맨틱)")
fi

# 공간 토큰
if ! grep -qiE '(spacing|공간|간격|gap|padding)' "$DS_FILE"; then
  MISSING+=("spacing: 공간 토큰 (spacing 스케일)")
fi

# 타이포 토큰
if ! grep -qiE '(typography|타이포|font|폰트)' "$DS_FILE"; then
  MISSING+=("typography: 타이포 토큰 (폰트/사이즈/웨이트)")
fi

# 기본 컴포넌트
for comp in "Button" "Input" "Badge" "Toast"; do
  if ! grep -qi "$comp" "$DS_FILE"; then
    MISSING+=("component: $comp 미정의")
  fi
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo "PASS: DS 토큰 체크리스트 통과"
  exit 0
else
  echo "FAIL: DS 토큰 누락 ${#MISSING[@]}건"
  echo "---"
  for item in "${MISSING[@]}"; do
    echo "- $item"
  done
  exit 1
fi
