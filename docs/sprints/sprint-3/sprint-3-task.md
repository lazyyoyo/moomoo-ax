# sprint-3 태스크

## T0. 기존 자산 이식

team-design/team-product에서 references 복사 + ax 구조에 맞게 조정.

- [ ] `references/design-principles.md` — slop 방지 + 안티패턴
- [ ] `references/font-catalog.md` + `korean-fonts.md` + `font-pairing-kr.md`
- [ ] `references/trends-2026.md`
- [ ] `references/domain-checklists.md`
- [ ] `references/layout-patterns.md`
- [ ] `references/animation-recipes.md`
- [ ] `references/reference-readme-template.md` — 부분 태깅 + Story 매핑 포맷 추가

## T1. ax-design SKILL.md 작성

8단계 플로우 정의.

- [ ] 1단계: DS 토큰 확인 절차
- [ ] 2단계: 오너 인터뷰 항목 (레퍼런스 + 접근 방식, 주관적 질문 금지)
- [ ] 3단계: UX 플로우 설계 연동 (ux-designer 호출)
- [ ] 4단계: Story별 디자인 분기 판정 로직 + scope.md 기록
- [ ] 5단계: 컴포넌트 개발 + 오너 확정 + DS 등록 프로토콜
- [ ] 6단계: 전체 구성 규칙 (확정 컴포넌트만 사용)
- [ ] 7단계: 게이트 호출 순서 (①DS 린트 → ②레이아웃 → ③스크린샷 → ④Judge)
- [ ] 8단계: 오너 프리뷰 + 피드백 분류
- [ ] 오너 리젝 시 재작업 프로토콜 (5단계 max 2회, 8단계 max 3회)
- [ ] 실행 위치 명시 (version/vX.Y.Z 브랜치)
- [ ] 병렬성 규칙 (디자인 불필요 Story는 바로 worktree에서 빌드)
- [ ] 가드레일

## T2. 에이전트 작성

- [ ] `agents/ux-designer.md` — team-product에서 이식 + 컴포넌트 목록 산출 추가
- [ ] `agents/design-builder.md` — DS 위에서만 작업 + 확정 컴포넌트만 사용 제약

## T3. 게이트 스크립트

- [ ] `scripts/ds-completeness-check.sh` — DS 토큰 체크리스트 자동 검증
- [ ] `scripts/design-gate.sh` — 하드코딩 탐지 + 레이아웃 규칙 체크
- [ ] 게이트 실패 → 재작업 지시서 자동 생성 로직

## T4. 동적 체크리스트 (CheckEval)

- [ ] `references/checklist-generator.md` — UX 기반 Yes/No 체크리스트 생성 규칙
- [ ] Judge 게이트 ④의 체크리스트 포맷 정의
- [ ] 고정 루브릭 (항상 적용) + 동적 루브릭 (기능별 자동 생성) 분리

## T5. hooks 설정

- [ ] `UserPromptSubmit` 훅 — DS 토큰/규칙 자동 주입
- [ ] `PostToolUse` 훅 — Write/Edit 후 DS 린트 자동 실행

## T6. 템플릿

- [ ] `templates/design-brief.md` — 오너 인터뷰 결과 포맷
- [ ] `templates/ds-preview-page/` — DS 프리뷰 페이지 템플릿 (sasasa 수준 이상)
- [ ] `templates/design-review.md` — 게이트 결과 + 오너 피드백 이력 포맷

## T7. 릴리즈

- [ ] plugin.json + marketplace.json 버전 bump (0.2.0 → 0.3.0)
- [ ] BACKLOG.md done 섹션에 sprint-3 기록
- [ ] 커밋 + PR + 태그

## T8. 도그푸딩

대상: rubato 또는 yoyowiki. 디자인 필요 Story + 불필요 Story 혼합 버전으로 실행.

### 검증 기준

**DS 토큰 (1단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| D1 | DS 토큰 확인/생성 | DESIGN_SYSTEM.md에 색상/공간/타이포/기본 컴포넌트 존재 |
| D2 | 브랜드 톤 유지 | brand/와 DS 토큰 정합 |

**오너 인터뷰 (2단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| I1 | 주관적 질문 없음 | "느낌/무드" 질문 미발생 |
| I2 | 레퍼런스 부분 태깅 | README.md에 "참고할 포인트" + Story 매핑 존재 (레퍼런스 있을 때) |
| I3 | 레퍼런스 없이 진행 가능 | 레퍼런스 없다고 답하면 정상 진행 |

**Story별 분기 (4단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| S1 | Story별 디자인 판정 | scope.md §Story Map에 각 Story의 디자인 필요성 기록 |
| S2 | 병렬 빌드 | 디자인 불필요 Story가 worktree에서 바로 빌드 가능 |
| S3 | 억지 디자인 없음 | 조합 가능 Story에 새 시안 생성 안 함 |

**컴포넌트 확정 (5단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| C1 | 개별 확정 | 신규 컴포넌트마다 오너 확정 라운드트립 발생 |
| C2 | DS 등록 | 확정 컴포넌트가 DESIGN_SYSTEM.md + 프리뷰 페이지에 등록 |
| C3 | 리젝 처리 | 오너 리젝 시 재수정 후 재제출 (전체 시안으로 넘어가지 않음) |

**게이트 (7단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| G1 | DS 린트 | 하드코딩된 색상/간격 탐지 |
| G2 | 레이아웃 규칙 | max-width, header 등 공통 규칙 준수 확인 |
| G3 | 실패→재작업 자동 | 게이트 No 항목 → 수정 지시서 자동 생성 |

**통합**

| # | 기준 | PASS 조건 |
|---|---|---|
| X1 | version branch 실행 | 모든 디자인 작업이 version/vX.Y.Z에서 실행 |
| X2 | worktree 전파 | 디자인 확정 후 story worktree에 git merge로 전파 성공 |
| X3 | 오너 프리뷰 | 새 화면이면 항상 프리뷰 실행 |
| X4 | "이건 아닌데" 감소 | 8단계에서 전체 리젝 횟수가 기존 대비 감소 |

---

**의존 순서**: T0 → T1/T2 (병렬) → T3/T4/T5 (병렬) → T6 → T7 → T8
