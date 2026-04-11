---
improve_target: ../../plugin/skills/ax-implement/SKILL.md
---

# ax-implement — 오너 규칙

## 목적

team-ax 파이프라인의 implement 단계. 주어진 spec + base 컨텍스트(fixture)에 대해
**구현 코드**를 자동 생성한다.

team-product 에서 implement 가 병목이었던 이유:
- plan/design 단계는 그럭저럭 돌아갔지만 실제 구현에서 오너가 일일이 고쳐야 했음
- 산출물이 "컴파일은 되지만 스펙 완료 기준을 일부만 충족" 인 경우가 가장 많음
- subagent 오케스트레이션 (planner/executor/reviewer) 의 자연어 지시가 자의적으로 해석됨

ax-implement 의 지향점:
- **오너가 산출물을 그대로 커밋해도 될 품질** 의 코드를 자동 생성
- spec 완료 기준 을 **하나도 빼지 않고** 구현
- 타입 안전 + 에지 케이스 + 토큰 효율 모두 만족
- 산출물 형식은 **오너가 빠르게 훑고 그대로 붙일 수 있는** 고정 포맷

## (C') Progressive Codification 원칙

이 stage 의 improve_target 은 `plugin/skills/ax-implement/SKILL.md` — team-product seed 포팅본이다.
levelup loop 는 이 SKILL.md 를 iteration 간 개선한다. 자연어 규칙 중 deterministic 한 것은
script 추출 후보 로 식별 (v0.2 는 식별만, 자동 추출은 v0.3+).

## 입력 계약

`labs/ax-implement/input/{fixture_id}/` 디렉토리를 stdin 으로 받는다. 파일은
`=== FILE: {rel} ===` 마커로 구분되며, 최소 구성:

- `SPEC.md` — 구현해야 할 기능의 스펙 (완료 기준 포함)
- `META.md` — fixture 메타데이터 (fixture_id, 출처 커밋, 선택 이유)
- `base/**` — 참조용 기존 코드. 순수 추가 fixture 이므로 구현해야 할 파일은 base/ 에 없다.

## 출력 계약

stdout 으로만 출력한다. 아래 구조를 **순서대로** 포함한 마크다운.

```
# Implementation: {fixture_id}

## Summary
- verdict: ready / partial / failed
- 한 줄 요약 (무엇을 구현했는지)
- 생성 파일 목록 (경로만)

## Files

### {path/to/file.ext}
```{lang}
{파일 전체 내용}
```

(필요 시 여러 ### 반복)

## Self-check
- spec 완료 기준 N/총 충족 (각 항목 간단히 매핑)
- 타입 안전성: OK / 이슈
- 에지 케이스 처리: 열거
- 토큰 효율: 불필요한 설명 없음
```

## 절대 규칙 (위반 시 무효)

1. **stdout 출력만 허용**. 파일 저장 (open/write 등) 금지.
2. **stdin 으로 입력 받기**. argv 나 파일 읽기로 input 받지 말 것.
3. **고정 섹션 구조 준수**. 위 템플릿의 섹션 순서/이름/개수를 바꾸지 말 것.
4. **verdict 는 ready/partial/failed 세 값만**. 다른 값 금지.
5. **각 파일 코드 블록은 파일 전체**. 부분/일부만 출력 금지 — loop.py 가 전체 교체를 가정.
6. **spec 완료 기준 전부 구현**. 미구현 항목이 있으면 verdict=partial + Self-check 에 명시.
7. **산출물 외의 설명문 금지** (예: "구현을 생성했습니다", "다음은 분석입니다"). 토큰 낭비.
8. **한국어로 작성**. 섹션 헤더는 영어 유지. 코드 주석은 상황 맞게.

## 개선 가능 영역 (루프가 건드려도 되는 부분)

- SKILL.md 문장 강조 / 지시 정제 / 중복 압축
- 자연어 체크리스트 중 deterministic 한 것을 script 추출 후보 로 식별 (주석)
- 토큰 낭비 구간 감지 — 같은 지시가 여러 번 반복되면 통합
- fixture 입력 parsing 로직 (script.py 부분)

## 불변 영역 (루프가 건드리면 안 되는 부분)

- 출력 섹션 구조 (위 템플릿)
- verdict 3값 제약 (ready/partial/failed)
- stdin/stdout 계약
- fixture 입력 디렉토리 구조
- 절대 규칙 1~8
