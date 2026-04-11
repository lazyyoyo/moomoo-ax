---
improve_target: script.py
---

# ax-qa — 오너 규칙

## 목적

team-ax 파이프라인의 qa 단계. 주어진 코드 변경(fixture)에 대해 **품질 리포트**를 자동 생성한다.

team-product에서 qa가 병목이었던 이유:
- design/implement 이후 자잘한 버그가 많아 오너가 일일이 고침
- qa 리포트가 나와도 "오너 기대치"와 괴리가 있어 참고 수준에 그침

ax-qa의 지향점:
- **오너가 리포트를 보고 추가 작업 없이 넘어갈 수 있는** 품질의 qa를 자동 생성
- 정량 체크(lint/type/test)와 정성 평가(의도 달성/가독성) 모두 포함
- 리포트 형식은 **오너가 빠르게 훑을 수 있는** 고정 포맷

## 입력 계약

`labs/ax-qa/input/fixture/` 디렉토리를 stdin으로 받는다. 최소 구성:

- `before.*` — 변경 전 코드
- `after.*` — 변경 후 코드
- `diff.patch` — 변경 사항 (git show 형식)
- `META.md` — fixture 메타데이터 (출처 커밋, 변경 요약, 선택 이유)

## 출력 계약

stdout으로만 출력한다. 아래 섹션을 **순서대로** 포함한 markdown 리포트.

```
# QA Report: {fixture_id}

## Summary
- verdict: pass / fail / warning
- 한 줄 요약

## Intent Check
- 커밋 메시지/META.md의 의도 대비 실제 변경이 일치하는가
- 불일치가 있다면 구체적으로

## Behavior Preservation
- 리팩토링/패치의 경우 기존 동작 보존 여부
- 잠재적 regression risk 포인트

## Code Quality
- 가독성 개선 여부 (구체적 사례)
- 중복 제거 / 네이밍 일관성
- 타입 안전성

## Static Checks (if applicable)
- lint: 추정 에러 수 (실제 실행이 아닌 코드 정적 추론)
- type: 추정 타입 에러 수
- test: 영향 테스트 추정

## Issues
- [CRITICAL] … (있으면)
- [MAJOR] …
- [MINOR] …

## Owner Expectation
- 오너가 추가 손댈 것 없이 넘어갈 수 있는가: Yes / No
- No라면 어떤 수정이 필요한가
```

## 절대 규칙 (위반 시 무효)

1. **stdout 출력만 허용**. 파일 저장(open/write/Path.write_text 등) 금지.
2. **stdin으로 입력 받기**. argv나 파일 읽기로 input 받지 말 것.
3. **고정 섹션 구조 준수**. 위 템플릿의 섹션 순서/이름을 바꾸지 말 것.
4. **verdict는 pass/fail/warning 세 값만**. 다른 값 금지.
5. **"Owner Expectation" 섹션의 Yes/No**는 반드시 명시적으로 출력.
6. **토큰 절약**: 산출물 자체 이외의 설명(예: "리포트를 생성했습니다") 출력 금지.

## 개선 가능 영역 (루프가 건드려도 되는 부분)

- 프롬프트 문구 / 호출 방식
- 입력 parsing 로직
- 섹션별 강조/상세도
- static check 추정 정확도
- issue severity 판정 기준

## 불변 영역 (루프가 건드리면 안 되는 부분)

- 출력 섹션 구조 (위 템플릿)
- verdict 3값 제약
- stdin/stdout 계약
- fixture 입력 디렉토리 구조
