"""plugin/skills/ax-implement/scripts/select_codex_model.py tests."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin" / "skills" / "ax-implement" / "scripts"))

import select_codex_model  # noqa: E402


def test_stage_final_review_uses_strong_model():
    payload = select_codex_model.select_model(
        role="reviewer",
        task_id="stage-final-review",
        task_summary="전체 stage 최종 검토",
        files=["plan.md"],
    )

    assert payload["tier"] == "final-review"
    assert payload["model"] == select_codex_model.FINAL_REVIEW_MODEL
    assert payload["risk"] == "high"


def test_low_risk_executor_uses_fast_model():
    payload = select_codex_model.select_model(
        role="executor",
        task_id="T-003",
        task_summary="홈 page wiring 및 copy 연결",
        files=[],
    )

    assert payload["tier"] == "fast"
    assert payload["model"] == select_codex_model.FAST_MODEL
    assert payload["risk"] == "low"


def test_high_risk_reviewer_uses_strong_model_for_shared_component():
    payload = select_codex_model.select_model(
        role="reviewer",
        task_id="T-001",
        task_summary="Button 컴포넌트 검토",
        files=["src/components/Button.tsx", "src/components/Button.test.tsx"],
    )

    assert payload["tier"] == "strong"
    assert payload["model"] == select_codex_model.STRONG_MODEL
    assert payload["risk"] == "high"


def test_ambiguous_executor_defaults_to_strong_model():
    payload = select_codex_model.select_model(
        role="executor",
        task_id="T-099",
        task_summary="misc update",
        files=["src/feature/widget.ts"],
    )

    assert payload["tier"] == "strong"
    assert payload["model"] == select_codex_model.STRONG_MODEL
    assert payload["risk"] == "ambiguous"
