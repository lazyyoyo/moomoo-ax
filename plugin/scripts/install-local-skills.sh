#!/usr/bin/env bash
# team-ax 로컬 스킬 동기화.
# 정본: plugin/skills/ax-review/
# 동기화 대상:
#   1. ~/.codex/skills/ax-review/ (Codex가 $ax-review로 발견)
#   2. ~/.claude/plugins/cache/lazyyoyo/team-ax/_latest_/skills/ax-review/ (Claude 플러그인 캐시 — 캐시 존재 시에만)

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="$repo_root/skills"
codex_root="$HOME/.codex/skills"
claude_cache_base="$HOME/.claude/plugins/cache/lazyyoyo/team-ax"

# 동기화할 스킬 목록 (현재는 ax-review만 — codex 위임 대상)
skills=(
  "ax-review"
)

if [[ ! -d "$source_root" ]]; then
  echo "Missing source skills directory: $source_root" >&2
  exit 1
fi

mkdir -p "$codex_root"

for name in "${skills[@]}"; do
  src="$source_root/$name"
  if [[ ! -d "$src" ]]; then
    echo "Skipping $name — not found at $src" >&2
    continue
  fi
  mkdir -p "$codex_root/$name"
  rsync -a --delete --exclude '.DS_Store' "$src/" "$codex_root/$name/"
done

# Claude 플러그인 캐시는 존재 시에만 갱신 (설치되지 않은 환경에서는 스킵)
latest_claude_cache=""
if [[ -d "$claude_cache_base" ]]; then
  latest_claude_cache="$(find "$claude_cache_base" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -n 1 || true)"

  if [[ -n "${latest_claude_cache:-}" ]]; then
    mkdir -p "$latest_claude_cache/skills"
    for name in "${skills[@]}"; do
      src="$source_root/$name"
      [[ -d "$src" ]] || continue
      mkdir -p "$latest_claude_cache/skills/$name"
      rsync -a --delete --exclude '.DS_Store' "$src/" "$latest_claude_cache/skills/$name/"
    done
  fi
fi

echo "Installed Codex skills into: $codex_root"
if [[ -n "${latest_claude_cache:-}" ]]; then
  echo "Installed Claude plugin skills into: $latest_claude_cache/skills"
else
  echo "Claude team-ax plugin cache not found; skipped Claude install"
fi
