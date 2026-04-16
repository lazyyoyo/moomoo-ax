#!/usr/bin/env bash
# Phase B 부트스트랩: Phase A 산출물 커밋 → 폴더 승격 → version branch → Story별 worktree 생성.
#
# 사용법: phase-b-setup.sh <version>
#   예: phase-b-setup.sh v1.7.0
#
# 전제: versions/undefined/scope.md 가 존재하고, §Story Map에 "### Story N:" 패턴이 있어야 함.

set -euo pipefail

VERSION="${1:?사용법: phase-b-setup.sh <version> (예: v1.7.0)}"
VERSION_DIR="versions/${VERSION}"
SCOPE_FILE="versions/undefined/scope.md"
WORKTREE_BASE=".claude/worktrees"

if [[ ! -f "$SCOPE_FILE" ]]; then
  echo "ERROR: $SCOPE_FILE 없음. Phase A가 완료되지 않았습니다." >&2
  exit 1
fi

# 1. Phase A 산출물 커밋
git add versions/undefined/
git commit -m "Phase A 완료 — ${VERSION} scope 확정" || echo "Phase A 산출물 이미 커밋됨"

# 2. 폴더 승격: versions/undefined/ → versions/vX.Y.Z/
if [[ -d "$VERSION_DIR" ]]; then
  echo "ERROR: $VERSION_DIR 이미 존재합니다." >&2
  exit 1
fi

mv "versions/undefined" "$VERSION_DIR"
git add "versions/"
git commit -m "Phase B — ${VERSION} 폴더 승격"

# 3. version branch 생성
BRANCH_NAME="version/${VERSION}"
git checkout -b "$BRANCH_NAME"
echo "version branch 생성: $BRANCH_NAME"

# 4. Story별 worktree 생성
STORIES=$(grep -E '^### Story [0-9]+:' "$VERSION_DIR/scope.md" | sed 's/^### Story \([0-9]*\):.*/\1/')

if [[ -z "$STORIES" ]]; then
  echo "WARNING: Story가 없습니다. worktree를 생성하지 않습니다." >&2
  echo "---"
  echo "version_dir: $VERSION_DIR"
  echo "branch: $BRANCH_NAME"
  echo "worktrees: 0"
  exit 0
fi

mkdir -p "$WORKTREE_BASE"

WORKTREE_COUNT=0
WORKTREE_PATHS=""

for STORY_NUM in $STORIES; do
  WT_NAME="story-${STORY_NUM}"
  WT_PATH="${WORKTREE_BASE}/${WT_NAME}"
  WT_BRANCH="${BRANCH_NAME}/story-${STORY_NUM}"

  if [[ -d "$WT_PATH" ]]; then
    echo "SKIP: $WT_PATH 이미 존재" >&2
    continue
  fi

  git worktree add "$WT_PATH" -b "$WT_BRANCH" "$BRANCH_NAME"
  WORKTREE_COUNT=$((WORKTREE_COUNT + 1))
  WORKTREE_PATHS="${WORKTREE_PATHS}${WT_PATH}\n"
  echo "worktree 생성: $WT_PATH ($WT_BRANCH)"
done

echo "---"
echo "version_dir: $VERSION_DIR"
echo "branch: $BRANCH_NAME"
echo "worktrees: $WORKTREE_COUNT"
echo -e "$WORKTREE_PATHS"
