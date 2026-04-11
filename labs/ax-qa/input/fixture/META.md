# Fixture: rubato:0065654

## 출처

- **프로젝트**: rubato (`~/hq/projects/rubato`)
- **커밋**: `0065654543e1443ae56eb734208c398d0ce0889d99`
- **메시지**: `refactor: search intent — task 생성 로직 헬퍼 추출 (buildTaskBody, intentSuccessToast)`
- **날짜**: 2026-04-10 (어제, v1.5.3 배포 작업 중)

## 포함 파일

- `before.tsx` — 커밋 직전 상태 (`git show 0065654^:dev/src/app/(protected)/search/page.tsx`)
- `after.tsx` — 커밋 적용 후 상태 (`git show 0065654:dev/src/app/(protected)/search/page.tsx`)
- `diff.patch` — 커밋 전체 diff (`git show 0065654`)

## 변경 요약

- 대상 파일: `dev/src/app/(protected)/search/page.tsx` (1 파일만)
- diff: `+19 / -30` (순감소 11줄)
- 성격: **리팩토링** — 동작 변경 없이 가독성/중복 제거
- 주요 변경:
  - `buildTaskBody()` 헬퍼 함수 추출
  - `intentSuccessToast()` 헬퍼 함수 추출
  - 중복된 task 생성 로직을 헬퍼로 통합

## ax-qa fixture로 선택한 이유

1. **통제 가능 크기**: 1 파일, 리팩토링 성격이라 후속 영향 범위 좁음
2. **qa의 classical 축이 전부 걸림**:
   - 기존 동작 보존 여부 (리팩토링의 핵심)
   - 가독성 개선 여부
   - 타입 안전성 유지
   - 네이밍 일관성
   - 중복 제거 효과
3. **정량/정성 혼합**: lint/type 에러(정량) + "리팩토링 의도 달성"(정성)
4. **재현성**: 커밋 해시 고정 → 언제든 같은 입력으로 재실험 가능

## v0.1 levelup loop 대상

- **stage**: `ax-qa`
- **fixture_id**: `rubato:0065654`
- **목적**: engine smoke test — 이 fixture를 input으로 주고, `labs/ax-qa/script.py`가 qa 리포트를 생성하고, `rubric.yml`이 점수를 매긴다
- **v0.1 목표**: 1 cycle 완주 + Supabase 레코드 + 대시보드 표시. "개선이 실제로 일어나는가"는 v0.2 목표.
