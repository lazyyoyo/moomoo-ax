"""
ax-implement script v1 — fixture 디렉토리 → 구현 코드 산출물

계약 (program.md 참조):
- stdin 으로 fixture 디렉토리 내용을 받음 ('=== FILE: {rel} ===' 마커)
- plugin/skills/ax-implement/SKILL.md 를 시스템 지식으로 주입
- stdout 으로 Implementation 마크다운만 출력
- stderr 로는 토큰 메타(JSON 1줄)만 출력 (claude.call_for_script 자동 처리)
- 절대 파일 저장 금지
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from claude import call_for_script

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_PATH = REPO_ROOT / "plugin" / "skills" / "ax-implement" / "SKILL.md"


PROMPT_TEMPLATE = """너는 ax-implement — team-ax 파이프라인의 implement 단계다.
아래 team-ax implement skill 지침을 따라 주어진 fixture 에 대한 구현 코드를 작성한다.

===== SKILL 지침 (system knowledge) =====
{skill}
===== SKILL 지침 끝 =====

아래는 구현 대상 fixture 디렉토리의 내용이다.
파일은 `=== FILE: {{rel}} ===` 마커로 구분되어 있다.

fixture 내용:
--------
{fixture}
--------

## 과업

1. `SPEC.md` 의 "완료 기준" 을 **빠짐없이** 구현한다.
2. `base/**` 의 기존 코드 스타일 / 네이밍 / 타입 패턴을 따른다.
3. 생성할 파일의 위치/이름은 SPEC 이 제시한 경로를 사용한다.
4. SPEC 에 명시되지 않은 추가 기능/리팩터/테스트는 만들지 않는다.

## 출력 계약 (program.md 와 일치 — 엄격 준수)

아래 구조만 출력. 다른 말 금지.

```
# Implementation: {fixture_id}

## Summary
- verdict: ready / partial / failed 중 하나
- 한 줄 요약 (무엇을 구현했는지)
- 생성 파일 목록 (경로만)

## Files

### {{path/to/file.ext}}
```{{lang}}
{{파일 전체 내용}}
```

(필요 시 여러 ### 반복)

## Self-check
- spec 완료 기준 매핑: 1/2/3/... 각 항목 "충족 (근거)"
- 타입 안전성: OK / 이슈
- 에지 케이스 처리: 열거
- 토큰 효율: 설명 없음 여부
```

## 절대 규칙
- stdout 만 사용, 위 구조 그대로
- verdict 는 ready / partial / failed 만
- 각 파일 코드 블록은 **파일 전체** (부분 금지)
- 산출물 외 설명문/서론/결론/메타 멘트 금지
- 한국어 (섹션 헤더는 영어 유지, 코드 주석은 상황 맞게)
- 코드 블록 언어 태그 정확히 (`typescript` 또는 `ts`)
"""


def extract_fixture_id(fixture_text: str) -> str:
    """META.md 에서 fixture_id 추출. 없으면 'unknown'."""
    in_meta = False
    for line in fixture_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("=== FILE: META.md"):
            in_meta = True
            continue
        if in_meta:
            if stripped.startswith("=== FILE:"):
                break
            # 첫 줄이 '# Fixture: ...' 또는 'fixture_id: ...'
            if stripped.startswith("# Fixture:"):
                return stripped.replace("# Fixture:", "").strip()
            if stripped.lower().startswith("fixture_id:"):
                return stripped.split(":", 1)[1].strip()
    return "unknown"


def load_skill() -> str:
    if not SKILL_PATH.exists():
        print(f"SKILL.md 없음: {SKILL_PATH}", file=sys.stderr)
        sys.exit(1)
    return SKILL_PATH.read_text().strip()


def main():
    fixture = sys.stdin.read().strip()
    if not fixture:
        print("(빈 입력)", file=sys.stderr)
        sys.exit(1)

    fixture_id = extract_fixture_id(fixture)
    skill = load_skill()

    prompt = PROMPT_TEMPLATE.format(
        skill=skill,
        fixture=fixture,
        fixture_id=fixture_id,
    )
    output, _ = call_for_script(prompt, timeout=300)

    print(output)


if __name__ == "__main__":
    main()
