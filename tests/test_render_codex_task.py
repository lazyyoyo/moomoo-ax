"""plugin/skills/ax-implement/scripts/render_codex_task.py tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "skills" / "ax-implement" / "scripts"))

import render_codex_task  # noqa: E402


def test_render_executor_includes_task_fields():
    text = render_codex_task.render_executor(
        task_id="T-001",
        task_summary="Button 구현",
        relevant_files=["src/Button.tsx", "src/Button.test.tsx"],
        constraints=["토큰-only", "text hardcoding 금지"],
    )

    assert "T-001" in text
    assert "Button 구현" in text
    assert "- src/Button.tsx" in text
    assert "- 토큰-only" in text
    assert '"role": "executor"' in text


def test_render_reviewer_uses_fallback_for_empty_blocks():
    text = render_codex_task.render_reviewer(
        task_id="T-002",
        task_summary="Review Button",
        review_scope=[],
        spec_paths=[],
    )

    assert "T-002" in text
    assert "Review Button" in text
    assert "- (none)" in text
    assert '"role": "reviewer"' in text
