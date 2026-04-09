#!/usr/bin/env bash
#
# gate_static.sh — 정적 게이트 (MVP v0.1)
#
# 실행: bash gate_static.sh
# 결과: exit 0 (통과) / exit 1 (실패, stdout에 에러 출력)
#
# 검사 순서: eslint → tsc → build
# 하나라도 실패하면 즉시 exit 1 + 에러 출력

set -euo pipefail

ERRORS=""
FAILED=0

# ── 유틸 ──────────────────────────────────────────────

has_cmd() { command -v "$1" &>/dev/null; }

append_error() {
    local label="$1"
    local msg="$2"
    ERRORS+="[$label]"$'\n'"$msg"$'\n\n'
    FAILED=1
}

# ── ESLint ────────────────────────────────────────────

run_eslint() {
    if [ -f node_modules/.bin/eslint ]; then
        local out
        if ! out=$(npx eslint --format compact src/ 2>&1); then
            append_error "eslint" "$out"
        fi
    elif has_cmd eslint; then
        local out
        if ! out=$(eslint --format compact src/ 2>&1); then
            append_error "eslint" "$out"
        fi
    fi
}

# ── TypeScript ────────────────────────────────────────

run_tsc() {
    if [ -f tsconfig.json ]; then
        local out
        if ! out=$(npx tsc --noEmit 2>&1); then
            append_error "tsc" "$out"
        fi
    fi
}

# ── Build ─────────────────────────────────────────────

run_build() {
    if [ -f package.json ]; then
        # build 스크립트 존재 여부 확인
        if node -e "const p=require('./package.json'); process.exit(p.scripts?.build ? 0 : 1)" 2>/dev/null; then
            local out
            if ! out=$(npm run build 2>&1); then
                append_error "build" "$out"
            fi
        fi
    fi
}

# ── Prettier (검증만, 수정 안함) ─────────────────────

run_prettier() {
    if [ -f node_modules/.bin/prettier ]; then
        local out
        if ! out=$(npx prettier --check "src/**/*.{ts,tsx,js,jsx}" 2>&1); then
            append_error "prettier" "$out"
        fi
    fi
}

# ── 실행 ──────────────────────────────────────────────

run_eslint
run_tsc
run_build
run_prettier

if [ "$FAILED" -eq 1 ]; then
    echo "$ERRORS"
    exit 1
fi

exit 0
