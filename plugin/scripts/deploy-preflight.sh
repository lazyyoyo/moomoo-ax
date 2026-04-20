#!/usr/bin/env bash
# deploy 사전 확인. ax-deploy 1단계.
#
# 사용법: deploy-preflight.sh [versions/vX.Y.Z 경로]
# 기본값: versions/ 하위 최신 버전 자동 감지
#
# 종료 코드: 0 = 통과, 1 = 차단 사유 있음
#
# v0.7.0 변경 (rubato admin 도그푸딩 피드백):
# - spec 경로 자동 탐지 — `docs/specs/` 하드코딩 제거. find로 모든 `*/docs/specs` 디렉토리.
#   rubato의 `dev/docs/specs/` 같은 subdirectory 구조 인지.
# - ⏳ planned 마커 검사를 본 트랙 scope 한정 — 다른 도메인 spec 잔재 무시.
#   본 트랙 = `git diff --name-only <base>..HEAD` 결과의 spec 파일.
# - `grep -c` 결과 안전 처리 — 다중 라인/빈 결과 모두 정수로 정규화 (`[[: 0\n0` syntax error 제거).

set -euo pipefail

# ============================================================
# 인자 파싱 / 버전 디렉토리 감지
# ============================================================

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

# ============================================================
# 헬퍼
# ============================================================

# `grep -c` 결과를 항상 정수로 정규화 (다중 라인 합산, 빈 결과는 0)
safe_grep_count() {
  local pattern="$1"
  shift
  local out
  out=$(grep -c "$pattern" "$@" 2>/dev/null || true)
  # 다중 파일 결과(`file:N` 형식) → 합산. 단일 결과는 그대로.
  if [[ "$out" =~ : ]]; then
    out=$(echo "$out" | awk -F: '{s+=$2} END{print s+0}')
  fi
  # 빈 문자열 / 비숫자 → 0
  [[ -z "$out" || ! "$out" =~ ^[0-9]+$ ]] && out=0
  echo "$out"
}

# 본 트랙(현재 브랜치) 기점 base — main/master로 자동 결정. 두 브랜치 모두 없으면 빈 값.
detect_base_ref() {
  if git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    echo "origin/main"
  elif git rev-parse --verify --quiet main >/dev/null 2>&1; then
    echo "main"
  elif git rev-parse --verify --quiet origin/master >/dev/null 2>&1; then
    echo "origin/master"
  elif git rev-parse --verify --quiet master >/dev/null 2>&1; then
    echo "master"
  else
    echo ""
  fi
}

# ============================================================
# 1. ⏳ planned 마커 잔존 — 본 트랙에서 변경된 spec 파일에만 적용
# ============================================================

# spec 디렉토리 자동 탐지 (`docs/specs/` 하드코딩 제거)
# macOS 기본 bash 3.2는 `mapfile` 미지원 → while read 루프 사용
SPEC_DIRS=()
while IFS= read -r d; do
  [[ -n "$d" ]] && SPEC_DIRS+=("$d")
done < <(find . -type d -path "*/docs/specs" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null)

if [[ ${#SPEC_DIRS[@]} -eq 0 ]]; then
  FAILS+=("docs/specs 디렉토리를 찾을 수 없음 (자동 탐지 실패)")
else
  BASE_REF="$(detect_base_ref)"

  if [[ -z "$BASE_REF" ]]; then
    # 비교 기준이 없으면(초기 리포 등) 모든 spec 검사 — 기존 동작 유지
    PLANNED_FILES=()
    for d in "${SPEC_DIRS[@]}"; do
      while IFS= read -r f; do
        [[ -n "$f" ]] && PLANNED_FILES+=("$f")
      done < <(grep -rl '⏳ planned' "$d" 2>/dev/null || true)
    done
  else
    # 본 트랙 변경 파일과 spec 디렉토리 교집합에서만 마커 검사
    CHANGED_SPECS=()
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      for d in "${SPEC_DIRS[@]}"; do
        # 디렉토리 prefix 매치
        d_clean="${d#./}"
        if [[ "$f" == "$d_clean"/* ]]; then
          CHANGED_SPECS+=("$f")
          break
        fi
      done
    done < <(git diff --name-only "$BASE_REF"...HEAD 2>/dev/null || true)

    PLANNED_FILES=()
    for f in "${CHANGED_SPECS[@]}"; do
      [[ -f "$f" ]] || continue
      if grep -q '⏳ planned' "$f" 2>/dev/null; then
        PLANNED_FILES+=("$f")
      fi
    done
  fi

  if [[ ${#PLANNED_FILES[@]} -gt 0 ]]; then
    PREVIEW=$(printf '%s ' "${PLANNED_FILES[@]:0:3}")
    FAILS+=("⏳ planned 마커 잔존 ${#PLANNED_FILES[@]}건 (본 트랙 변경분): ${PREVIEW}")
  fi
fi

# ============================================================
# 2. scope.md 섹션 완성도
# ============================================================

SCOPE_FILE="${VERSION_DIR}/scope.md"
if [[ -f "$SCOPE_FILE" ]]; then
  # § 화면 정의는 v0.7부터 추가. "(없음)" 명시 허용 → 섹션 헤더만 있으면 통과.
  for section in "§ 버전 메타" "§ JTBD" "§ Story Map" "§ 화면 정의" "§ SLC 체크" "§ 비범위" "§ 수정 계획" "§ 수정 로그" "§ 리뷰"; do
    if ! grep -q "$section" "$SCOPE_FILE" 2>/dev/null; then
      FAILS+=("scope.md 누락 섹션: $section")
    fi
  done
else
  FAILS+=("scope.md 없음: $SCOPE_FILE")
fi

# ============================================================
# 3. build-plan.md 미완료 태스크 (grep -c 안전 처리)
# ============================================================

PLAN_FILE="${VERSION_DIR}/build-plan.md"
if [[ -f "$PLAN_FILE" ]]; then
  UNCHECKED=$(safe_grep_count '^\- \[ \]' "$PLAN_FILE")
  if [[ "$UNCHECKED" -gt 0 ]]; then
    FAILS+=("build-plan.md 미완료 태스크 ${UNCHECKED}건")
  fi
fi

# ============================================================
# 4. 미커밋 파일
# ============================================================

DIRTY=$(git status --porcelain 2>/dev/null | grep -v '^??' | head -5 || true)
if [[ -n "$DIRTY" ]]; then
  FAILS+=("미커밋 파일 존재: $(echo "$DIRTY" | head -3 | tr '\n' ' ')")
fi

# ============================================================
# 결과
# ============================================================

if [[ ${#FAILS[@]} -eq 0 ]]; then
  echo "PASS: deploy 사전 확인 통과"
  echo "---"
  echo "version:    $VERSION_DIR"
  echo "spec dirs:  ${SPEC_DIRS[*]:-(none)}"
  echo "base ref:   ${BASE_REF:-(none — 모든 spec 검사)}"
  exit 0
else
  echo "FAIL: deploy 차단 사유 ${#FAILS[@]}건"
  echo "---"
  for f in "${FAILS[@]}"; do
    echo "- $f"
  done
  exit 1
fi
