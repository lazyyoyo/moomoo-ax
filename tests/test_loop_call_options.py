"""
src/loop.py 의 v0.3 Phase 1 추가 경로 단위 테스트.

범위:
- resolve_call_options: program.md frontmatter 의 call_options 정규화
- call_options_to_env: 정규화된 dict → env 변수 매핑
- run_script: env 주입 + stderr tool_call_count 집계
- improve_artifact: call_options → claude.call kwargs 전파
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import loop  # noqa: E402


# ────────────────────────────────────────────────────────────
# resolve_call_options
# ────────────────────────────────────────────────────────────


def test_resolve_call_options_none(tmp_path):
    assert loop.resolve_call_options(None, tmp_path) == {}


def test_resolve_call_options_dict_list(tmp_path):
    raw = {
        "allowed_tools": ["Read", "Write"],
        "permission_mode": "acceptEdits",
        "output_format": "stream-json",
        "bare": True,
    }
    out = loop.resolve_call_options(raw, tmp_path)
    assert out["allowed_tools"] == ["Read", "Write"]
    assert out["permission_mode"] == "acceptEdits"
    assert out["output_format"] == "stream-json"
    assert out["bare"] is True


def test_resolve_call_options_allowed_tools_string(tmp_path):
    raw = {"allowed_tools": "Read, Write,Bash"}
    out = loop.resolve_call_options(raw, tmp_path)
    assert out["allowed_tools"] == ["Read", "Write", "Bash"]


def test_resolve_call_options_plugin_dir_relative(tmp_path):
    raw = {"plugin_dir": "../../plugin"}
    out = loop.resolve_call_options(raw, tmp_path / "labs" / "ax-implement")
    # 결과는 절대경로, 구조적으로 해석됨
    assert Path(out["plugin_dir"]).is_absolute()
    assert out["plugin_dir"].endswith("plugin")


def test_resolve_call_options_plugin_dir_absolute(tmp_path):
    abs_path = str(tmp_path / "absolute" / "plugin")
    raw = {"plugin_dir": abs_path}
    out = loop.resolve_call_options(raw, tmp_path)
    assert out["plugin_dir"] == abs_path


def test_resolve_call_options_unknown_key_ignored(tmp_path, capsys):
    raw = {"allowed_tools": ["Read"], "unknown_key": "value"}
    out = loop.resolve_call_options(raw, tmp_path)
    assert "unknown_key" not in out
    assert "allowed_tools" in out
    captured = capsys.readouterr()
    assert "unknown_key" in captured.out


def test_resolve_call_options_non_dict_returns_empty(tmp_path, capsys):
    assert loop.resolve_call_options("not a dict", tmp_path) == {}
    assert loop.resolve_call_options([1, 2], tmp_path) == {}


def test_resolve_call_options_bad_allowed_tools(tmp_path, capsys):
    raw = {"allowed_tools": 123}
    out = loop.resolve_call_options(raw, tmp_path)
    assert "allowed_tools" not in out


# ────────────────────────────────────────────────────────────
# call_options_to_env
# ────────────────────────────────────────────────────────────


def test_call_options_to_env_empty():
    assert loop.call_options_to_env({}) == {}


def test_call_options_to_env_list_comma_joined():
    out = loop.call_options_to_env({"allowed_tools": ["Read", "Write", "Bash"]})
    assert out["MOOMOO_AX_ALLOWED_TOOLS"] == "Read,Write,Bash"


def test_call_options_to_env_bare_flag():
    out = loop.call_options_to_env({"bare": True})
    assert out["MOOMOO_AX_BARE"] == "1"


def test_call_options_to_env_bare_false_omitted():
    out = loop.call_options_to_env({"bare": False})
    assert "MOOMOO_AX_BARE" not in out


def test_call_options_to_env_full():
    opts = {
        "allowed_tools": ["Read"],
        "permission_mode": "acceptEdits",
        "output_format": "stream-json",
        "plugin_dir": "/abs/plugin",
        "bare": True,
        "setting_sources": "project,local",
    }
    out = loop.call_options_to_env(opts)
    assert out == {
        "MOOMOO_AX_ALLOWED_TOOLS": "Read",
        "MOOMOO_AX_PERMISSION_MODE": "acceptEdits",
        "MOOMOO_AX_OUTPUT_FORMAT": "stream-json",
        "MOOMOO_AX_PLUGIN_DIR": "/abs/plugin",
        "MOOMOO_AX_BARE": "1",
        "MOOMOO_AX_SETTING_SOURCES": "project,local",
    }


# ────────────────────────────────────────────────────────────
# run_script — env 주입
# ────────────────────────────────────────────────────────────


def _mock_subprocess(stdout: str, stderr: str = "", returncode: int = 0) -> MagicMock:
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = stderr
    mock.returncode = returncode
    return mock


def test_run_script_passes_env_variables(tmp_path):
    script_py = tmp_path / "script.py"
    script_py.write_text("print('hi')")

    captured = {}

    def fake_run(cmd, input, capture_output, text, timeout, cwd, env):
        captured["env"] = env
        return _mock_subprocess("output")

    call_options = {
        "allowed_tools": ["Read", "Write"],
        "permission_mode": "acceptEdits",
        "output_format": "stream-json",
    }
    with patch("loop.subprocess.run", side_effect=fake_run):
        result = loop.run_script(script_py, "fixture text",
                                 call_options=call_options)

    assert result["success"] is True
    env = captured["env"]
    assert env["MOOMOO_AX_ALLOWED_TOOLS"] == "Read,Write"
    assert env["MOOMOO_AX_PERMISSION_MODE"] == "acceptEdits"
    assert env["MOOMOO_AX_OUTPUT_FORMAT"] == "stream-json"


def test_run_script_no_call_options_no_env_pollution(tmp_path):
    script_py = tmp_path / "script.py"
    script_py.write_text("print('hi')")
    captured = {}

    def fake_run(cmd, input, capture_output, text, timeout, cwd, env):
        captured["env"] = env
        return _mock_subprocess("output")

    with patch("loop.subprocess.run", side_effect=fake_run):
        loop.run_script(script_py, "fixture")

    env = captured["env"]
    assert "MOOMOO_AX_ALLOWED_TOOLS" not in env
    assert "MOOMOO_AX_PERMISSION_MODE" not in env


def test_run_script_parses_tool_call_count_from_stderr(tmp_path):
    script_py = tmp_path / "script.py"
    script_py.write_text("print('x')")
    stderr_meta = json.dumps({
        "tokens": {"input": 5, "output": 10,
                   "cache_creation": 100, "cache_read": 50},
        "cost_usd": 0.33,
        "num_turns": 2,
        "tool_call_count": 1,
    })
    with patch("loop.subprocess.run",
               return_value=_mock_subprocess("output text", stderr_meta)):
        result = loop.run_script(script_py, "fixture")
    assert result["tool_call_count"] == 1
    assert result["num_turns"] == 2
    assert result["tokens"]["cache_creation"] == 100
    assert result["cost_usd"] == 0.33


# ────────────────────────────────────────────────────────────
# improve_artifact — call_options 전파
# ────────────────────────────────────────────────────────────


def test_improve_artifact_passes_options_to_claude_call(tmp_path):
    target = tmp_path / "SKILL.md"
    original = "---\nname: x\n---\n\n## A\n\n본문.\n" + "\n".join(f"line {i}" for i in range(50))
    target.write_text(original)

    captured_kwargs = {}

    new_content = "---\nname: x\n---\n\n## A\n\n## B\n\n" + "\n".join(f"l {i}" for i in range(50))
    fake_result = {
        "success": True,
        "output": f"```markdown\n{new_content}\n```",
        "tokens": {"input": 1, "output": 2,
                   "cache_creation": 0, "cache_read": 0},
        "cost_usd": 0.1,
    }

    def fake_call(prompt, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_result

    call_options = {
        "allowed_tools": ["Read", "Write"],
        "permission_mode": "acceptEdits",
        "output_format": "stream-json",  # improve 에선 stream-json 전파 안 함
        "plugin_dir": "/abs/plugin",
        "bare": True,
        "setting_sources": "project",
    }

    with patch("loop.claude_api.call", side_effect=fake_call):
        meta = loop.improve_artifact(
            "program body",
            target,
            [{"question": "failed test"}],
            "earlier output",
            call_options=call_options,
        )

    # allowed_tools, permission_mode, plugin_dir, bare, setting_sources 만 전파
    # (output_format 은 improve 쪽에서 제외)
    assert captured_kwargs["allowed_tools"] == ["Read", "Write"]
    assert captured_kwargs["permission_mode"] == "acceptEdits"
    assert captured_kwargs["plugin_dir"] == "/abs/plugin"
    assert captured_kwargs["bare"] is True
    assert captured_kwargs["setting_sources"] == "project"
    assert "output_format" not in captured_kwargs

    assert meta["skipped"] is False


def test_improve_artifact_without_call_options(tmp_path):
    """call_options 가 None 이어도 기존 동작 유지 (호환성)."""
    target = tmp_path / "SKILL.md"
    target.write_text("---\nname: x\n---\n\n## A\n\n" + "\n".join(f"l{i}" for i in range(50)))

    captured_kwargs = {}
    new_md = "---\nname: x\n---\n\n## A\n\n## B\n\n" + "\n".join(f"l{i}" for i in range(50))

    def fake_call(prompt, **kwargs):
        captured_kwargs.update(kwargs)
        return {
            "success": True,
            "output": f"```markdown\n{new_md}\n```",
            "tokens": {"input": 1, "output": 1,
                       "cache_creation": 0, "cache_read": 0},
            "cost_usd": 0.05,
        }

    with patch("loop.claude_api.call", side_effect=fake_call):
        meta = loop.improve_artifact(
            "program body",
            target,
            [{"question": "x"}],
            "output",
        )

    # kwargs 는 비어있어야 함 (call_options=None)
    assert captured_kwargs == {}
    assert meta["skipped"] is False
