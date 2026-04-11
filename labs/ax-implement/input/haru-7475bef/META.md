# Fixture: haru:7475bef

## 출처
- project: haru (journal)
- 원본 커밋: `7475bef feat(dev): @날짜 파서 구현 + 테스트 16건`
- 커밋일: 2026-04-02
- 경로: `~/hq/projects/journal/`

## 선택 이유
- 순수 추가 (리팩터/수정 아님) — implement stage 평가 대상에 적합
- 구현 범위 작고 단일 파일 (parser 98줄) + 테스트 16건 — oracle 명확
- spec 문서 (`dev/docs/specs/date-natural-input.md`) 있음 — 요구사항 복원 가능
- 파싱 로직이 날짜/요일/자연어 혼합이라 rubric 구분력 있음

## 변경 요약
- **신규**: `dev/src/lib/parse-date-tag.ts` (파서 본체, 98줄)
- **신규**: `dev/src/lib/__tests__/parse-date-tag.test.ts` (테스트 16건, 116줄)

## fixture 내 구성
- `SPEC.md` — `dev/docs/specs/date-natural-input.md` 핵심 발췌 + 완료 기준
- `base/parse-hashtag.ts` — 동일 패턴의 기존 파서 (스타일 참고)
- `base/date-utils.ts` — 요일 배열 / 날짜 유틸 (상수 참고)

## 기대 산출물
- `dev/src/lib/parse-date-tag.ts` 한 개 파일. 테스트 파일은 이 fixture 에서는 요구하지 않음 (v0.2 는 구현 단일 파일만 평가).

## rubric 구분력 포인트
- 요일 파싱의 "오늘이면 다음 주" 규칙 — 놓치기 쉬움
- 유효하지 않은 날짜 (@2/30) null 처리
- 이미 지난 숫자 날짜 → 내년
- cleanText 에서 양쪽/중복 공백 정리
- 4개 패턴 그룹 (상대/요일/다음주요일/숫자) 모두 지원
