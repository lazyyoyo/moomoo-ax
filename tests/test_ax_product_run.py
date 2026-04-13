"""scripts/ax_product_run.py 드라이버 흐름 검증 (mock 기반).

실 claude CLI 는 호출하지 않음. claude.call 을 patch 해서 다음을 확인:
- allowed_tools 에 plugin_dir 절대경로 기반 Bash 패턴 포함
- cwd 가 run_dir (임시 경로) 로 전달
- stdout_path 가 .harness/runs/<run_id>.ndjson 에 기록
- cleanup (run_dir 삭제) 이 try/finally 로 실행됨
- fixture 원본에 .git 이 생성되지 않음 (copytree 격리)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ax_product_run  # noqa: E402


def _make_fixture(tmp_path: Path) -> Path:
    """테스트용 plain 디렉토리 fixture 생성 (git repo 아님)."""
    fixture = tmp_path / "fx"
    fixture.mkdir()
    (fixture / "package.json").write_text('{"name":"fx","scripts":{}}', encoding="utf-8")
    (fixture / "versions").mkdir()
    (fixture / "versions" / "plan.md").write_text("- [ ] T-001 dummy\n", encoding="utf-8")
    return fixture


def _mock_claude_call_success(**kwargs):
    """claude.call 성공 응답 + stdout_path 있으면 파일에 sample ndjson 기록."""
    stdout_path = kwargs.get("stdout_path")
    if stdout_path:
        Path(stdout_path).write_text('{"type":"result","subtype":"success"}\n',
                                     encoding="utf-8")
    return {
        "success": True,
        "output": "done",
        "tokens": {"input_tokens": 0, "output_tokens": 0,
                   "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
        "cost_usd": 0.01,
        "duration_sec": 1.0,
        "tool_events": [],
        "num_turns": 2,
        "session_id": "test-sess",
        "error": None,
    }


def test_build_allowed_tools_uses_absolute_plugin_path(tmp_path):
    plugin_dir = tmp_path / "plug"
    tools = ax_product_run.build_allowed_tools(plugin_dir)
    scripts_abs = str(plugin_dir / "skills" / "ax-implement" / "scripts") + "/*"

    assert f"Bash(bash {scripts_abs})" in tools
    assert f"Bash({scripts_abs})" in tools
    assert f"Bash(python3 {scripts_abs})" in tools
    # env 변수 치환형 패턴이 빠져있어야 함 (permission rule 이 치환 안 함)
    assert not any("${CLAUDE_SKILL_DIR}" in t for t in tools)
    # 기본 BASE 패턴은 그대로 유지
    assert "Bash(git:*)" in tools
    assert "Read" in tools


def test_driver_passes_cwd_and_stdout_path(tmp_path, monkeypatch):
    """드라이버가 claude.call 에 cwd=run_dir, stdout_path=ndjson 전달하는지."""
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    captured = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return _mock_claude_call_success(**kwargs)

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
    ])
    with patch.object(ax_product_run.claude, "call", side_effect=fake_call):
        rc = ax_product_run.main()

    assert rc == 0
    assert captured["plugin_dir"] == plugin_dir.resolve()
    assert captured["cwd"] is not None
    cwd = Path(captured["cwd"])
    assert cwd.name.startswith("ax-run-")
    assert cwd.parent == Path(tempfile.gettempdir())
    assert captured["stdout_path"].parent == log_dir
    assert captured["stdout_path"].suffix == ".ndjson"
    # cwd 이름의 hash 부분과 ndjson 파일명이 같은 run_id
    assert captured["stdout_path"].stem == cwd.name.replace("ax-run-", "")


def test_driver_cleans_up_run_dir_on_success(tmp_path, monkeypatch):
    """성공 시 run_dir 이 shutil.rmtree 로 제거됨."""
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    captured_cwd: list[Path] = []

    def fake_call(**kwargs):
        captured_cwd.append(Path(kwargs["cwd"]))
        assert captured_cwd[-1].exists(), "run_dir must exist during call"
        return _mock_claude_call_success(**kwargs)

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
    ])
    with patch.object(ax_product_run.claude, "call", side_effect=fake_call):
        ax_product_run.main()

    assert captured_cwd
    assert not captured_cwd[0].exists(), "run_dir must be removed after cleanup"


def test_driver_cleans_up_on_exception(tmp_path, monkeypatch):
    """claude.call 이 예외 던져도 finally 로 run_dir 제거."""
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    captured_cwd: list[Path] = []

    def fake_call(**kwargs):
        captured_cwd.append(Path(kwargs["cwd"]))
        raise RuntimeError("boom")

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
    ])
    with patch.object(ax_product_run.claude, "call", side_effect=fake_call):
        try:
            ax_product_run.main()
        except RuntimeError:
            pass

    assert captured_cwd
    assert not captured_cwd[0].exists(), "run_dir must be removed even on exception"


def test_driver_keep_flag_preserves_run_dir(tmp_path, monkeypatch):
    """--keep 시 run_dir 보존."""
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    captured_cwd: list[Path] = []

    def fake_call(**kwargs):
        captured_cwd.append(Path(kwargs["cwd"]))
        return _mock_claude_call_success(**kwargs)

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
        "--keep",
    ])
    try:
        with patch.object(ax_product_run.claude, "call", side_effect=fake_call):
            ax_product_run.main()

        assert captured_cwd[0].exists(), "--keep should preserve run_dir"
    finally:
        # 수동 cleanup (테스트 후)
        if captured_cwd and captured_cwd[0].exists():
            shutil.rmtree(captured_cwd[0], ignore_errors=True)


def test_fixture_remains_plain_directory(tmp_path, monkeypatch):
    """드라이버 실행 후 fixture 원본에 .git 이 생성되지 않아야 함."""
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
    ])
    with patch.object(ax_product_run.claude, "call", side_effect=_mock_claude_call_success):
        ax_product_run.main()

    assert not (fixture / ".git").exists(), "fixture must remain plain (no .git)"


def test_driver_rejects_fixture_with_git(tmp_path, monkeypatch):
    """fixture 에 .git 이 이미 있으면 드라이버가 거부 (exit 2)."""
    fixture = _make_fixture(tmp_path)
    (fixture / ".git").mkdir()
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
    ])
    rc = ax_product_run.main()
    assert rc == 2


def test_driver_rejects_missing_plugin_dir(tmp_path, monkeypatch):
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "nonexistent"

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
    ])
    rc = ax_product_run.main()
    assert rc == 2
