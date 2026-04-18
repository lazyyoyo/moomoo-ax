#!/usr/bin/env bash
# team-ax 전용 statusline.
#
# 표시: [repo] [brn] [sprint] [wt:N] [ver]
#
# 입력: Claude Code가 JSON을 stdin으로 전달
# - cwd, model 등
#
# 사용: ~/.claude/settings.json 또는 프로젝트 .claude/settings.json의
#   statusLine.command에 이 스크립트 경로를 연결.

set -eu

# stdin JSON 파싱 (cwd만 사용)
INPUT=""
if [[ ! -t 0 ]]; then
  INPUT=$(cat)
fi

CWD=$(printf '%s' "$INPUT" | python3 -c 'import sys,json; d=json.load(sys.stdin) if sys.stdin.isatty()==False else {}; print(d.get("workspace",{}).get("current_dir") or d.get("cwd") or "")' 2>/dev/null || true)
if [[ -z "$CWD" ]]; then
  CWD="$PWD"
fi

cd "$CWD" 2>/dev/null || true

# repo 이름
REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "$CWD")")

# 브랜치
BRN=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "-")

# 스프린트 — 브랜치명에서 추출하거나 docs/sprints/sprint-* 최신
SPRINT=""
if [[ "$BRN" == sprint-*/* ]]; then
  SPRINT=$(echo "$BRN" | sed 's|/.*||')
elif [[ -d docs/sprints ]]; then
  SPRINT=$(ls -d docs/sprints/sprint-* 2>/dev/null | sort -V | tail -1 | xargs basename 2>/dev/null || true)
fi

# 버전 — versions/ 최신 또는 브랜치 version/vX.Y.Z
VER=""
if [[ "$BRN" == version/v* ]]; then
  VER=$(echo "$BRN" | sed 's|version/||')
elif [[ "$BRN" == sprint-*/v* ]]; then
  VER=$(echo "$BRN" | sed 's|.*/||')
elif [[ -d versions ]]; then
  VER=$(ls -d versions/v* 2>/dev/null | sort -V | tail -1 | xargs basename 2>/dev/null || true)
fi

# 워크트리 수
WT=0
if [[ -d .claude/worktrees ]]; then
  WT=$(find .claude/worktrees -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
fi

# dirty 여부
DIRTY=""
if git rev-parse --git-dir >/dev/null 2>&1; then
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    DIRTY="*"
  fi
fi

# 출력 조립 (ANSI 색상)
C_RESET='\033[0m'
C_DIM='\033[2m'
C_BLUE='\033[34m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_MAGENTA='\033[35m'

out="${C_BLUE}📦 ${REPO}${C_RESET}"
out="${out} ${C_DIM}|${C_RESET} ${C_GREEN}${BRN}${DIRTY}${C_RESET}"
[[ -n "$SPRINT" ]] && out="${out} ${C_DIM}|${C_RESET} ${C_YELLOW}${SPRINT}${C_RESET}"
[[ -n "$VER" ]] && out="${out} ${C_DIM}|${C_RESET} ${C_MAGENTA}${VER}${C_RESET}"
[[ "$WT" -gt 0 ]] && out="${out} ${C_DIM}|${C_RESET} wt:${WT}"

printf '%b' "$out"
