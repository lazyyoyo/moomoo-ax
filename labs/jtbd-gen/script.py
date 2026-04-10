"""
jtbd-gen script.py — seed.md → jtbd.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from claude import call_for_script


def generate(seed: str) -> str:
    prompt = f"""아래 시드 문서를 분석하여 JTBD(Jobs To Be Done) 문서를 생성해.

## 시드 문서

{seed}

## 출력 형식 (마크다운, 이 구조 정확히 따를 것)

## Core Job Statement
When [상황], I want to [동기], so I can [기대 결과].

## Job Map
1. **정의하기**: (사용자가 목표를 정의하는 단계)
2. **찾기**: (필요한 정보/도구를 찾는 단계)
3. **준비하기**: (실행 준비 단계)
4. **실행하기**: (핵심 작업 수행)
5. **확인하기**: (결과 확인)
6. **수정하기**: (필요 시 조정)

## Competing Solutions

| 대안 | 잘하는 점 | 못하는 점 |
|------|----------|----------|
| ... | ... | ... |

(최소 2개)

## Underserved Needs
- (높은 중요도 + 낮은 만족도인 니즈들)

## 규칙
- 시드에 없는 정보를 지어내지 마. 합리적 추론만.
- 서론/요약 없이 바로 본문."""

    output, _ = call_for_script(prompt)
    return output


if __name__ == "__main__":
    print(generate(sys.stdin.read().strip()))
