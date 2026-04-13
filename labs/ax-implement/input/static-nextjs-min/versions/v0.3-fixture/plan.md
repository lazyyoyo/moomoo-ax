# v0.3-fixture Implementation Plan — static-nextjs-min

> 생성: seed 커밋
> 대상: `static-nextjs-min` fixture
> 목표: ax-implement end-to-end 검증용 최소 UI 태스크 3개

## 스코프

DESIGN_SYSTEM 의 `Button` 컴포넌트 신규 도입 + 유닛 테스트 + 홈 페이지 시연.

## Preflight 체크

- [ ] DESIGN_SYSTEM.md 토큰 목록 확인
- [ ] `src/i18n/copy.ts` 경유 (UI 텍스트 하드코딩 금지)
- [ ] token-only 스타일링

## 구현 계획

### T-001. Button 컴포넌트 신규 (agent: design-engineer)

- spec: `DESIGN_SYSTEM.md` #컴포넌트-목록
- 파일:
  - `src/components/Button.tsx`
- 설명: `primary` / `secondary` 두 variant. `children`, `onClick`, `variant`, `disabled` prop. DESIGN_SYSTEM 토큰만 사용 (inline style 또는 CSS module). 접근성: 네이티브 `<button>` 기반
- 검증: 컴포넌트가 두 variant 렌더링되고 토큰만 사용하는지
- AC:
  1. `variant="primary"` 와 `variant="secondary"` 둘 다 지원
  2. 하드코딩 컬러 값 없음 (`var(--color-*)` 만)
  3. `disabled` prop 반영

### T-002. Button 유닛 테스트 (agent: design-engineer)

- spec: `DESIGN_SYSTEM.md` #컴포넌트-목록
- 파일:
  - `src/components/Button.test.tsx`
- 설명: vitest + React Testing Library (없으면 `@testing-library/react` 추가 — ARCHITECTURE.md 먼저 갱신). 두 variant 렌더링, `onClick` 호출, `disabled` 동작 검증
- 검증: `npm test` 통과
- AC:
  1. 2 variant 테스트 케이스
  2. click / disabled 케이스
  3. `npm test` exit 0

### T-003. 홈 페이지에 Button 시연 (agent: design-engineer)

- spec: (fixture seed `src/app/page.tsx`)
- 파일:
  - `src/app/page.tsx` 수정
  - `src/i18n/copy.ts` 에 버튼 라벨 추가
- 설명: 홈 페이지에 primary / secondary 버튼 각 1개씩 배치. 라벨은 copy 경유
- 검증: `npm run build` 통과 + 페이지에 버튼이 렌더링되는 구조
- AC:
  1. `page.tsx` 에서 `Button` import + 2개 렌더
  2. 라벨은 `copy.home.*` 에서 로드
  3. `npm run lint` + `npm run typecheck` + `npm run build` 모두 pass

## 이슈 로그

(없음)
