"""
scripts/ax_generated.py + scripts/ax_post_commit.py 테스트.

- ax_generated: 매니페스트 record/lookup/reconcile 단위 테스트
- ax_post_commit: 임시 git repo 에서 end-to-end (dry-run)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import ax_generated  # noqa: E402
import ax_post_commit  # noqa: E402


# ──────────────────────────────────────────────────────────
# ax_generated — 매니페스트 헬퍼
# ──────────────────────────────────────────────────────────

def test_record_creates_manifest_and_artifact(tmp_path):
    ax_generated.record(
        tmp_path,
        "src/foo.ts",
        stage="ax-implement",
        fixture_id="haru:abc123",
        user_name="yoyo",
        content="export const foo = 1\n",
    )

    manifest = tmp_path / ".ax-generated.jsonl"
    assert manifest.exists()
    line = manifest.read_text().strip()
    entry = json.loads(line)
    assert entry["path"] == "src/foo.ts"
    assert entry["stage"] == "ax-implement"
    assert entry["fixture_id"] == "haru:abc123"
    assert entry["user_name"] == "yoyo"
    assert "generated_at" in entry

    artifact = tmp_path / ".ax-artifacts" / "src" / "foo.ts"
    assert artifact.exists()
    assert artifact.read_text() == "export const foo = 1\n"


def test_lookup_returns_latest_entry(tmp_path):
    ax_generated.record(
        tmp_path, "src/foo.ts",
        stage="ax-implement", fixture_id="x:1", user_name="yoyo",
        content="v1\n",
    )
    ax_generated.record(
        tmp_path, "src/foo.ts",
        stage="ax-implement", fixture_id="x:2", user_name="yoyo",
        content="v2\n",
    )
    entry = ax_generated.lookup(tmp_path, "src/foo.ts")
    assert entry is not None
    assert entry["fixture_id"] == "x:2"


def test_lookup_missing_returns_none(tmp_path):
    assert ax_generated.lookup(tmp_path, "nothing.ts") is None


def test_reconcile_removes_entry_and_artifact(tmp_path):
    ax_generated.record(
        tmp_path, "src/foo.ts",
        stage="ax-implement", fixture_id="x:1", user_name="yoyo",
        content="v1\n",
    )
    ax_generated.record(
        tmp_path, "src/bar.ts",
        stage="ax-implement", fixture_id="x:1", user_name="yoyo",
        content="v1\n",
    )

    removed = ax_generated.reconcile(tmp_path, "src/foo.ts")
    assert removed is True

    # foo 는 사라져야 함
    assert ax_generated.lookup(tmp_path, "src/foo.ts") is None
    assert not (tmp_path / ".ax-artifacts" / "src" / "foo.ts").exists()

    # bar 는 남아 있어야 함
    assert ax_generated.lookup(tmp_path, "src/bar.ts") is not None
    assert (tmp_path / ".ax-artifacts" / "src" / "bar.ts").exists()


def test_reconcile_removes_all_entries_clears_manifest(tmp_path):
    ax_generated.record(
        tmp_path, "only.ts",
        stage="ax-implement", fixture_id="x:1", user_name="yoyo",
        content="v1\n",
    )
    ax_generated.reconcile(tmp_path, "only.ts")

    manifest = tmp_path / ".ax-generated.jsonl"
    assert not manifest.exists()


def test_all_tracked_paths(tmp_path):
    ax_generated.record(
        tmp_path, "a.ts",
        stage="ax-implement", fixture_id="x:1", user_name="yoyo", content="a\n",
    )
    ax_generated.record(
        tmp_path, "b.ts",
        stage="ax-implement", fixture_id="x:1", user_name="yoyo", content="b\n",
    )
    ax_generated.record(
        tmp_path, "a.ts",  # dup
        stage="ax-implement", fixture_id="x:2", user_name="yoyo", content="a2\n",
    )
    paths = ax_generated.all_tracked_paths(tmp_path)
    assert paths == {"a.ts", "b.ts"}


# ──────────────────────────────────────────────────────────
# compute_diff_stats — diff 측정
# ──────────────────────────────────────────────────────────

def test_diff_stats_identical_is_zero():
    stats = ax_post_commit.compute_diff_stats("a\nb\nc\n", "a\nb\nc\n")
    assert stats == {
        "hunks_added": 0, "hunks_deleted": 0,
        "lines_added": 0, "lines_deleted": 0,
    }


def test_diff_stats_pure_addition():
    stats = ax_post_commit.compute_diff_stats("a\nb\n", "a\nb\nc\nd\n")
    assert stats["lines_added"] == 2
    assert stats["lines_deleted"] == 0
    assert stats["hunks_added"] >= 1


def test_diff_stats_pure_deletion():
    stats = ax_post_commit.compute_diff_stats("a\nb\nc\nd\n", "a\nb\n")
    assert stats["lines_deleted"] == 2
    assert stats["lines_added"] == 0


def test_diff_stats_replace():
    stats = ax_post_commit.compute_diff_stats("a\nb\nc\n", "a\nXX\nc\n")
    assert stats["lines_added"] >= 1
    assert stats["lines_deleted"] >= 1


# ──────────────────────────────────────────────────────────
# process_commit — 임시 git repo end-to-end (dry-run)
# ──────────────────────────────────────────────────────────

def _run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def tmp_git_repo(tmp_path):
    """git 초기화 + 초기 커밋된 임시 repo."""
    _run(["git", "init", "-q", "-b", "main"], cwd=tmp_path)
    _run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)
    _run(["git", "config", "user.name", "test"], cwd=tmp_path)
    _run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("init\n")
    _run(["git", "add", "."], cwd=tmp_path)
    _run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path)
    return tmp_path


def test_process_commit_no_manifest_noop(tmp_git_repo):
    records = ax_post_commit.process_commit(tmp_git_repo, dry_run=True)
    assert records == []


def test_process_commit_ax_file_unchanged_is_recorded_as_zero_diff(tmp_git_repo):
    """ax 가 생성한 파일이 그대로 커밋되면 diff 0 로 기록 (intervention 0)."""
    content = "const a = 1\n" * 10
    src = tmp_git_repo / "src.ts"
    src.write_text(content)

    ax_generated.record(
        tmp_git_repo, "src.ts",
        stage="ax-implement", fixture_id="haru:t1", user_name="yoyo",
        content=content,
    )

    _run(["git", "add", "src.ts"], cwd=tmp_git_repo)
    _run(["git", "commit", "-q", "-m", "apply ax output as-is"], cwd=tmp_git_repo)

    records = ax_post_commit.process_commit(tmp_git_repo, dry_run=True)
    assert len(records) == 1
    rec = records[0]
    assert rec["original_path"] == "src.ts"
    assert rec["lines_added"] == 0
    assert rec["lines_deleted"] == 0
    assert rec["hunks_added"] == 0
    assert rec["stage"] == "ax-implement"
    assert rec["user_name"] == "yoyo"
    assert rec["project"] == tmp_git_repo.name

    # reconcile 되었는지
    assert ax_generated.lookup(tmp_git_repo, "src.ts") is None


def test_process_commit_ax_file_modified_captures_diff(tmp_git_repo):
    """ax 생성물을 오너가 수정 후 커밋 → lines_added/deleted 잡힘."""
    original = "const a = 1\nconst b = 2\nconst c = 3\n"
    modified = "const a = 1\nconst b = 999\nconst c = 3\nconst d = 4\n"

    src = tmp_git_repo / "src.ts"
    src.write_text(original)
    ax_generated.record(
        tmp_git_repo, "src.ts",
        stage="ax-implement", fixture_id="haru:t1", user_name="yoyo",
        content=original,
    )
    # 오너가 수정
    src.write_text(modified)

    _run(["git", "add", "src.ts"], cwd=tmp_git_repo)
    _run(["git", "commit", "-q", "-m", "tweak ax output"], cwd=tmp_git_repo)

    records = ax_post_commit.process_commit(tmp_git_repo, dry_run=True)
    assert len(records) == 1
    rec = records[0]
    assert rec["lines_added"] >= 1
    assert rec["lines_deleted"] >= 1


def test_process_commit_untracked_file_ignored(tmp_git_repo):
    """매니페스트에 없는 파일은 무시."""
    (tmp_git_repo / "untracked.ts").write_text("plain file\n")
    _run(["git", "add", "untracked.ts"], cwd=tmp_git_repo)
    _run(["git", "commit", "-q", "-m", "random"], cwd=tmp_git_repo)

    records = ax_post_commit.process_commit(tmp_git_repo, dry_run=True)
    assert records == []


def test_process_commit_mixed_tracked_and_untracked(tmp_git_repo):
    """한 커밋에 ax 파일 + 일반 파일 섞여 있어도 ax 만 잡음."""
    ax_generated.record(
        tmp_git_repo, "ax_file.ts",
        stage="ax-implement", fixture_id="haru:t1", user_name="yoyo",
        content="ax orig\n",
    )
    (tmp_git_repo / "ax_file.ts").write_text("ax orig\n")
    (tmp_git_repo / "owner_file.ts").write_text("owner made this\n")

    _run(["git", "add", "."], cwd=tmp_git_repo)
    _run(["git", "commit", "-q", "-m", "mixed"], cwd=tmp_git_repo)

    records = ax_post_commit.process_commit(tmp_git_repo, dry_run=True)
    assert len(records) == 1
    assert records[0]["original_path"] == "ax_file.ts"
