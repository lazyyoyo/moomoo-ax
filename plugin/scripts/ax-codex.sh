#!/usr/bin/env bash
# /ax-codex 스킬의 실행 엔진 — install / uninstall / status.
#
# team-ax 플러그인 중 codex 위임 대상(ax-review, ax-execute)을
# ~/.codex/skills/로 동기화한다. ax-status와 같은 패턴.
#
# 가드레일:
#   - 파일 삭제는 mv ~/.Trash/ (rm 금지)
#   - rsync 옵션 고정: -a --delete --exclude '.DS_Store'
#   - 대상 스킬 목록 고정 (확장 시 SKILL.md와 함께 수정)
#   - 구버전 ~/.codex/skills/execute/(rename 이전)가 있으면 휴지통 이동

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_ROOT="$REPO_ROOT/skills"
CODEX_ROOT="$HOME/.codex/skills"
CLAUDE_CACHE_BASE="$HOME/.claude/plugins/cache/lazyyoyo/team-ax"
TRASH="$HOME/.Trash"

# codex 위임 대상 스킬 목록 (SKILL.md와 일치 유지)
SKILLS=("ax-review" "ax-execute")

# rename 이전 이름 — install 시 정리
LEGACY_SKILLS=("execute")

# ============================================================
# 헬퍼
# ============================================================

die()  { echo "❌ $*" >&2; exit 1; }
info() { echo "  $*"; }
ok()   { echo "✅ $*"; }
warn() { echo "⚠️  $*"; }

timestamp() { date +%Y%m%d-%H%M%S; }

require_rsync() {
  command -v rsync >/dev/null 2>&1 || die "rsync가 필요합니다."
}

latest_claude_cache() {
  [[ -d "$CLAUDE_CACHE_BASE" ]] || return 1
  find "$CLAUDE_CACHE_BASE" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -n 1
}

move_to_trash() {
  local target="$1"
  [[ -e "$target" ]] || return 0
  mkdir -p "$TRASH"
  local base
  base="$(basename "$target")"
  local dest="$TRASH/${base}.$(timestamp)"
  mv "$target" "$dest"
  info "휴지통 이동: $target → $dest"
}

sync_one() {
  local name="$1" dest_root="$2"
  local src="$SOURCE_ROOT/$name"
  if [[ ! -d "$src" ]]; then
    warn "source 없음: $src — skip"
    return 0
  fi
  mkdir -p "$dest_root/$name"
  rsync -a --delete --exclude '.DS_Store' "$src/" "$dest_root/$name/"
  info "synced: $dest_root/$name"
}

# ============================================================
# 서브커맨드
# ============================================================

cmd_install() {
  require_rsync
  [[ -d "$SOURCE_ROOT" ]] || die "source skills 없음: $SOURCE_ROOT"

  echo "▶ /ax-codex install"
  mkdir -p "$CODEX_ROOT"

  # 정본 → codex
  for name in "${SKILLS[@]}"; do
    sync_one "$name" "$CODEX_ROOT"
  done

  # 구버전 정리
  for legacy in "${LEGACY_SKILLS[@]}"; do
    if [[ -d "$CODEX_ROOT/$legacy" ]]; then
      move_to_trash "$CODEX_ROOT/$legacy"
    fi
  done

  # Claude 플러그인 캐시 (있을 때만)
  local cache
  if cache="$(latest_claude_cache)" && [[ -n "$cache" ]]; then
    mkdir -p "$cache/skills"
    for name in "${SKILLS[@]}"; do
      sync_one "$name" "$cache/skills"
    done
    ok "Claude 플러그인 캐시 동기화: $cache/skills"
  else
    info "Claude 플러그인 캐시 없음 — skip"
  fi

  ok "codex 동기화 완료: $CODEX_ROOT"
}

cmd_uninstall() {
  echo "▶ /ax-codex uninstall"
  for name in "${SKILLS[@]}"; do
    if [[ -d "$CODEX_ROOT/$name" ]]; then
      move_to_trash "$CODEX_ROOT/$name"
    else
      info "없음 skip: $CODEX_ROOT/$name"
    fi
  done

  # 혹시 남아있을 구버전도 정리
  for legacy in "${LEGACY_SKILLS[@]}"; do
    if [[ -d "$CODEX_ROOT/$legacy" ]]; then
      move_to_trash "$CODEX_ROOT/$legacy"
    fi
  done

  ok "uninstall 완료"
}

status_one() {
  local name="$1"
  local src="$SOURCE_ROOT/$name"
  local dst="$CODEX_ROOT/$name"
  if [[ ! -d "$dst" ]]; then
    echo "  $name: ✗ missing"
    return
  fi
  if [[ ! -d "$src" ]]; then
    echo "  $name: ⚠  source 없음 (정본 제거됨?)"
    return
  fi
  if diff -rq --exclude '.DS_Store' "$src" "$dst" >/dev/null 2>&1; then
    echo "  $name: ✓ synced"
  else
    echo "  $name: ⚠  stale (source와 다름 — /ax-codex install 필요)"
  fi
}

cmd_status() {
  echo "▶ /ax-codex status"
  echo ""
  if command -v codex >/dev/null 2>&1; then
    echo "codex CLI: ✓ $(command -v codex)"
  else
    echo "codex CLI: ✗ 미설치"
  fi
  echo ""
  echo "대상 스킬 ($CODEX_ROOT):"
  for name in "${SKILLS[@]}"; do
    status_one "$name"
  done
  echo ""
  echo "구버전 잔재:"
  local found=0
  for legacy in "${LEGACY_SKILLS[@]}"; do
    if [[ -d "$CODEX_ROOT/$legacy" ]]; then
      echo "  $legacy: ⚠  $CODEX_ROOT/$legacy 존재 — /ax-codex install로 정리"
      found=1
    fi
  done
  [[ "$found" -eq 0 ]] && echo "  (없음)"
  echo ""
  local cache
  if cache="$(latest_claude_cache)" && [[ -n "$cache" ]]; then
    echo "Claude 플러그인 캐시: $cache"
    for name in "${SKILLS[@]}"; do
      local dst="$cache/skills/$name"
      if [[ -d "$dst" ]]; then
        echo "  $name: ✓ present"
      else
        echo "  $name: ✗ missing"
      fi
    done
  else
    echo "Claude 플러그인 캐시: (없음)"
  fi
}

# ============================================================
# 엔트리포인트
# ============================================================

main() {
  local sub="${1:-status}"
  case "$sub" in
    install)   cmd_install ;;
    uninstall) cmd_uninstall ;;
    status|"") cmd_status ;;
    -h|--help|help)
      cat <<EOF
사용법: bash ax-codex.sh <subcommand>

서브커맨드:
  install     ~/.codex/skills/로 ax-review + ax-execute 동기화 + 구버전 정리
  uninstall   ~/.codex/skills/ 대상 스킬 휴지통 이동
  status      현재 동기화 상태 확인 (기본)
EOF
      ;;
    *) die "알 수 없는 서브커맨드: $sub (install/uninstall/status)" ;;
  esac
}

main "$@"
