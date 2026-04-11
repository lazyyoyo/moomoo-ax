"""
problem-frame script.py — seed.md + jtbd.md → problem-frame.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_lib"))
from claude import call_for_script


def generate(context: str) -> str:
    prompt = f"""아래 시드 + JTBD 문서를 분석하여 Problem Framing 문서를 생성해.

## 입력 문서

{context}

## 출력 형식 (마크다운, 이 구조 정확히 따를 것)

## HMW Questions (우선순위순)
1. 어떻게 하면 [구체적 문제]를 해결할 수 있을까?
2. ...
(3~5개)

## Solution Candidates

| ID | 솔루션 | HMW# | Impact | Feasibility | 판정 |
|----|--------|-------|--------|-------------|------|
| S1 | ... | 1 | H | H | ✅ 진행 |
| S2 | ... | 1 | H | M | ⏳ 후순위 |
(최소 5개, Impact/Feasibility는 H/M/L)

## Selected Direction
- 핵심 솔루션: S?
- 이유: ...
- 핵심 가정: ...

## 규칙
- JTBD의 Underserved Needs를 HMW에 반영
- 서론/요약 없이 바로 본문"""

    output, _ = call_for_script(prompt)
    return output


if __name__ == "__main__":
    print(generate(sys.stdin.read().strip()))
