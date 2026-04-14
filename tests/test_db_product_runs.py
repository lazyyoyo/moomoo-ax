"""src/db.py 의 product_runs write helper 테스트."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import db  # noqa: E402


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b""


def test_start_product_run_posts_expected_payload(monkeypatch):
    monkeypatch.setattr(db, "SUPABASE_KEY", "test-key")
    captured = {}

    def fake_urlopen(req):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data.decode())
        captured["headers"] = dict(req.header_items())
        return _FakeResponse()

    monkeypatch.setattr(db.urllib.request, "urlopen", fake_urlopen)

    ok = db.start_product_run(
        product_run_id="run-123",
        user_name="yoyo",
        project="static-nextjs-min",
        command="/team-ax:ax-implement",
        stage="ax-implement",
        fixture_id="static-nextjs-min",
        session_id="sess-1",
    )

    assert ok is True
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/rest/v1/product_runs")
    assert captured["body"]["id"] == "run-123"
    assert captured["body"]["status"] == "running"
    assert captured["body"]["project"] == "static-nextjs-min"
    assert captured["body"]["stage"] == "ax-implement"
    assert captured["body"]["fixture_id"] == "static-nextjs-min"
    assert captured["body"]["session_id"] == "sess-1"


def test_finish_product_run_patches_expected_payload(monkeypatch):
    monkeypatch.setattr(db, "SUPABASE_KEY", "test-key")
    captured = {}

    def fake_urlopen(req):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data.decode())
        return _FakeResponse()

    monkeypatch.setattr(db.urllib.request, "urlopen", fake_urlopen)

    ok = db.finish_product_run(
        product_run_id="run-123",
        status="done",
        stage="ax-implement",
        session_id="sess-2",
        duration_sec=12.5,
        cost_usd=0.42,
        num_turns=7,
        tool_call_stats={"tool_counts": {"Task": 3}},
        intervention_count=0,
    )

    assert ok is True
    assert captured["method"] == "PATCH"
    assert captured["url"].endswith("/rest/v1/product_runs?id=eq.run-123")
    assert captured["body"]["status"] == "done"
    assert captured["body"]["stage"] == "ax-implement"
    assert captured["body"]["session_id"] == "sess-2"
    assert captured["body"]["duration_sec"] == 12.5
    assert captured["body"]["cost_usd"] == 0.42
    assert captured["body"]["num_turns"] == 7
    assert captured["body"]["tool_call_stats"] == {"tool_counts": {"Task": 3}}
    assert captured["body"]["intervention_count"] == 0
