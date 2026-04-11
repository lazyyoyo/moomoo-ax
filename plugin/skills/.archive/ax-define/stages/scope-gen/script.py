"""
scope-gen script.py — problem-frame.md → scope.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_lib"))
from claude import call_for_script


def generate(context: str) -> str:
    prompt = f"""아래 Problem Framing 문서를 분석하여 SLC 기반 스코프 문서를 생성해.

## 입력 문서

{context}

## 출력 형식 (마크다운, 이 구조 정확히 따를 것)

## SLC Checklist
- **Simple**: 혼자서 2주 스프린트에 구현 가능한가?
- **Lovable**: 이것만으로 "오 좋다"가 나오는가?
- **Complete**: 반쪽짜리가 아니라 끝까지 완결되는가?

## v1 Scope

| 기능 | S | L | C | 버전 |
|------|---|---|---|------|
| ... | ✅/❌ | ✅/❌ | ✅/❌ | v1/v2/v3 |

## Out of Scope
- (명시적 제외 항목)

## 핵심 사용자 플로우 (v1)
1. ... → 2. ... → 3. ...

## 규칙
- Selected Direction의 솔루션을 기능으로 분해
- v1에는 S+L+C 모두 ✅인 것만 포함
- 서론/요약 없이 바로 본문"""

    output, _ = call_for_script(prompt)
    return output


if __name__ == "__main__":
    print(generate(sys.stdin.read().strip()))
