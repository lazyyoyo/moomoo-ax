#!/usr/bin/env bash
#
# gate_static.sh — 정적 게이트 (MVP v0.1)
#
# 사용: bash gate_static.sh <프로젝트경로> <결과JSON경로>
# 결과: exit 0 (통과) / exit 1 (실패)
#       결과 JSON: {"passed": bool, "errors": [...]}
#
# 검사 순서: tsc → eslint → build

set -uo pipefail

PROJECT_DIR="${1:-.}"
RESULT_FILE="${2:-/tmp/ax-gate-result.json}"

cd "$PROJECT_DIR"

errors=()

# ── TypeScript 타입체크 ───────────────────────────────

if [ -f tsconfig.json ]; then
    if ! tsc_out=$(npx tsc --noEmit 2>&1); then
        errors+=("typecheck: $tsc_out")
    fi
fi

# ── ESLint ────────────────────────────────────────────

if [ -f node_modules/.bin/eslint ]; then
    if ! lint_out=$(npx eslint --format compact src/ 2>&1); then
        errors+=("lint: $lint_out")
    fi
fi

# ── Build ─────────────────────────────────────────────

if [ -f package.json ]; then
    if node -e "const p=require('./package.json'); process.exit(p.scripts?.build ? 0 : 1)" 2>/dev/null; then
        if ! build_out=$(npm run build 2>&1); then
            errors+=("build: $build_out")
        fi
    fi
fi

# ── Prettier (검증만) ────────────────────────────────

if [ -f node_modules/.bin/prettier ]; then
    if ! fmt_out=$(npx prettier --check "src/**/*.{ts,tsx,js,jsx}" 2>&1); then
        errors+=("format: $fmt_out")
    fi
fi

# ── 결과 출력 ────────────────────────────────────────

if [ ${#errors[@]} -eq 0 ]; then
    echo '{"passed": true, "errors": []}' > "$RESULT_FILE"
    exit 0
else
    # 에러를 JSON 배열로 구성
    json_errors="["
    first=true
    for err in "${errors[@]}"; do
        # JSON 이스케이프: 줄바꿈, 따옴표, 백슬래시
        escaped=$(echo "$err" | head -c 2000 | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")
        if [ "$first" = true ]; then
            json_errors+="$escaped"
            first=false
        else
            json_errors+=",$escaped"
        fi
    done
    json_errors+="]"

    echo "{\"passed\": false, \"errors\": $json_errors}" > "$RESULT_FILE"
    exit 1
fi
