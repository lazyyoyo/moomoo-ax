#!/usr/bin/env bash
# install_ax_diff_hook.sh — 대상 프로젝트에 ax-diff post-commit hook 설치
#
# 사용:
#   scripts/install_ax_diff_hook.sh <target_project_root>
#
# 동작:
# - <target>/.git/hooks/post-commit 에 ax-diff 블록 append (이미 있으면 skip)
# - 기존 post-commit 과 공존 (하단 append + marker 로 구분)
# - moomoo-ax 경로는 이 스크립트의 위치에서 자동 해석

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <target_project_root>" >&2
    exit 1
fi

TARGET="$(cd "$1" && pwd)"
if [[ ! -d "$TARGET/.git" ]]; then
    echo "ERROR: $TARGET 는 git 저장소가 아님 (.git 없음)" >&2
    exit 1
fi

# moomoo-ax 루트 = 이 스크립트 parent 의 parent
MOOMOO_AX_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$MOOMOO_AX_ROOT/.venv/bin/python"
HOOK_SCRIPT="$MOOMOO_AX_ROOT/scripts/ax_post_commit.py"

if [[ ! -x "$PY" ]]; then
    echo "ERROR: $PY 실행 불가. moomoo-ax venv 확인 필요" >&2
    exit 1
fi
if [[ ! -f "$HOOK_SCRIPT" ]]; then
    echo "ERROR: $HOOK_SCRIPT 없음" >&2
    exit 1
fi

POST_COMMIT="$TARGET/.git/hooks/post-commit"
MARKER_BEGIN="# >>> moomoo-ax ax-diff hook >>>"
MARKER_END="# <<< moomoo-ax ax-diff hook <<<"

GITIGNORE="$TARGET/.gitignore"
GITIGNORE_MARKER="# moomoo-ax ax-diff hook artifacts"

# .gitignore 에 ax 추적 파일 제외 항목 보장
ensure_gitignore() {
    if [[ -f "$GITIGNORE" ]] && grep -q "$GITIGNORE_MARKER" "$GITIGNORE"; then
        return 0
    fi
    # 마커 없으면 append
    {
        [[ -f "$GITIGNORE" ]] && echo ""
        echo "$GITIGNORE_MARKER"
        echo ".ax-generated.jsonl"
        echo ".ax-artifacts/"
    } >> "$GITIGNORE"
    echo "[install] $GITIGNORE 에 ax 추적 파일 제외 항목 추가"
}

ensure_gitignore

# idempotent 체크
if [[ -f "$POST_COMMIT" ]] && grep -q "$MARKER_BEGIN" "$POST_COMMIT"; then
    echo "[install] $POST_COMMIT 에 ax-diff hook 이미 설치됨 — skip"
    exit 0
fi

# 기존 파일이 없으면 shebang 먼저
if [[ ! -f "$POST_COMMIT" ]]; then
    cat > "$POST_COMMIT" <<'SHEBANG'
#!/usr/bin/env bash
SHEBANG
fi

# 블록 append
cat >> "$POST_COMMIT" <<EOF

$MARKER_BEGIN
# moomoo-ax 자동 diff 수집. 이 블록을 삭제하면 비활성화.
"$PY" "$HOOK_SCRIPT" "$TARGET" || true
$MARKER_END
EOF

chmod +x "$POST_COMMIT"

echo "[install] $POST_COMMIT 에 ax-diff hook 설치 완료"
echo "[install]   python  : $PY"
echo "[install]   script  : $HOOK_SCRIPT"
echo "[install]   target  : $TARGET"
