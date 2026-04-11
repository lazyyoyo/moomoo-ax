"""
scripts/ax_feedback.py CLI 단위 테스트.

DB insert 는 mock — 실 smoke 는 별도 수동 호출.
"""

import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import ax_feedback  # noqa: E402


# ──────────────────────────────────────────────────────────
# infer_user / infer_project — 매핑 로직
# ──────────────────────────────────────────────────────────

def test_infer_user_env_var_priority(monkeypatch):
    monkeypatch.setenv("MOOMOO_AX_USER", "custom_user")
    assert ax_feedback.infer_user() == "custom_user"


def test_infer_user_git_lazyyoyo_maps_to_yoyo(monkeypatch):
    monkeypatch.delenv("MOOMOO_AX_USER", raising=False)
    with patch.object(ax_feedback, "_git", return_value="lazyyoyo"):
        assert ax_feedback.infer_user() == "yoyo"


def test_infer_user_unknown_git_passes_through(monkeypatch):
    monkeypatch.delenv("MOOMOO_AX_USER", raising=False)
    with patch.object(ax_feedback, "_git", return_value="someone_else"):
        assert ax_feedback.infer_user() == "someone_else"


def test_infer_user_no_git_falls_back_to_yoyo(monkeypatch):
    monkeypatch.delenv("MOOMOO_AX_USER", raising=False)
    with patch.object(ax_feedback, "_git", return_value=""):
        assert ax_feedback.infer_user() == "yoyo"


def test_infer_project_uses_git_toplevel():
    with patch.object(ax_feedback, "_git", return_value="/tmp/some/haru"):
        assert ax_feedback.infer_project() == "haru"


def test_infer_project_none_outside_repo():
    with patch.object(ax_feedback, "_git", return_value=""):
        assert ax_feedback.infer_project() is None


# ──────────────────────────────────────────────────────────
# read_content — arg / stdin 분기
# ──────────────────────────────────────────────────────────

def test_read_content_prefers_arg():
    assert ax_feedback.read_content("from arg") == "from arg"


def test_read_content_strips_whitespace():
    assert ax_feedback.read_content("  spaced  ") == "spaced"


def test_read_content_empty_arg_returns_empty_when_tty():
    # sys.stdin.isatty() returns True in pytest usually
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = True
        assert ax_feedback.read_content("") == ""
        assert ax_feedback.read_content(None) == ""


def test_read_content_falls_back_to_stdin():
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = False
        mock_stdin.read.return_value = "from stdin\n"
        assert ax_feedback.read_content(None) == "from stdin"


# ──────────────────────────────────────────────────────────
# CLI 통합 — subprocess + MOOMOO_AX_DRY_RUN / mock db
# ──────────────────────────────────────────────────────────

def _run_cli(args, env=None, input_text=None):
    """subprocess 로 ax_feedback.py 호출. db.log_feedback 을 미리 mock 하려면
    별도 wrapper 가 필요하므로 여기서는 mock 없이 DB 연결 실패 시 exit 2 경로 사용."""
    cmd = [sys.executable, str(ROOT / "scripts" / "ax_feedback.py"), *args]
    full_env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp"}
    if env:
        full_env.update(env)
    return subprocess.run(
        cmd, input=input_text, capture_output=True, text=True,
        env=full_env,
    )


def test_cli_rejects_empty_content():
    """arg 도 stdin 도 없으면 exit 1 + 에러 메시지."""
    result = _run_cli([])
    assert result.returncode == 1
    assert "비었" in result.stderr or "empty" in result.stderr.lower()


# ──────────────────────────────────────────────────────────
# log_feedback mock 통합 — main() 직접 호출
# ──────────────────────────────────────────────────────────

def test_main_happy_path_calls_log_feedback(monkeypatch, capsys):
    """content + priority 전달 시 log_feedback 이 올바른 인자로 호출되는지."""
    calls = []

    def fake_log_feedback(**kwargs):
        calls.append(kwargs)
        return True, "fake-row-id-123"

    # sys.argv 설정 + db mock
    monkeypatch.setattr(sys, "argv", [
        "ax-feedback",
        "--priority", "high",
        "--stage", "ax-implement",
        "--project", "haru",
        "--user", "yoyo",
        "test content here",
    ])
    # db import 되기 전에 sys.modules 에 스텁 주입
    import types
    fake_db = types.SimpleNamespace(log_feedback=fake_log_feedback)
    monkeypatch.setitem(sys.modules, "db", fake_db)

    ax_feedback.main()

    assert len(calls) == 1
    call = calls[0]
    assert call["user_name"] == "yoyo"
    assert call["content"] == "test content here"
    assert call["priority"] == "high"
    assert call["stage"] == "ax-implement"
    assert call["project"] == "haru"

    captured = capsys.readouterr()
    assert "feedback 기록됨" in captured.out
    assert "fake-row-id-123" in captured.out


def test_main_defaults_to_medium_priority(monkeypatch):
    calls = []

    def fake_log_feedback(**kwargs):
        calls.append(kwargs)
        return True, "id-1"

    monkeypatch.setattr(sys, "argv", [
        "ax-feedback", "--user", "yoyo", "minimal msg",
    ])
    # project inference 를 None 으로 고정
    monkeypatch.setattr(ax_feedback, "infer_project", lambda: None)

    import types
    monkeypatch.setitem(sys.modules, "db",
                        types.SimpleNamespace(log_feedback=fake_log_feedback))

    ax_feedback.main()
    assert calls[0]["priority"] == "medium"
    assert calls[0]["project"] is None
    assert calls[0]["stage"] is None


def test_main_exit_2_on_db_failure(monkeypatch):
    def fake_log_feedback(**kwargs):
        return False, None

    monkeypatch.setattr(sys, "argv", [
        "ax-feedback", "--user", "yoyo", "msg",
    ])
    monkeypatch.setattr(ax_feedback, "infer_project", lambda: None)

    import types
    monkeypatch.setitem(sys.modules, "db",
                        types.SimpleNamespace(log_feedback=fake_log_feedback))

    with pytest.raises(SystemExit) as exc:
        ax_feedback.main()
    assert exc.value.code == 2
