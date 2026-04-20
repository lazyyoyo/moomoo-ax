#!/usr/bin/env bash
# team-ax 전용 statusline v2.
#
# 표시:
#   Line 1 (항상): 📦 repo | brn* | sprint | ver | wt:N
#   Line 2 (CTX): CTX [▰▰▱▱…]  PCT%  used_k/total_k
#   Line 3 (5H):  5H  [▰▱▱▱…]  PCT%  ↻ Xh
#   Line 4 (7D):  7D  [▰▱▱▱…]  PCT%  ↻ Yd
#
# 토글 (settings.json):
#   .statusline.ctx / .5h / .7d / .branch    — 각 행 on/off (기본 true)
#
# 전역 off:
#   CLAUDE_STATUSLINE_OFF=1
#
# 입력: Claude Code가 JSON을 stdin으로 전달
#   .workspace.current_dir / .cwd
#   .context_window.used_percentage / .context_window.context_window_size
#
# 의존: jq, python3 (선택), curl (선택, fetch-usage.sh용)

[ "${CLAUDE_STATUSLINE_OFF:-0}" = "1" ] && exit 0

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ============================================================
# 입력 파싱
# ============================================================

INPUT=""
if [[ ! -t 0 ]]; then
  INPUT=$(cat)
fi

# CWD 추출
CWD=$(printf '%s' "$INPUT" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get("workspace", {}).get("current_dir") or d.get("cwd") or "")
except Exception:
    pass
' 2>/dev/null || true)
[[ -z "$CWD" ]] && CWD="$PWD"
cd "$CWD" 2>/dev/null || true

# context_window 파싱
PCT=0
CTX_SIZE=200000
if [[ -n "$INPUT" ]] && command -v jq >/dev/null 2>&1; then
  _PCT=$(printf '%s' "$INPUT" | jq -r '.context_window.used_percentage // 0' 2>/dev/null | cut -d. -f1)
  _SIZE=$(printf '%s' "$INPUT" | jq -r '.context_window.context_window_size // 200000' 2>/dev/null)
  [[ "$_PCT" =~ ^[0-9]+$ ]] && PCT="$_PCT"
  [[ "$_SIZE" =~ ^[0-9]+$ ]] && CTX_SIZE="$_SIZE"
fi

USED_K=$(awk "BEGIN{printf \"%.0f\", ($PCT * $CTX_SIZE / 100) / 1000}")
TOTAL_K=$(awk "BEGIN{printf \"%.0f\", $CTX_SIZE / 1000}")

# ============================================================
# 토글 키 읽기 (~/.claude/settings.json)
# ============================================================

SL_CTX=true
SL_5H=true
SL_7D=true
SL_BRANCH=true

GLOBAL_SETTINGS="$HOME/.claude/settings.json"
if [[ -f "$GLOBAL_SETTINGS" ]] && command -v jq >/dev/null 2>&1; then
  read -r SL_CTX SL_5H SL_7D SL_BRANCH <<<"$(jq -r '
    [
      (if .statusline.ctx == null then true else .statusline.ctx end),
      (if .statusline["5h"] == null then true else .statusline["5h"] end),
      (if .statusline["7d"] == null then true else .statusline["7d"] end),
      (if .statusline.branch == null then true else .statusline.branch end)
    ] | join(" ")
  ' "$GLOBAL_SETTINGS" 2>/dev/null || echo "true true true true")"
fi

# ============================================================
# repo / branch / sprint / ver / worktree (v1 유지)
# ============================================================

REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "$CWD")")
BRN=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "-")

SPRINT=""
if [[ "$BRN" == sprint-*/* ]]; then
  SPRINT=$(echo "$BRN" | sed 's|/.*||')
elif [[ -d docs/sprints ]]; then
  SPRINT=$(ls -d docs/sprints/sprint-* 2>/dev/null | sort -V | tail -1 | xargs basename 2>/dev/null || true)
fi

VER=""
if [[ "$BRN" == version/v* ]]; then
  VER=$(echo "$BRN" | sed 's|version/||')
elif [[ "$BRN" == sprint-*/v* ]]; then
  VER=$(echo "$BRN" | sed 's|.*/||')
elif [[ -d versions ]]; then
  VER=$(ls -d versions/v* 2>/dev/null | sort -V | tail -1 | xargs basename 2>/dev/null || true)
fi

WT=0
if [[ -d .claude/worktrees ]]; then
  WT=$(find .claude/worktrees -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
fi

DIRTY=""
if git rev-parse --git-dir >/dev/null 2>&1; then
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    DIRTY="*"
  fi
fi

# ============================================================
# 반응형 레이아웃
# ============================================================

W="${COLUMNS:-$(tput cols 2>/dev/null || echo 80)}"
if [[ "$W" -ge 60 ]]; then
  MODE=L; BAR_W=15
elif [[ "$W" -ge 40 ]]; then
  MODE=M; BAR_W=10
else
  MODE=S; BAR_W=5
fi

# ============================================================
# quota 캐시 (5H/7D)
# ============================================================

# 백그라운드 fire-and-forget — 캐시 갱신
[[ -x "$SCRIPT_DIR/fetch-usage.sh" ]] && "$SCRIPT_DIR/fetch-usage.sh" >/dev/null 2>&1 &

CACHE="/tmp/claude-usage-cache.json"
H5=""; D7=""; RESET_5H=""; RESET_7D=""
if [[ -f "$CACHE" ]] && command -v jq >/dev/null 2>&1; then
  _H5_RAW=$(jq -r '.five_hour.utilization // empty' "$CACHE" 2>/dev/null | cut -d. -f1)
  _D7_RAW=$(jq -r '.seven_day.utilization // empty' "$CACHE" 2>/dev/null | cut -d. -f1)
  [[ "$_H5_RAW" =~ ^[0-9]+$ ]] && H5="$_H5_RAW"
  [[ "$_D7_RAW" =~ ^[0-9]+$ ]] && D7="$_D7_RAW"
  RESET_5H=$(jq -r '.five_hour.resets_at // empty' "$CACHE" 2>/dev/null)
  RESET_7D=$(jq -r '.seven_day.resets_at // empty' "$CACHE" 2>/dev/null)
fi

# ============================================================
# 헬퍼
# ============================================================

# 색상
C_RESET='\033[0m'
C_DIM='\033[2m'
C_BOLD='\033[1m'
C_RED='\033[31m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_BLUE='\033[34m'
C_MAGENTA='\033[35m'
C_CYAN='\033[36m'

# 임계치 색상
threshold_color() {
  local pct=$1 base_color=$2
  if [[ "$pct" -ge 80 ]] 2>/dev/null; then echo "$C_RED"
  elif [[ "$pct" -ge 50 ]] 2>/dev/null; then echo "$C_YELLOW"
  else echo "$base_color"; fi
}

# 바 렌더 (filled▰ / empty▱)
make_bar() {
  local pct=$1 color=$2 width=${3:-15}
  local f=$(( pct * width / 100 ))
  [[ "$f" -gt "$width" ]] && f="$width"
  [[ "$f" -lt 0 ]] && f=0
  local e=$(( width - f ))
  printf '%b' "${color}$(printf "%${f}s" | tr ' ' '▰')${C_DIM}$(printf "%${e}s" | tr ' ' '▱')${C_RESET}"
}

# stale 체크 (resets_at 과거)
is_stale() {
  local reset_at="$1"
  [[ -z "$reset_at" ]] && return 1
  local ts
  ts=$(date -juf "%Y-%m-%dT%H:%M:%S" "${reset_at%%.*}" "+%s" 2>/dev/null) || return 1
  [[ -z "$ts" ]] && return 1
  [[ "$ts" -le "$(date +%s)" ]]
}

# 남은 시간 표기
time_remaining() {
  local reset_at="$1"
  [[ -z "$reset_at" ]] && return
  local ts
  ts=$(date -juf "%Y-%m-%dT%H:%M:%S" "${reset_at%%.*}" "+%s" 2>/dev/null) || return
  local diff=$(( ts - $(date +%s) ))
  [[ "$diff" -le 0 ]] && echo "now" && return
  local d=$((diff / 86400)) h=$(((diff % 86400) / 3600)) m=$(((diff % 3600) / 60))
  if [[ "$d" -gt 0 ]]; then echo "${d}d${h}h"
  elif [[ "$h" -gt 0 ]]; then echo "${h}h${m}m"
  else echo "${m}m"; fi
}

# chart 행: label(3) bar pct% [suffix only L]
chart_row() {
  local label="$1" pct="$2" color="$3" label_color="$4" suffix="$5"
  local lbl
  lbl=$(printf '%-3s' "$label")
  local num
  num=$(printf '%3s' "$pct")
  printf '%b' "${C_BOLD}${label_color}${lbl}${C_RESET} "
  make_bar "$pct" "$color" "$BAR_W"
  printf '%b' " ${color}${num}%${C_RESET}"
  [[ "$MODE" = "L" && -n "$suffix" ]] && printf '%b' "  ${C_DIM}${suffix}${C_RESET}"
  printf '\n'
}

# ============================================================
# 출력
# ============================================================

# Line 1 — 헤더 (branch 토글에 따라 일부 생략)
out="${C_BLUE}📦 ${REPO}${C_RESET}"
if [[ "$SL_BRANCH" != "false" ]]; then
  out="${out} ${C_DIM}|${C_RESET} ${C_GREEN}${BRN}${DIRTY}${C_RESET}"
  [[ -n "$SPRINT" ]] && out="${out} ${C_DIM}|${C_RESET} ${C_YELLOW}${SPRINT}${C_RESET}"
  [[ -n "$VER" ]] && out="${out} ${C_DIM}|${C_RESET} ${C_MAGENTA}${VER}${C_RESET}"
  [[ "$WT" -gt 0 ]] && out="${out} ${C_DIM}|${C_RESET} wt:${WT}"
fi
printf '%b\n' "$out"

# Line 2 — CTX
if [[ "$SL_CTX" != "false" ]]; then
  CTX_COLOR=$(threshold_color "$PCT" "$C_CYAN")
  CTX_SUFFIX="${USED_K}k/${TOTAL_K}k"
  chart_row "CTX" "$PCT" "$CTX_COLOR" "$C_CYAN" "$CTX_SUFFIX"
fi

# Line 3 — 5H
if [[ "$SL_5H" != "false" && -n "$H5" ]]; then
  if is_stale "$RESET_5H"; then
    printf '%b\n' "${C_BOLD}${C_GREEN}5H ${C_RESET} ${C_YELLOW}⚠ stale${C_RESET}"
  else
    H5_COLOR=$(threshold_color "$H5" "$C_GREEN")
    R5=$(time_remaining "$RESET_5H")
    chart_row "5H" "$H5" "$H5_COLOR" "$C_GREEN" "${R5:+↻ ${R5}}"
  fi
fi

# Line 4 — 7D
if [[ "$SL_7D" != "false" && -n "$D7" ]]; then
  if is_stale "$RESET_7D"; then
    printf '%b\n' "${C_BOLD}${C_BLUE}7D ${C_RESET} ${C_YELLOW}⚠ stale${C_RESET}"
  else
    D7_COLOR=$(threshold_color "$D7" "$C_BLUE")
    R7=$(time_remaining "$RESET_7D")
    chart_row "7D" "$D7" "$D7_COLOR" "$C_BLUE" "${R7:+↻ ${R7}}"
  fi
fi

exit 0
