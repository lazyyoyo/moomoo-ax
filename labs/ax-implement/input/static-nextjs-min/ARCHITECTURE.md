# ARCHITECTURE

## 기술 스택

- 프레임워크: `next` (App Router, v15)
- 언어: `typescript` (strict)
- 런타임: `react` / `react-dom` (v19)
- 린트: `eslint` + `eslint-config-next`
- 유닛 테스트: `vitest` + `jsdom`

## 디렉토리

```
src/
├── app/          # Next.js App Router
├── components/   # UI 컴포넌트
└── i18n/
    └── copy.ts   # 모든 UI 문자열
```

## 원칙

- 텍스트는 `src/i18n/copy.ts` 경유. 컴포넌트에 직접 문자열 금지
- 컴포넌트는 `src/components/` 하위. `DESIGN_SYSTEM.md` 의 variant 규칙 준수
- 신규 라이브러리 도입 시 이 문서의 "기술 스택" 에 먼저 기록 후 설치
