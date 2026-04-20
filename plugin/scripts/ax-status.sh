#!/usr/bin/env bash
# /ax-status 스킬의 실행 엔진 — install / uninstall / toggle / on / off / show.
#
# 글로벌 ~/.claude/settings.json의 statusLine.command를 team-ax 래퍼로 교체하고,
# 토글 키(.statusline.{ctx,5h,7d,branch})를 관리한다.
#
# 가드레일:
#   - settings.json 수정 전 항상 타임스탬프 백업 생성
#   - 파일 삭제는 mv ~/.Trash/ (rm 금지)
#   - 의존성(jq) 없으면 명확히 에러
#   - team-ax 미설치 상태에서 install 호출 시 안내 후 중단

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WRAPPER_TEMPLATE="$SCRIPT_DIR/templates/hud-wrapper.sh"
HUD_DIR="$HOME/.claude/hud"
WRAPPER_PATH="$HUD_DIR/ax-statusline.sh"
SETTINGS="$HOME/.claude/settings.json"
INSTALLED_JSON="$HOME/.claude/plugins/installed_plugins.json"
TRASH="$HOME/.Trash"

# ============================================================
# 헬퍼
# ============================================================

die()  { echo "❌ $*" >&2; exit 1; }
info() { echo "  $*"; }
ok()   { echo "✅ $*"; }
warn() { echo "⚠️  $*"; }

require_jq() {
  command -v jq >/dev/null 2>&1 || die "jq가 필요합니다. brew install jq"
}

backup_settings() {
  [[ -f "$SETTINGS" ]] || return 0
  local ts
  ts="$(date +%Y%m%d-%H%M%S)"
  cp "$SETTINGS" "${SETTINGS}.bak-${ts}"
  info "백업: ${SETTINGS}.bak-${ts}"
}

ensure_settings_object() {
  if [[ ! -f "$SETTINGS" ]]; then
    mkdir -p "$(dirname "$SETTINGS")"
    echo '{}' > "$SETTINGS"
  fi
}

team_ax_install_path() {
  [[ -f "$INSTALLED_JSON" ]] || return 1
  jq -r '
    .plugins
    | to_entries[]
    | select(.key | startswith("team-ax@"))
    | .value[0].installPath
  ' "$INSTALLED_JSON" 2>/dev/null | head -1
}

# ============================================================
# install
# ============================================================

cmd_install() {
  require_jq

  local install_path
  install_path="$(team_ax_install_path || true)"
  if [[ -z "$install_path" ]]; then
    die "team-ax 플러그인이 설치되어 있지 않습니다. 먼저 마켓플레이스에서 설치하세요."
  fi
  info "team-ax 설치 경로: $install_path"

  [[ -f "$WRAPPER_TEMPLATE" ]] || die "래퍼 템플릿을 찾을 수 없습니다: $WRAPPER_TEMPLATE"

  mkdir -p "$HUD_DIR"
  cp "$WRAPPER_TEMPLATE" "$WRAPPER_PATH"
  chmod +x "$WRAPPER_PATH"
  ok "래퍼 설치: $WRAPPER_PATH"

  ensure_settings_object
  backup_settings

  # 기존 statusLine 백업 + 래퍼 경로로 교체 + 토글 키 기본값 주입
  local tmp
  tmp="$(mktemp)"
  jq --arg cmd "$WRAPPER_PATH" '
    (.statusLine // null) as $existing
    | .
    | (if $existing != null and (.statusLineBackup == null) then .statusLineBackup = $existing else . end)
    | .statusLine = { type: "command", command: $cmd }
    | .statusline = (.statusline // {})
    | .statusline.ctx = (if .statusline.ctx == null then true else .statusline.ctx end)
    | .statusline["5h"] = (if .statusline["5h"] == null then true else .statusline["5h"] end)
    | .statusline["7d"] = (if .statusline["7d"] == null then true else .statusline["7d"] end)
    | .statusline.branch = (if .statusline.branch == null then true else .statusline.branch end)
  ' "$SETTINGS" > "$tmp"
  mv "$tmp" "$SETTINGS"

  ok "글로벌 statusLine 교체 완료"
  info "현재 명령: $(jq -r '.statusLine.command' "$SETTINGS")"
  cmd_show
  echo ""
  info "Claude Code를 재시작하면 새 statusline이 적용됩니다."
}

# ============================================================
# uninstall
# ============================================================

cmd_uninstall() {
  require_jq

  if [[ ! -f "$SETTINGS" ]]; then
    warn "$SETTINGS 가 없습니다. 할 일 없음."
    return 0
  fi

  backup_settings

  local has_backup
  has_backup="$(jq -r 'has("statusLineBackup")' "$SETTINGS" 2>/dev/null || echo "false")"

  local tmp
  tmp="$(mktemp)"
  if [[ "$has_backup" = "true" ]]; then
    jq '.statusLine = .statusLineBackup | del(.statusLineBackup)' "$SETTINGS" > "$tmp"
    info "기존 statusLine 백업을 복원했습니다."
  else
    jq 'del(.statusLine)' "$SETTINGS" > "$tmp"
    info "기존 statusLine이 없어서 statusLine 키를 제거했습니다."
  fi
  mv "$tmp" "$SETTINGS"

  # 래퍼 휴지통 이동 (삭제 금지)
  if [[ -e "$WRAPPER_PATH" ]]; then
    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    mv "$WRAPPER_PATH" "$TRASH/ax-statusline.sh.${ts}"
    ok "래퍼 휴지통 이동: $TRASH/ax-statusline.sh.${ts}"
  fi

  ok "uninstall 완료"
  info "토글 키(.statusline)는 유지했습니다. 재설치 시 그대로 사용됩니다."
}

# ============================================================
# toggle <key>
# ============================================================

cmd_toggle() {
  local key="${1:-}"
  case "$key" in
    ctx|5h|7d|branch) ;;
    *) die "사용법: /ax-status toggle <ctx|5h|7d|branch>" ;;
  esac

  require_jq
  ensure_settings_object
  backup_settings

  local tmp
  tmp="$(mktemp)"
  # 5h/7d는 jq에서 numeric-prefix 키라 인덱싱 형태 사용
  jq --arg k "$key" '
    .statusline = (.statusline // {})
    | (.statusline[$k] = (if .statusline[$k] == false then true else false end))
  ' "$SETTINGS" > "$tmp"
  mv "$tmp" "$SETTINGS"

  local now
  now="$(jq -r --arg k "$key" '.statusline[$k]' "$SETTINGS")"
  ok "statusline.$key = $now"
}

# ============================================================
# on / off
# ============================================================

cmd_on() {
  cat <<EOF
전역 off 해제 — 셸 환경 변수에서 CLAUDE_STATUSLINE_OFF를 제거하세요.

  unset CLAUDE_STATUSLINE_OFF

영구 적용은 ~/.zshrc 또는 ~/.bashrc에서 해당 export 라인 제거.
Claude Code 세션을 재시작해야 반영됩니다.
EOF
}

cmd_off() {
  cat <<EOF
전역 off — 셸 환경 변수 CLAUDE_STATUSLINE_OFF=1 설정.

  export CLAUDE_STATUSLINE_OFF=1

영구 적용은 ~/.zshrc 또는 ~/.bashrc에 위 라인 추가.
일시적으로는 현재 셸에서만 동작 — Claude Code 세션 재시작 시 반영.

특정 행만 끄고 싶으면 toggle 사용:
  /ax-status toggle 7d
EOF
}

# ============================================================
# show
# ============================================================

cmd_show() {
  echo ""
  echo "📊 ax-status 현재 상태"
  echo ""

  # 래퍼
  if [[ -x "$WRAPPER_PATH" ]]; then
    echo "  래퍼:    ✅ $WRAPPER_PATH"
  else
    echo "  래퍼:    ❌ 미설치 ($WRAPPER_PATH)"
  fi

  # team-ax 설치 경로
  local install_path
  install_path="$(team_ax_install_path 2>/dev/null || true)"
  if [[ -n "$install_path" && -d "$install_path" ]]; then
    echo "  team-ax: ✅ $install_path"
  else
    echo "  team-ax: ❌ 미설치"
  fi

  # 글로벌 statusLine
  if [[ -f "$SETTINGS" ]] && command -v jq >/dev/null 2>&1; then
    local cur_cmd
    cur_cmd="$(jq -r '.statusLine.command // "(none)"' "$SETTINGS")"
    echo "  설정:    $cur_cmd"
  fi

  # 토글 키
  if [[ -f "$SETTINGS" ]] && command -v jq >/dev/null 2>&1; then
    echo ""
    echo "  토글 (settings.json .statusline):"
    jq -r '
      .statusline // {} as $s
      | "    ctx    = \( if $s.ctx    == null then true else $s.ctx    end )",
        "    5h     = \( if $s["5h"] == null then true else $s["5h"] end )",
        "    7d     = \( if $s["7d"] == null then true else $s["7d"] end )",
        "    branch = \( if $s.branch == null then true else $s.branch end )"
    ' "$SETTINGS"
  fi

  # 캐시 상태
  local cache="/tmp/claude-usage-cache.json"
  echo ""
  if [[ -f "$cache" ]]; then
    local age=$(( $(date +%s) - $(stat -f %m "$cache") ))
    echo "  캐시:    ✅ $cache (${age}초 전)"
  else
    echo "  캐시:    ❌ 없음 ($cache)"
  fi

  # 전역 off
  echo ""
  if [[ "${CLAUDE_STATUSLINE_OFF:-0}" = "1" ]]; then
    echo "  전역 off: ⚠️  CLAUDE_STATUSLINE_OFF=1 — statusline 비활성화 중"
  else
    echo "  전역 off: 비활성"
  fi
}

# ============================================================
# 라우팅
# ============================================================

usage() {
  cat <<EOF
사용법: ax-status <command> [args]

명령:
  install              글로벌 settings.json statusLine을 team-ax 래퍼로 교체
  uninstall            기존 statusLine 복원 + 래퍼 휴지통 이동
  toggle <key>         특정 행 on/off (key: ctx | 5h | 7d | branch)
  on                   전역 off 해제 안내
  off                  전역 off 설정 안내
  show                 현재 설정 / 래퍼 / 캐시 / 토글 상태 출력

예:
  ax-status install
  ax-status toggle 7d
  ax-status show
EOF
}

case "${1:-show}" in
  install)   shift; cmd_install   "$@" ;;
  uninstall) shift; cmd_uninstall "$@" ;;
  toggle)    shift; cmd_toggle    "$@" ;;
  on)        shift; cmd_on        "$@" ;;
  off)       shift; cmd_off       "$@" ;;
  show)      shift; cmd_show      "$@" ;;
  -h|--help|help) usage ;;
  *) usage; exit 1 ;;
esac
