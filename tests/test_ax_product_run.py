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
    assert "Task" not in tools


def test_build_allowed_tools_scopes_write_edit_when_editable_root_is_set(tmp_path):
    plugin_dir = tmp_path / "plug"
    editable_root = tmp_path / "dashboard"
    editable_root.mkdir()

    tools = ax_product_run.build_allowed_tools(plugin_dir, editable_root=editable_root)
    editable_pattern = f"//{editable_root.resolve().as_posix().lstrip('/')}/**"

    assert f"Write({editable_pattern})" in tools
    assert f"Edit({editable_pattern})" in tools
    assert "Write" not in tools
    assert "Edit" not in tools


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
    with (
        patch.object(ax_product_run.claude, "call", side_effect=fake_call),
        patch.object(ax_product_run.db, "start_product_run", return_value=True),
        patch.object(ax_product_run.db, "finish_product_run", return_value=True),
    ):
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
    with (
        patch.object(ax_product_run.claude, "call", side_effect=fake_call),
        patch.object(ax_product_run.db, "start_product_run", return_value=True),
        patch.object(ax_product_run.db, "finish_product_run", return_value=True),
    ):
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
    with (
        patch.object(ax_product_run.claude, "call", side_effect=fake_call),
        patch.object(ax_product_run.db, "start_product_run", return_value=True),
        patch.object(ax_product_run.db, "finish_product_run", return_value=True),
    ):
        rc = ax_product_run.main()

    assert captured_cwd
    assert rc == 1
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
        with (
            patch.object(ax_product_run.claude, "call", side_effect=fake_call),
            patch.object(ax_product_run.db, "start_product_run", return_value=True),
            patch.object(ax_product_run.db, "finish_product_run", return_value=True),
        ):
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
    with (
        patch.object(ax_product_run.claude, "call", side_effect=_mock_claude_call_success),
        patch.object(ax_product_run.db, "start_product_run", return_value=True),
        patch.object(ax_product_run.db, "finish_product_run", return_value=True),
    ):
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


def test_driver_target_subdir_mode_uses_scoped_cwd_and_prompt(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "dashboard"
    target_dir.mkdir(parents=True)
    (target_dir / "plan.md").write_text("- [ ] T-001 dummy\n", encoding="utf-8")
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    captured = {}
    guard_state = {"tracked": "", "staged": "", "untracked": ""}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return _mock_claude_call_success(**kwargs)

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--target-subdir", "dashboard",
        "--repo-root", str(repo_root),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
    ])
    with (
        patch.object(ax_product_run.claude, "call", side_effect=fake_call),
        patch.object(ax_product_run, "_capture_outside_target_state",
                     side_effect=[guard_state, guard_state]),
        patch.object(ax_product_run.db, "start_product_run", return_value=True) as start_mock,
        patch.object(ax_product_run.db, "finish_product_run", return_value=True),
    ):
        rc = ax_product_run.main()

    assert rc == 0
    assert captured["cwd"] == target_dir.resolve()
    assert "[TARGET_SUBDIR]" in captured["prompt"]
    assert "dashboard" in captured["prompt"]
    editable_pattern = f"//{target_dir.resolve().as_posix().lstrip('/')}/**"
    assert f"Write({editable_pattern})" in captured["allowed_tools"]
    assert f"Edit({editable_pattern})" in captured["allowed_tools"]

    start_kwargs = start_mock.call_args.kwargs
    assert start_kwargs["project"] == repo_root.name
    assert start_kwargs["output_path"] == "dashboard"
    assert start_kwargs["fixture_id"] is None


def test_driver_rejects_target_subdir_inside_harness_paths(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    deny_target = repo_root / "plugin"
    deny_target.mkdir(parents=True)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--target-subdir", "plugin",
        "--repo-root", str(repo_root),
        "--plugin-dir", str(plugin_dir),
    ])

    rc = ax_product_run.main()
    assert rc == 2


def test_driver_aborts_when_product_run_start_logging_fails(tmp_path, monkeypatch):
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

    with (
        patch.object(ax_product_run.db, "start_product_run", return_value=False),
        patch.object(ax_product_run.claude, "call") as call_mock,
    ):
        rc = ax_product_run.main()

    assert rc == 3
    call_mock.assert_not_called()


def test_driver_logs_product_run_start_and_finish(tmp_path, monkeypatch):
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

    with (
        patch.object(ax_product_run.claude, "call", side_effect=_mock_claude_call_success),
        patch.object(ax_product_run.db, "start_product_run", return_value=True) as start_mock,
        patch.object(ax_product_run.db, "finish_product_run", return_value=True) as finish_mock,
    ):
        rc = ax_product_run.main()

    assert rc == 0
    start_kwargs = start_mock.call_args.kwargs
    assert start_kwargs["project"] == fixture.name
    assert start_kwargs["command"] == "/team-ax:ax-implement"
    assert start_kwargs["stage"] == "ax-implement"
    assert start_kwargs["fixture_id"] == fixture.name

    finish_kwargs = finish_mock.call_args.kwargs
    assert finish_kwargs["status"] == "done"
    assert finish_kwargs["stage"] == "ax-implement"
    assert finish_kwargs["session_id"] == "test-sess"
    assert finish_kwargs["num_turns"] == 2
    assert finish_kwargs["cost_usd"] == 0.01
    assert finish_kwargs["tool_call_stats"] == {
        "tool_counts": {},
        "task_subagent_counts": {},
    }


def test_driver_returns_nonzero_when_finish_logging_fails(tmp_path, monkeypatch):
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

    with (
        patch.object(ax_product_run.claude, "call", side_effect=_mock_claude_call_success),
        patch.object(ax_product_run.db, "start_product_run", return_value=True),
        patch.object(ax_product_run.db, "finish_product_run", return_value=False),
    ):
        rc = ax_product_run.main()

    assert rc == 3


def test_driver_project_override_wins_over_fixture_name(tmp_path, monkeypatch):
    fixture = _make_fixture(tmp_path)
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    log_dir = tmp_path / "runs"

    monkeypatch.setattr(sys, "argv", [
        "ax_product_run.py",
        "--fixture", str(fixture),
        "--plugin-dir", str(plugin_dir),
        "--log-dir", str(log_dir),
        "--project", "moomoo-ax",
    ])

    with (
        patch.object(ax_product_run.claude, "call", side_effect=_mock_claude_call_success),
        patch.object(ax_product_run.db, "start_product_run", return_value=True) as start_mock,
        patch.object(ax_product_run.db, "finish_product_run", return_value=True),
    ):
        rc = ax_product_run.main()

    assert rc == 0
    assert start_mock.call_args.kwargs["project"] == "moomoo-ax"


def test_summarize_tool_calls_counts_task_subagents():
    tool_events = [
        {"tool_name": "Task", "tool_input": {"subagent_type": "team-ax:executor"}},
        {"tool_name": "Task", "tool_input": {"subagent_type": "team-ax:reviewer"}},
        {"tool_name": "Task", "tool_input": {"subagent_type": "team-ax:reviewer"}},
        {"tool_name": "Bash", "tool_input": {"cmd": "git status"}},
    ]

    stats = ax_product_run._summarize_tool_calls(tool_events)

    assert stats["tool_counts"] == {"Task": 3, "Bash": 1}
    assert stats["task_subagent_counts"] == {
        "team-ax:executor": 1,
        "team-ax:reviewer": 2,
    }


def test_summarize_tool_calls_counts_agent_tool_subagents():
    tool_events = [
        {"tool_name": "Agent", "tool_input": {"agent_type": "reviewer"}},
        {"tool_name": "Agent", "tool_input": {"subagent_type": "executor"}},
        {"tool_name": "Bash", "tool_input": {"cmd": "git status"}},
    ]

    stats = ax_product_run._summarize_tool_calls(tool_events)

    assert stats["tool_counts"] == {"Agent": 2, "Bash": 1}
    assert stats["task_subagent_counts"] == {
        "reviewer": 1,
        "executor": 1,
    }
