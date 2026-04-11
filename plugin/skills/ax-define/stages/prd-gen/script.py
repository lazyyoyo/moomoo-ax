"""
prd-gen script.py — seed + jtbd + problem-frame + scope → prd.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_lib"))
from claude import call_for_script


def generate(context: str) -> str:
    prompt = f"""아래 문서들을 종합하여 PRD(Product Requirements Document)를 생성해.

## 입력 문서

{context}

## 출력 형식 (마크다운, 이 구조 정확히 따를 것)

## 1. Overview
- 제품명 / 한줄 설명
- 이 PRD가 다루는 범위 (v1)

## 2. Background & Problem
- Core Job Statement (jtbd에서)
- 선택된 HMW + 핵심 가정 (problem-frame에서)

## 3. Goals & Success Metrics
- 목표 1: ... → 지표: ...
- 목표 2: ... → 지표: ...
- Non-goal: ...

## 4. User Stories
- AS A [사용자], I WANT [행동], SO THAT [가치]

## 5. Functional Requirements

| ID | 요구사항 | 우선순위 | 수용 기준 |
|----|----------|----------|----------|
| FR-01 | ... | Must | ... |

## 6. Technical Constraints
- 스택: ...
- API 의존성: ...

## 7. UI/UX Direction
- 핵심 플로우 (scope에서)

## 8. Out of Scope
- (scope에서)

## 9. Open Questions
- 아직 결정 안 된 것들

## 규칙
- 앞 단계 문서 내용을 종합. 새로 지어내지 마.
- 개발자/에이전트가 바로 구현 가능한 구체성
- 서론 없이 바로 본문"""

    output, _ = call_for_script(prompt, timeout=180)
    return output


if __name__ == "__main__":
    print(generate(sys.stdin.read().strip()))
