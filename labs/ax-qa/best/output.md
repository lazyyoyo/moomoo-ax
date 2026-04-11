# QA Report: rubato:0065654

## Summary
- verdict: pass
- `buildTaskBody`와 `intentSuccessToast` 헬퍼 추출로 task 생성/토스트 중복 로직을 성공적으로 통합한 리팩토링.

## Intent Check
커밋 메시지의 의도(`buildTaskBody`, `intentSuccessToast` 헬퍼 추출)와 실제 변경이 정확히 일치한다. `handleIntentAdd`와 `handleAdd` 두 곳에 중복되어 있던 task body 조립 로직(status 분기 + start_date 조건부 추가)이 `buildTaskBody`로, 두 곳의 동일한 토스트 분기가 `intentSuccessToast`로 추출됐다. 부수적으로 불필요한 주석 제거와 `(catalogBookId as string)` 괄호 정리도 같이 들어갔다.

## Behavior Preservation
동작은 완전히 보존된다.
- `buildTaskBody`는 기존 인라인 로직과 동일하게 `reading → in_progress + start_date`, `want-to-read → todo`를 반환한다.
- `intentSuccessToast`도 기존 삼항 분기와 동일한 메시지를 돌려준다.
- 잠재적 regression 포인트: `handleIntentAdd`의 PATCH 분기에서 `today` 변수 제거 후 `new Date().toISOString().split("T")[0]`를 인라인 호출로 바꿨는데, PATCH 경로는 한 번만 계산되므로 기능적 차이는 없다. 동일 핸들러 내에서 PATCH와 POST 경로가 분기되므로 날짜가 두 번 계산되는 케이스도 없다.

## Code Quality
가독성이 명확히 개선됐다.
- `handleIntentAdd`의 새 task 생성 블록이 6줄 → 1줄로 축약됐고, `handleAdd`의 intent 분기도 6줄 → 1줄로 축약됐다.
- 중복 제거: task body 조립 2곳, 성공 토스트 분기 2곳 → 각각 단일 헬퍼로 통합.
- 네이밍: `buildTaskBody`, `intentSuccessToast`는 역할이 분명하다. 파라미터 `i: NonNullable<SearchIntent>`는 짧지만 스코프가 좁아 허용 가능.
- 타입 안전성: `NonNullable<SearchIntent>`로 null 케이스를 타입 레벨에서 차단, 호출처가 이미 `if (!intent) return` / `if (intent && catalogBookId)`로 가드하므로 안전.
- `catalog_book_id: catalogBookId as string` 괄호 제거는 순수 스타일 정리.

## Static Checks
- lint: 0 (정적 추정)
- type: 0 (정적 추정 — `NonNullable` 가드 정확)
- test: search 페이지 intent 플로우 E2E 범위 — reading/want-to-read intent로 신규 책 추가, 기존 todo→in_progress 전환, 중복 409 처리 경로

## Issues
None.

## Owner Expectation
오너가 추가 수정 없이 이대로 넘어갈 수 있는가: Yes
순수 리팩토링이고 동작 보존이 명확하며, 커밋 의도와 구현이 정확히 일치한다. 순 -11줄 감소로 의도한 가독성 개선 효과도 달성됐다.