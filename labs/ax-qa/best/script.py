"""
ax-qa script v1 — fixture 디렉토리 → QA 리포트

계약 (program.md 참조):
- stdin으로 fixture 디렉토리 내용을 받음
  ('=== FILE: {name} ===' 마커로 파일 구분)
- stdout으로 QA 리포트 마크다운만 출력
- stderr로는 토큰 메타(JSON 1줄)만 출력 (claude.call_for_script가 자동 처리)
- 절대 파일 저장 금지
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from claude import call_for_script


PROMPT_TEMPLATE = """아래는 코드 변경 fixture 디렉토리의 내용이야.
파일은 `=== FILE: {{name}} ===` 마커로 구분되어 있어.

fixture 내용:
--------
{fixture}
--------

이 변경에 대해 QA 리포트를 작성해.
아래 템플릿을 정확히 따라서 마크다운으로 출력해.
절대 다른 말 없이 리포트만 출력.

# QA Report: {fixture_id}

## Summary
- verdict: pass / fail / warning 중 하나
- 한 줄 요약 (무엇이 어떻게 됐는지)

## Intent Check
META.md에 있는 커밋 의도와 실제 변경이 일치하는지 판단.
구체적 근거 1~3줄.

## Behavior Preservation
리팩토링/패치의 경우 기존 동작이 보존됐는지.
잠재적 regression 포인트가 있으면 구체적으로.

## Code Quality
가독성 개선 여부 (구체적 사례 — 함수명, 변경 블록 등).
중복 제거 / 네이밍 일관성 / 타입 안전성.

## Static Checks
lint: 추정 에러 수 또는 '정적 추정 불가'
type: 추정 타입 에러 수
test: 영향 테스트 범위 추정

## Issues
문제 없으면 'None'.
있으면 severity 태그:
- [CRITICAL] …
- [MAJOR] …
- [MINOR] …

## Owner Expectation
오너가 추가 수정 없이 이대로 넘어갈 수 있는가: Yes 또는 No
근거 1~2줄.

## 절대 규칙
- 위 섹션 구조 그대로
- verdict는 pass/fail/warning 중 하나만
- Owner Expectation은 Yes 또는 No 명시
- 리포트 외의 설명문 절대 출력 금지
- 한국어로 작성 (섹션 헤더는 영어 유지)
"""


def extract_fixture_id(fixture_text: str) -> str:
    """META.md에서 fixture id 추출. 없으면 'unknown'."""
    for line in fixture_text.splitlines():
        line = line.strip()
        if line.startswith("# Fixture:"):
            return line.replace("# Fixture:", "").strip()
    return "unknown"


def main():
    fixture = sys.stdin.read().strip()
    if not fixture:
        print("(빈 입력)", file=sys.stderr)
        sys.exit(1)

    fixture_id = extract_fixture_id(fixture)

    prompt = PROMPT_TEMPLATE.format(fixture=fixture, fixture_id=fixture_id)
    output, _ = call_for_script(prompt, timeout=180)

    print(output)


if __name__ == "__main__":
    main()
