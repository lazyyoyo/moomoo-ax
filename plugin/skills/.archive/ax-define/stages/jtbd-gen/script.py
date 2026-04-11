"""
jtbd-gen script.py — seed.md → jtbd.md (2-pass: extract → generate)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_lib"))
from claude import call_for_script


MIN_SEED_LENGTH = 30


def extract(seed: str) -> str:
    """1단계: 시드에서 JTBD 요소를 원문 인용으로 추출."""
    prompt = f"""아래 시드 문서에서 JTBD 분석에 필요한 요소를 추출해.
반드시 시드 원문을 그대로 인용해. 시드에 해당 정보가 없으면 "없음"이라고만 적어.
절대 추론하거나 보충하지 마. 원문 그대로만.

<seed>
{seed}
</seed>

아래 형식으로 출력해:

사용자: "시드 원문 인용"
상황: "시드 원문 인용"
동기: "시드 원문 인용"
기대결과: "시드 원문 인용"
기존대안1: "시드 원문 인용"
기존대안1_장점: "시드 원문 인용"
기존대안1_단점: "시드 원문 인용"
기존대안2: "시드 원문 인용"
기존대안2_장점: "시드 원문 인용"
기존대안2_단점: "시드 원문 인용"
불만: "시드 원문 인용"
핵심키워드: 시드에서 반복되거나 강조된 단어/표현 나열"""

    raw, _ = call_for_script(prompt, timeout=60)
    return raw.strip()


def generate(seed: str) -> str:
    if len(seed.strip()) < MIN_SEED_LENGTH:
        print(f"시드가 너무 짧음 ({len(seed.strip())}자). 최소 {MIN_SEED_LENGTH}자 필요.", file=sys.stderr)
        sys.exit(1)

    # 1단계: 추출
    extraction = extract(seed)

    # 2단계: 추출 결과 + 시드 원문 → JTBD 문서 생성
    prompt = f"""아래 "추출 결과"와 "시드 원문"을 사용해 JTBD 문서를 생성해.

## 절대 규칙 (하나라도 위반하면 실패)
1. 시드 원문에 존재하는 단어·표현·고유명사만 사용해.
2. 시드에 없는 도구명, 서비스명, 기능명, 수치를 절대 추가하지 마.
3. Competing Solutions는 시드에 언급된 대안만 사용해. 시드에 대안이 1개뿐이면 "현재 방식(수작업/미사용)"을 두 번째로 써. 구체적 도구명을 지어내지 마.
4. 모든 내용은 추출 결과의 인용문에서만 가져와. "없음"인 항목은 "시드에서 확인 불가"로 적어.
5. Job Map 각 단계의 설명에 시드 원문 키워드를 반드시 포함해.

## 추출 결과
{extraction}

## 시드 원문 (대조용)
<seed>
{seed}
</seed>

## 출력 형식 — 아래 마크다운 구조를 정확히 따라. 다른 텍스트 추가 금지.

## Core Job Statement
When [추출된 상황을 시드 표현 그대로], I want to [추출된 동기를 시드 표현 그대로], so I can [추출된 기대결과를 시드 표현 그대로].

## Job Map
1. **정의하기**: (시드 키워드 사용)
2. **찾기**: (시드 키워드 사용)
3. **준비하기**: (시드 키워드 사용)
4. **실행하기**: (시드 키워드 사용)
5. **확인하기**: (시드 키워드 사용)
6. **수정하기**: (시드 키워드 사용)

## Competing Solutions

| 대안 | 잘하는 점 | 못하는 점 |
|------|----------|----------|
| (시드에 언급된 대안만) | (시드 원문 기반) | (시드 원문 기반) |

## Underserved Needs
- (시드에서 직접 도출되는 높은 중요도 + 낮은 만족도 니즈만)

## 마지막 점검
출력 완료 전에 아래를 확인하고, 위반 시 해당 부분을 즉시 수정해:
- [ ] 모든 고유명사가 시드에 존재하는가?
- [ ] Competing Solutions의 대안명이 시드에 있는가?
- [ ] 시드에 없는 수치나 도구명이 포함되지 않았는가?"""

    raw, meta = call_for_script(prompt, timeout=120)

    # 후처리: 마지막 점검 체크리스트 제거
    output = raw.strip()
    output = re.sub(r"## 마지막 점검.*", "", output, flags=re.DOTALL).strip()

    # Core Job Statement 앞의 불필요한 텍스트 제거
    match = re.search(r"## Core Job Statement", output)
    if match:
        output = output[match.start():]

    return output


if __name__ == "__main__":
    print(generate(sys.stdin.read().strip()))
