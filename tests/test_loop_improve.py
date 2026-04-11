"""
src/loop.py 의 improve_artifact 경로 단위 테스트.

R5 회귀 방지:
- 부분 코드 블록으로 전체 파일 덮어쓰기 차단
- 여러 블록 있으면 가장 긴 것 선택
- 언어별 최소 구조 검증 (python/markdown)
- 백업(.prev) 동작
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import loop  # noqa: E402


# ──────────────────────────────────────────────────────────
# extract_code_block
# ──────────────────────────────────────────────────────────

def test_extract_python_simple():
    output = """설명
```python
def main():
    print("hello")
```
"""
    result = loop.extract_code_block(output, "python")
    assert result == 'def main():\n    print("hello")'


def test_extract_python_picks_largest_of_many():
    """R5 핵심: 여러 블록 중 가장 긴 것을 선택해야 함."""
    long_block = "def main():\n" + "    pass\n" * 20
    output = f"""앞 설명
```python
def helper():
    pass
```
뒤 설명
```python
{long_block}```
"""
    result = loop.extract_code_block(output, "python")
    assert "pass" in result
    # 긴 블록이 선택되었는지
    assert result.count("pass") > 10


def test_extract_python_py_tag_variant():
    output = """```py
def main():
    x = 1
```"""
    result = loop.extract_code_block(output, "python")
    assert "def main" in result


def test_extract_python_no_match():
    output = "그냥 산문 텍스트, 코드 블록 없음"
    assert loop.extract_code_block(output, "python") is None


def test_extract_python_fallback_to_unlabeled_fence():
    """언어 태그 없는 펜스 블록도 폴백으로 추출."""
    output = """```
def main():
    return 1
```"""
    result = loop.extract_code_block(output, "python")
    assert result is not None
    assert "def main" in result


def test_extract_markdown_block():
    output = """설명
```markdown
---
name: test
---

## section one
body

## section two
more
```
"""
    result = loop.extract_code_block(output, "markdown")
    assert "name: test" in result
    assert "## section one" in result


# ──────────────────────────────────────────────────────────
# validate_structure — python
# ──────────────────────────────────────────────────────────

def test_validate_python_ok_with_main():
    content = "def main():\n    pass\n" + "# filler\n" * 40
    ok, reason = loop.validate_structure(content, "python")
    assert ok, reason


def test_validate_python_ok_with_name_guard():
    content = "x = 1\n" * 40 + 'if __name__ == "__main__":\n    print("hi")\n'
    ok, reason = loop.validate_structure(content, "python")
    assert ok, reason


def test_validate_python_fail_missing_entry():
    content = "# just comments\n" * 40
    ok, reason = loop.validate_structure(content, "python")
    assert not ok
    assert "main" in reason or "__name__" in reason


def test_validate_python_fail_too_short():
    """R5 재현 조건: Claude가 9줄짜리 함수만 반환."""
    content = "def read_dir(path):\n    return []\n" * 4
    ok, reason = loop.validate_structure(content, "python")
    assert not ok
    assert "짧음" in reason


# ──────────────────────────────────────────────────────────
# validate_structure — markdown
# ──────────────────────────────────────────────────────────

def test_validate_markdown_ok_with_frontmatter():
    content = "---\nname: test_skill\ndescription: x\n---\n\n" + "content line\n" * 50
    ok, reason = loop.validate_structure(content, "markdown")
    assert ok, reason


def test_validate_markdown_ok_with_h2_sections():
    content = "# Title\n\n" + "## Section A\nbody\n\n" * 25
    ok, reason = loop.validate_structure(content, "markdown")
    assert ok, reason


def test_validate_markdown_fail_no_structure():
    content = "just prose\n" * 50
    ok, reason = loop.validate_structure(content, "markdown")
    assert not ok
    assert "frontmatter" in reason or "H2" in reason


def test_validate_markdown_fail_too_short():
    content = "---\nname: test\n---\n\n## Section\nbody\n"
    ok, reason = loop.validate_structure(content, "markdown")
    assert not ok
    assert "짧음" in reason


# ──────────────────────────────────────────────────────────
# backup_and_write
# ──────────────────────────────────────────────────────────

def test_backup_and_write_preserves_original(tmp_path):
    target = tmp_path / "target.py"
    target.write_text("ORIGINAL\n")
    loop.backup_and_write(target, "NEW CONTENT")

    assert target.read_text() == "NEW CONTENT\n"
    prev = target.with_suffix(".py.prev")
    assert prev.exists()
    assert prev.read_text() == "ORIGINAL\n"


def test_backup_and_write_no_prev_when_target_missing(tmp_path):
    target = tmp_path / "target.md"
    loop.backup_and_write(target, "BRAND NEW")

    assert target.read_text() == "BRAND NEW\n"
    prev = target.with_suffix(".md.prev")
    assert not prev.exists()


# ──────────────────────────────────────────────────────────
# load_program — frontmatter
# ──────────────────────────────────────────────────────────

def test_load_program_with_frontmatter(tmp_path):
    program = tmp_path / "program.md"
    program.write_text("""---
improve_target: script.py
other_field: value
---

# Body Title

Content here.
""")
    config, body = loop.load_program(program)
    assert config == {"improve_target": "script.py", "other_field": "value"}
    assert body.startswith("# Body Title")


def test_load_program_without_frontmatter(tmp_path):
    program = tmp_path / "program.md"
    program.write_text("# No frontmatter\n\nJust body.")
    config, body = loop.load_program(program)
    assert config == {}
    assert "No frontmatter" in body


def test_load_program_missing_file(tmp_path):
    config, body = loop.load_program(tmp_path / "nope.md")
    assert config == {}
    assert body == ""


# ──────────────────────────────────────────────────────────
# improve_artifact — 통합 (claude_api mocking)
# ──────────────────────────────────────────────────────────

def _mock_claude_call(output_text: str):
    def _call(prompt):
        return {
            "success": True,
            "output": output_text,
            "tokens": {"input": 10, "output": 20},
            "cost_usd": 0.001,
        }
    return _call


def test_improve_artifact_r5_scenario_rejects_partial_block(tmp_path):
    """
    R5 재현: Claude가 부분 함수(9줄)만 코드 블록에 넣어 응답.
    기존 동작은 이걸 전체 script로 덮어쓰는 것이었음.
    새 동작: 구조 검증 실패 → 원본 유지.
    """
    target = tmp_path / "script.py"
    original = (
        "import sys\n\n"
        "def main():\n"
        "    data = sys.stdin.read()\n"
        "    print('result:', data)\n"
    ) + "# filler\n" * 50
    target.write_text(original)

    partial_response = """개선해봤어.
```python
def read_dir(path):
    parts = []
    for f in path.iterdir():
        if f.is_file():
            parts.append(f.read_text())
    return parts
```
"""

    with patch.object(loop.claude_api, "call", _mock_claude_call(partial_response)):
        meta = loop.improve_artifact(
            program_body="test program",
            target=target,
            failed_items=[{"question": "something failed"}],
            output="old output",
        )

    assert meta["skipped"] is True
    assert "짧음" in meta["skip_reason"]
    # 원본이 그대로 유지되어야 함
    assert target.read_text() == original
    # 백업 파일도 만들어지지 않아야 함 (write 자체가 일어나지 않았으므로)
    assert not target.with_suffix(".py.prev").exists()


def test_improve_artifact_accepts_valid_full_replacement(tmp_path):
    target = tmp_path / "script.py"
    original = "def main():\n    print('old')\n" + "# old\n" * 40
    target.write_text(original)

    new_body = "def main():\n" + "    print('new')\n" * 40
    full_response = f"""전체 교체.
```python
{new_body}
```
"""

    with patch.object(loop.claude_api, "call", _mock_claude_call(full_response)):
        meta = loop.improve_artifact(
            program_body="test",
            target=target,
            failed_items=[{"question": "q"}],
            output="x",
        )

    assert meta["skipped"] is False
    assert "new" in target.read_text()
    prev = target.with_suffix(".py.prev")
    assert prev.exists()
    assert "old" in prev.read_text()


def test_improve_artifact_markdown_target(tmp_path):
    target = tmp_path / "SKILL.md"
    original = "---\nname: old_skill\n---\n\n" + "## Section\nold body\n" * 25
    target.write_text(original)

    new_md = "---\nname: new_skill\ndescription: updated\n---\n\n" + (
        "## New Section\nnew body line\n" * 25
    )
    full_response = f"""갱신.
```markdown
{new_md}
```
"""

    with patch.object(loop.claude_api, "call", _mock_claude_call(full_response)):
        meta = loop.improve_artifact(
            program_body="test",
            target=target,
            failed_items=[{"question": "q"}],
            output="x",
        )

    assert meta["skipped"] is False
    assert "new_skill" in target.read_text()
    prev = target.with_suffix(".md.prev")
    assert prev.exists()
    assert "old_skill" in prev.read_text()


def test_improve_artifact_no_code_block_rejects(tmp_path):
    target = tmp_path / "script.py"
    original = "def main():\n    pass\n" + "# line\n" * 40
    target.write_text(original)

    no_fence_response = "설명만 있고 코드 블록 없음"

    with patch.object(loop.claude_api, "call", _mock_claude_call(no_fence_response)):
        meta = loop.improve_artifact(
            program_body="test",
            target=target,
            failed_items=[{"question": "q"}],
            output="x",
        )

    assert meta["skipped"] is True
    assert "추출 실패" in meta["skip_reason"]
    assert target.read_text() == original
