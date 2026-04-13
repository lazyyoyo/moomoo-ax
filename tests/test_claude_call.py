"""
src/claude.py 단위 테스트.

범위:
- _build_command: 옵션별 CLI 플래그 조립
- parse_stream_json: NDJSON → 통합 dict
- call() 반환 shape (subprocess mock)
- call_for_script() stderr 메타 출력
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import claude  # noqa: E402


# ────────────────────────────────────────────────────────────
# _build_command
# ────────────────────────────────────────────────────────────


def test_build_command_minimal():
    cmd = claude._build_command(
        prompt="hi",
        output_format="json",
        allowed_tools=None,
        permission_mode=None,
        plugin_dir=None,
        bare=False,
        setting_sources=None,
    )
    assert cmd == ["claude", "-p", "hi", "--output-format", "json"]


def test_build_command_stream_json_adds_verbose():
    cmd = claude._build_command(
        prompt="hi",
        output_format="stream-json",
        allowed_tools=None,
        permission_mode=None,
        plugin_dir=None,
        bare=False,
        setting_sources=None,
    )
    assert "--verbose" in cmd
    assert cmd[:5] == ["claude", "-p", "hi", "--output-format", "stream-json"]


def test_build_command_all_options():
    cmd = claude._build_command(
        prompt="hi",
        output_format="stream-json",
        allowed_tools=["Read", "Write", "Bash(git:*)"],
        permission_mode="acceptEdits",
        plugin_dir="/abs/plugin",
        bare=True,
        setting_sources="project,local",
    )
    assert "--allowedTools" in cmd
    # allowedTools 뒤에 tools 가 순서대로
    idx = cmd.index("--allowedTools")
    assert cmd[idx + 1 : idx + 4] == ["Read", "Write", "Bash(git:*)"]
    assert "--permission-mode" in cmd
    assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"
    assert "--plugin-dir" in cmd
    assert cmd[cmd.index("--plugin-dir") + 1] == "/abs/plugin"
    assert "--bare" in cmd
    assert "--setting-sources" in cmd
    assert cmd[cmd.index("--setting-sources") + 1] == "project,local"


def test_build_command_no_allowed_tools_no_flag():
    cmd = claude._build_command(
        prompt="hi",
        output_format="json",
        allowed_tools=[],  # 빈 리스트는 플래그 생략
        permission_mode=None,
        plugin_dir=None,
        bare=False,
        setting_sources=None,
    )
    assert "--allowedTools" not in cmd


# ────────────────────────────────────────────────────────────
# parse_stream_json
# ────────────────────────────────────────────────────────────


def _ndjson(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events) + "\n"


def test_parse_stream_json_empty():
    result = claude.parse_stream_json("")
    assert result["output"] == ""
    assert result["tool_events"] == []
    assert result["num_turns"] == 0
    assert result["cost_usd"] == 0.0


def test_parse_stream_json_init_captures_session():
    stream = _ndjson(
        {
            "type": "system",
            "subtype": "init",
            "session_id": "sess-1",
            "model": "claude-opus-4-6[1m]",
        }
    )
    result = claude.parse_stream_json(stream)
    assert result["session_id"] == "sess-1"
    assert result["model"] == "claude-opus-4-6[1m]"


def test_parse_stream_json_tool_use_pair():
    stream = _ndjson(
        {
            "type": "assistant",
            "message": {
                "usage": {
                    "input_tokens": 5,
                    "output_tokens": 10,
                    "cache_creation_input_tokens": 100,
                    "cache_read_input_tokens": 50,
                },
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_01",
                        "name": "Read",
                        "input": {"file_path": "/tmp/a.txt"},
                    }
                ],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01",
                        "content": "file content here",
                    }
                ]
            },
        },
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "done",
            "num_turns": 2,
            "total_cost_usd": 0.42,
            "usage": {
                "input_tokens": 7,
                "output_tokens": 20,
                "cache_creation_input_tokens": 200,
                "cache_read_input_tokens": 100,
            },
            "session_id": "sess-2",
        },
    )
    result = claude.parse_stream_json(stream)
    assert result["output"] == "done"
    assert result["num_turns"] == 2
    assert result["cost_usd"] == 0.42
    assert result["session_id"] == "sess-2"
    assert result["tokens"] == {
        "input": 7,
        "output": 20,
        "cache_creation": 200,
        "cache_read": 100,
    }
    assert len(result["tool_events"]) == 1
    event = result["tool_events"][0]
    assert event["tool_name"] == "Read"
    assert event["tool_input"] == {"file_path": "/tmp/a.txt"}
    assert event["tool_result"] == "file content here"
    assert event["tool_use_id"] == "toolu_01"


def test_parse_stream_json_multiple_tools_and_orphan():
    """tool_use 3개 중 2개만 result 반환 → 1개는 orphan 으로도 append."""
    stream = _ndjson(
        {
            "type": "assistant",
            "message": {
                "usage": {"input_tokens": 1, "output_tokens": 1,
                          "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "Read", "input": {"p": "a"}},
                    {"type": "tool_use", "id": "t2", "name": "Write", "input": {"p": "b"}},
                    {"type": "tool_use", "id": "t3", "name": "Bash", "input": {"c": "ls"}},
                ],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "tool_use_id": "t1", "content": "ok1"},
                    {"type": "tool_result", "tool_use_id": "t2", "content": "ok2"},
                ]
            },
        },
        {"type": "result", "subtype": "success", "result": "done", "num_turns": 2,
         "total_cost_usd": 0.1, "usage": {}},
    )
    result = claude.parse_stream_json(stream)
    assert len(result["tool_events"]) == 3
    names = [e["tool_name"] for e in result["tool_events"]]
    assert set(names) == {"Read", "Write", "Bash"}
    # orphan (t3) 도 결과에 포함되지만 tool_result 는 None
    t3 = next(e for e in result["tool_events"] if e["tool_use_id"] == "t3")
    assert t3["tool_result"] is None


def test_parse_stream_json_handles_malformed_lines():
    stream = "not-json\n" + json.dumps(
        {"type": "result", "result": "ok", "num_turns": 1, "total_cost_usd": 0.05, "usage": {}}
    ) + "\n" + "{broken"
    result = claude.parse_stream_json(stream)
    assert result["output"] == "ok"
    assert result["num_turns"] == 1


# ────────────────────────────────────────────────────────────
# call() — subprocess mock
# ────────────────────────────────────────────────────────────


def _mock_completed(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


def test_call_json_success():
    payload = {
        "result": "hello",
        "num_turns": 1,
        "total_cost_usd": 0.25,
        "usage": {
            "input_tokens": 3,
            "output_tokens": 5,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 0,
        },
        "session_id": "abc",
    }
    with patch("claude.subprocess.run",
               return_value=_mock_completed(0, json.dumps(payload))):
        result = claude.call("hi")
    assert result["success"] is True
    assert result["output"] == "hello"
    assert result["cost_usd"] == 0.25
    assert result["num_turns"] == 1
    assert result["session_id"] == "abc"
    assert result["tokens"]["cache_creation"] == 100
    assert result["tool_events"] == []
    assert result["error"] is None


def test_call_json_invalid_stdout_fallback():
    with patch("claude.subprocess.run",
               return_value=_mock_completed(0, "not json at all")):
        result = claude.call("hi")
    assert result["success"] is True
    assert result["output"] == "not json at all"


def test_call_stream_json_success():
    stream = _ndjson(
        {"type": "system", "subtype": "init", "session_id": "s1",
         "model": "claude-opus-4-6[1m]"},
        {"type": "assistant", "message": {
            "usage": {"input_tokens": 1, "output_tokens": 1,
                      "cache_creation_input_tokens": 10, "cache_read_input_tokens": 0},
            "content": [{"type": "tool_use", "id": "tA", "name": "Read",
                         "input": {"file_path": "/x"}}]}},
        {"type": "user", "message": {
            "content": [{"type": "tool_result", "tool_use_id": "tA",
                         "content": "xxx"}]}},
        {"type": "result", "subtype": "success", "result": "done",
         "num_turns": 2, "total_cost_usd": 0.33,
         "usage": {"input_tokens": 2, "output_tokens": 3,
                   "cache_creation_input_tokens": 20, "cache_read_input_tokens": 5}},
    )
    with patch("claude.subprocess.run",
               return_value=_mock_completed(0, stream)):
        result = claude.call("hi", output_format="stream-json",
                             allowed_tools=["Read"], permission_mode="acceptEdits")
    assert result["success"] is True
    assert result["output"] == "done"
    assert result["cost_usd"] == 0.33
    assert len(result["tool_events"]) == 1
    assert result["tool_events"][0]["tool_name"] == "Read"


def test_call_nonzero_returncode():
    with patch("claude.subprocess.run",
               return_value=_mock_completed(1, "", "boom")):
        result = claude.call("hi")
    assert result["success"] is False
    assert result["error"] == "boom"
    assert result["tokens"] == claude.EMPTY_TOKENS
    assert result["tool_events"] == []


def test_call_timeout():
    import subprocess as sp
    with patch("claude.subprocess.run",
               side_effect=sp.TimeoutExpired(cmd="claude", timeout=1)):
        result = claude.call("hi", timeout=1)
    assert result["success"] is False
    assert "timeout" in result["error"]


def test_call_passes_all_flags():
    captured = {}

    def fake_run(cmd, capture_output, text, timeout, cwd=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return _mock_completed(0, json.dumps({"result": "x", "num_turns": 0,
                                              "total_cost_usd": 0, "usage": {}}))

    with patch("claude.subprocess.run", side_effect=fake_run):
        claude.call(
            "hi",
            allowed_tools=["Read", "Write"],
            permission_mode="acceptEdits",
            plugin_dir="/abs/plugin",
            bare=True,
            setting_sources="project",
        )
    cmd = captured["cmd"]
    assert "--allowedTools" in cmd
    assert "Read" in cmd and "Write" in cmd
    assert cmd[cmd.index("--permission-mode") + 1] == "acceptEdits"
    assert cmd[cmd.index("--plugin-dir") + 1] == "/abs/plugin"
    assert "--bare" in cmd
    assert cmd[cmd.index("--setting-sources") + 1] == "project"


# ────────────────────────────────────────────────────────────
# call_for_script
# ────────────────────────────────────────────────────────────


def test_call_for_script_emits_compact_meta_on_stderr(capsys):
    payload = {
        "result": "output text",
        "num_turns": 2,
        "total_cost_usd": 0.5,
        "usage": {"input_tokens": 1, "output_tokens": 2,
                  "cache_creation_input_tokens": 10, "cache_read_input_tokens": 5},
    }
    with patch("claude.subprocess.run",
               return_value=_mock_completed(0, json.dumps(payload))):
        output, meta = claude.call_for_script("hi")
    assert output == "output text"
    assert meta["tokens"]["cache_creation"] == 10
    assert meta["num_turns"] == 2

    captured = capsys.readouterr()
    assert captured.err.strip()
    stderr_obj = json.loads(captured.err.strip().splitlines()[-1])
    assert stderr_obj["tokens"]["cache_creation"] == 10
    assert stderr_obj["num_turns"] == 2
    assert stderr_obj["tool_call_count"] == 0


def test_call_for_script_exits_on_failure():
    with patch("claude.subprocess.run",
               return_value=_mock_completed(1, "", "fatal")):
        with pytest.raises(SystemExit) as exc:
            claude.call_for_script("hi")
    assert exc.value.code == 1
