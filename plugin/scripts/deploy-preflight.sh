#!/usr/bin/env bash
# deploy 사전 확인. ax-deploy 1단계.
#
# 사용법: deploy-preflight.sh [versions/vX.Y.Z 경로]
# 기본값: versions/ 하위 최신 버전 자동 감지
#
# 종료 코드: 0 = 통과, 1 = 차단 사유 있음

set -euo pipefail

# 버전 디렉토리 감지
if [[ -n "${1:-}" ]]; then
  VERSION_DIR="$1"
else
  VERSION_DIR=$(ls -d versions/v* 2>/dev/null | sort -V | tail -1 || true)
fi

if [[ -z "$VERSION_DIR" || ! -d "$VERSION_DIR" ]]; then
  echo "FAIL: 버전 디렉토리 없음. ax-define이 완료되지 않았습니다."
  exit 1
fi

FAILS=()

# 1. ⏳ planned 마커 잔존
PLANNED=$(grep -rl '⏳ planned' docs/specs/ 2>/dev/null || true)
if [[ -n "$PLANNED" ]]; then
  COUNT=$(echo "$PLANNED" | wc -l | tr -d ' ')
  FAILS+=("⏳ planned 마커 잔존 ${COUNT}건: $(echo "$PLANNED" | head -3 | tr '\n' ' ')")
fi

# 2. scope.md 섹션 완성도
SCOPE_FILE="${VERSION_DIR}/scope.md"
if [[ -f "$SCOPE_FILE" ]]; then
  for section in "§ 버전 메타" "§ JTBD" "§ Story Map" "§ SLC 체크" "§ 비범위" "§ 수정 계획" "§ 수정 로그" "§ 리뷰"; do
    if ! grep -q "$section" "$SCOPE_FILE" 2>/dev/null; then
      FAILS+=("scope.md 누락 섹션: $section")
    fi
  done
else
  FAILS+=("scope.md 없음: $SCOPE_FILE")
fi

# 3. build-plan.md 미완료 태스크
PLAN_FILE="${VERSION_DIR}/build-plan.md"
if [[ -f "$PLAN_FILE" ]]; then
  UNCHECKED=$(grep -c '^\- \[ \]' "$PLAN_FILE" 2>/dev/null || echo "0")
  if [[ "$UNCHECKED" -gt 0 ]]; then
    FAILS+=("build-plan.md 미완료 태스크 ${UNCHECKED}건")
  fi
fi

# 4. 미커밋 파일
DIRTY=$(git status --porcelain 2>/dev/null | grep -v '^\?\?' | head -5 || true)
if [[ -n "$DIRTY" ]]; then
  FAILS+=("미커밋 파일 존재: $(echo "$DIRTY" | head -3 | tr '\n' ' ')")
fi

# 결과
if [[ ${#FAILS[@]} -eq 0 ]]; then
  echo "PASS: deploy 사전 확인 통과"
  echo "---"
  echo "version: $VERSION_DIR"
  exit 0
else
  echo "FAIL: deploy 차단 사유 ${#FAILS[@]}건"
  echo "---"
  for f in "${FAILS[@]}"; do
    echo "- $f"
  done
  exit 1
fi
