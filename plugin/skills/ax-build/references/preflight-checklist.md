# Preflight 체크리스트

build 시작 전 확인 사항. 결과를 plan.md에 기록.

## 체크리스트

- [ ] **DS 컴포넌트 참조**: DESIGN_SYSTEM.md 컴포넌트 목록 확인. 목록에 없는 커스텀 컴포넌트는 사유 기록 필수
- [ ] **Anchor → Logic 순서**: 목업 안착(Anchor) 먼저, 기능(데이터/상태/이벤트) 나중. UI 뼈대가 잡힌 후 로직 연결
- [ ] **Token-only 스타일링**: DESIGN_SYSTEM.md 토큰만 사용. 색상/간격/폰트 직접 값 금지
- [ ] **i18n 리소스 경유**: 모든 UI 텍스트는 copy.ts 또는 i18n 시스템 경유. 컴포넌트에 직접 문자열 금지

## 왜 preflight인가

- 빌드 시작 후 발견하면 재작업 비용이 크다
- 체크리스트로 사전 확인하면 reviewer에서 걸리는 이슈 감소
- plan.md에 기록하면 reviewer가 확인 가능
