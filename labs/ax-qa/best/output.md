# QA Report: rubato:0065654

## Summary
- verdict: pass
- `buildTaskBody` / `intentSuccessToast` 헬퍼 추출로 task 생성 로직 중복을 제거한 순수 리팩토링. 동작 변화 없음.

## Intent Check
커밋 메시지의 "task 생성 로직 헬퍼 추출"과 실제 변경이 정확히 일치한다. `handleIntentAdd`와 `handleAdd` 두 곳에 중복되어 있던 `taskStatus` 결정 + `taskBody` 구성 + `start_date` 세팅 로직이 `buildTaskBody()`로, 두 곳의 삼항 toast 호출이 `intentSuccessToast()`로 통합되었다. META.md의 `+19/-30` 순감소 11줄도 diff와 일치.

## Behavior Preservation
기존 동작은 보존된다.
- `buildTaskBody`: `status` 결정식 (`reading` → `in_progress`, 외 → `todo`), `catalog_book_id` 주입, `reading`일 때만 `start_date` 추가 — 모두 before 로직과 동일.
- `intentSuccessToast`: `reading`이면 `intentReadingSuccess`, 그 외면 `intentWantToReadSuccess` — before의 삼항과 동일 (intent 타입이 `reading | want-to-read`이므로 else 분기 동치).
- PATCH 경로(`todo → in_progress`)는 `today` 지역 변수만 인라인되었고 값은 동일한 시점 계산(`new Date().toISOString().split("T")[0]`).
- 잠재 regression: `handleIntentAdd`와 `handleAdd`에서 `new Date()` 호출 시점이 약간 달라졌지만(각 호출부에서 즉시 계산) 의미 있는 차이 아님. `catalogBookId`에서 불필요한 괄호가 제거된 것도 타입상 무해.

## Code Quality
- 가독성 개선: `handleIntentAdd`의 "새 task 생성" 블록이 6줄 → 1줄로 축약, `handleAdd`의 intent 분기 블록도 6줄 → 1줄로 축약. 호출부의 인지 부하가 뚜렷이 감소.
- 중복 제거: 동일한 taskStatus/taskBody 빌드 로직 2곳, 동일한 성공 toast 삼항 2곳 → 각 1곳으로 통합.
- 네이밍 일관성: 헬퍼 파라미터 `i: NonNullable<SearchIntent>`는 타입 안전성을 강제해 호출부 `if (!intent) return` 가드 이후 그대로 넘겨도 안전. 다만 파라미터명 `i`는 `intent`가 더 명확했을 것 (MINOR).
- 타입 안전성: `NonNullable<SearchIntent>` 사용으로 null 유입을 컴파일 타임에 차단. 반환 타입은 구조 분해 대상이 `{ status, body }`로 추론되어 호출부에서 깔끔하게 쓰인다.

## Static Checks
- lint: 0 (정적 추정 — 기존 스타일 유지, unused import/var 없음)
- type: 0 (헬퍼 시그니처 명시, 호출부 구조 분해 타입 일치)
- test: `search/page.tsx`의 `handleIntentAdd` / `handleAdd` 흐름 — intent=reading, intent=want-to-read, todo→in_progress PATCH, 409 duplicate, 일반 서재 등록 5개 시나리오가 영향 범위. 단위 테스트보다 E2E/통합 테스트 대상.

## Issues
- [MINOR] `buildTaskBody` / `intentSuccessToast`의 파라미터명 `i`는 가독성 측면에서 `intent`가 더 적절. 스코프 내 상위 `intent` 변수와의 섀도잉을 피하려는 의도로 보이나, 헬퍼가 컴포넌트 내부 함수이므로 `currentIntent` 등이 더 명확.
- [MINOR] `buildTaskBody`는 `useCallback`/`useMemo`로 감싸지 않은 내부 함수라 매 렌더 재생성되지만, 외부로 전달되지 않으므로 성능 영향 없음. 현 상태 유지로 충분.

## Owner Expectation
- 이대로 넘어갈 수 있는가: Yes
- 근거: 동작 보존이 명확하고 중복 제거 효과가 실측 가능(-11줄). MINOR 이슈는 후속 개선으로도 충분.