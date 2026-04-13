# team-design 매핑

> moomoo-ax 가 team-ax 로 편입할 때 쓰는 영구 레퍼런스. 2026-04-11 기준 `~/hq/projects/my-agent-office/plugins/team-design/` 스냅샷.

## 개요

team-design 은 단일 스킬 `design-create` + 4 개 agent 로 구성된 디자인 스튜디오 플러그인이다. `design-create` 가 오케스트레이터로서 brief → plan → build → review → refine → preview 사이클을 돌리고, 실제 작업은 4 agent 가 분담한다. Build 는 `ui-designer` 혼자 담당, Review 는 `visual-reviewer` / `ux-reviewer` / `detail-reviewer` 3 관점이 병렬 검증한다.

team-product 의 `/product-design` 스킬은 "brief 만들어서 team-design 에 넘기는 프런트엔드" 역할이고, 실제 시안 생성 + 품질 검증 사이클은 team-design 이 독립적으로 수행한다 (README.md 60 줄 근처에 명시). moomoo-ax 의 ax-design stage 는 이 분업을 하나로 합치거나, 최소한 brief 생성 단계를 ax-define 과 통합해야 한다.

## Skill 요약

### design-create

- **목적**: Design Brief 를 입력받아 프로덕션급 UI 시안을 plan → build → review 사이클로 생성.
- **입력**:
  - Brief 가 이미 있음 (team-product 전달) → 그대로 사용 + `{project}/brand/` 로 Brand 섹션 보강
  - Brief 없음 → `AskUserQuestion` 으로 오너 인터뷰 후 `design-brief-vX.Y.md` 생성
  - 추가 입력: `{project}/brand/`, `{project}/reference/owner-profile.md`
- **출력**:
  - 시안 페이지 — `dev/src/app/(mockup)/vX.Y-{기능}-{variant}/`
  - `tokens.md` (DESIGN_SYSTEM.md 의 소스)
  - `dev/versions/vX.Y/design-plan.md`
  - `dev/docs/designs/design-brief-vX.Y.md`
  - `dev/docs/designs/creative-direction-vX.Y.md`
  - 채택 후 team-product 가 `dev/src/components/shared/` 로 승격
- **호출 agent**:
  - `ui-designer` — Phase 2 Build 에서 phase 별 격리 세션으로 병렬 호출. Phase 4 정제 루프에서도 수정 실행 주체.
  - `visual-reviewer` — Phase 3 Review 에서 시각 완성도 검증. Phase 4 에서는 해당 관점 이슈일 때만 재검증.
  - `ux-reviewer` — Phase 3 Review 에서 사용성 검증. 재검증 규칙 동일.
  - `detail-reviewer` — Phase 3 Review 에서 디테일/접근성/코드 품질 검증. 재검증 규칙 동일.
- **주요 자연어 규칙**:
  - 폰트 결정 프로토콜: Brand 지정 → `font-catalog.md` 매칭 → 한국어면 `korean-fonts.md` → `font-pairing-kr.md` → Google Fonts 탐색 순
  - 모션은 화면당 최소 1 개 "의미 있는" 모션 사전 결정, 장식 모션 금지
  - 레이아웃 패턴은 이전 phase 와 반복 금지
  - 카피 가이드라인을 design-plan.md 에 반드시 섹션으로 포함 (톤 / 금지 패턴 / 도메인 용어 매핑)
  - 정제 원칙: "추가 금지, 있는 것을 더 예술적으로"
  - 정제 루프 수정 전 Playwright 로 현재/수정 후 스크린샷 필수 (코드만 보고 수정 금지)
  - 정제 최대 2 회, 오너 프리뷰 최대 3 회 루프 후 미수렴 시 오너 결정 강제
  - 완료 기준 6 체크박스 (Flows / 3 리뷰 / 모션 / 피하고 싶은 것 회피)
- **references/** (10 개):
  - `design-brief-template.md` — Brief 작성 가이드
  - `design-principles.md` — 필수 원칙 + 안티패턴 (Build + Review 전체에서 로드)
  - `trends-2026.md` — 시각 트렌드 치트시트
  - `domain-checklists.md` — 도메인별 UI/UX 체크리스트
  - `font-catalog.md` — 영문 폰트
  - `korean-fonts.md` — 한국어 폰트
  - `font-pairing-kr.md` — 한영 페어링
  - `layout-patterns.md` — 레이아웃 패턴 목록
  - `animation-recipes.md` — 모션 코드 레시피
  - `library-decision.md` — 프론트엔드 라이브러리 선택
- **templates/**: 없음 (references 만 존재)
- **길이**: 230 줄
- **이관 난이도**: 4/5 — 오케스트레이션이 brief 생성 + plan + build + 3 관점 review + 2 단계 루프 제어까지 모두 자연어에 녹아 있음. Playwright 의존, team-product 경로 규약 의존, AskUserQuestion 을 brief 수집에 사용. moomoo-ax 쪽은 plan.py / loop.py 로 분리된 구조라 포팅보다 재설계에 가까움.
- **편입 우선도**: v0.3 이후 중. v0.3 은 design 루프 (단일 agent 개선) 스코프라 본 스킬 통째 편입은 범위 밖. 다만 references/ 의 10 개 문서와 3 관점 리뷰 agent 3 개는 v0.3 설계 때부터 참조 자산으로 즉시 활용 가능.

## Agent 별 요약

### ui-designer

- **역할**: design-plan.md 에서 결정된 폰트/모션/레이아웃/카피 가이드라인을 준수하여 실제 시안 코드를 작성.
- **허용 tools**: Read, Grep, Glob, Bash, Write, Edit
- **model**: opus / **color**: purple
- **사용처**: Phase 2 Build (phase 별 격리 세션 병렬), Phase 4 정제 (수정 실행). 같은 이슈 2 회 실패 또는 오너 "의도와 다르다" 피드백 시 `claude -p` 새 세션 트리거.
- **길이**: 40 줄
- **편입 가치**: 중. Constraints 가 엄격해서 (CSS 변수, i18n, 상태 변형 3 종, 인라인 SVG 금지 등) team-ax 의 ax-implement agent 기본 체크리스트로 재활용 가능. 단 프런트엔드 디자인 전용이라 ax-implement 범용 코드 빌더와는 분리 필요.

### visual-reviewer

- **역할**: 타이포그래피 위계 / 컬러 하모니 / 여백 리듬 / 트렌드 정합성 검증.
- **허용 tools**: Read, Grep, Glob (쓰기 권한 없음 — 명시적 read-only reviewer)
- **model**: opus / **color**: pink
- **사용처**: Phase 3 Review 3 관점 중 "예쁜가?" 축. Phase 4 재검증 시 시각 이슈 전담.
- **길이**: 47 줄
- **편입 가치**: 높음. 10 개 체크리스트 + "기억에 남는 포인트 / 아쉬운 한 가지" 출력 포맷이 LLM Judge 루브릭으로 직접 변환 가능. `references/trends-2026.md` 의존도만 추상화하면 ax-design rubric 재료로 바로 편입 가능.

### ux-reviewer

- **역할**: Brief Flows 커버리지 + 도메인 체크리스트 + 정보 계층 / CTA / 반응형 / 스캔 패턴 검증.
- **허용 tools**: Read, Grep, Glob (read-only)
- **model**: opus / **color**: green
- **사용처**: Phase 3 Review "읽기 쉬운가?" 축.
- **길이**: 52 줄
- **편입 가치**: 높음. 체크리스트 13 개 중 11~13 번 (카피 가이드라인 일치, 기능 나열 헤드라인 FAIL, 도메인 용어 위반 FAIL) 은 ax-define 의 카피 규칙과 직결 — ax-define 산출물 품질 게이트에 재활용 가능.

### detail-reviewer

- **역할**: WCAG 접근성 / 한국어 렌더링 (word-break, fallback) / 모션 의미성 / semantic HTML / CSS 변수 / 성능 / OS-브라우저 렌더링 차이 검증.
- **허용 tools**: Read, Grep, Glob, Bash (실제 렌더링 확인 의도)
- **model**: opus / **color**: orange
- **사용처**: Phase 3 Review "디테일이 있는가?" 축. 인라인 SVG `<path d>` 사용 시 FAIL (엄격).
- **길이**: 58 줄
- **편입 가치**: 중상. 접근성/성능/렌더링은 도메인 무관 공통 체크라 ax-qa stage 로 이관 가능. 한국어 렌더링은 team-ax 이 한국어 제품 전용인 이상 default 체크리스트로 포함해야 함.

## 의존 그래프

```
design-create (orchestrator)
  │
  ├─ [Phase 1 Plan] 자체 수행
  │     + references/ 10 개 문서 참조
  │     + AskUserQuestion (brief 없을 때)
  │
  ├─ [Phase 2 Build] → ui-designer (phase 별 병렬, 격리 세션)
  │
  ├─ [Phase 3 Review] 3 관점 병렬
  │     ├─ visual-reviewer
  │     ├─ ux-reviewer
  │     └─ detail-reviewer
  │
  ├─ [Phase 4 Refine] (이슈 있을 때만, 최대 2 회)
  │     → Playwright 캡처 → 계획 수립 → ui-designer (새 세션 규칙)
  │     → Playwright 재캡처 → 해당 관점 reviewer 재검증
  │
  └─ [Phase 5 Preview] 오너 확인 (최대 3 회)
        피드백 유형별 복귀 지점 분기:
          - 스타일 → Phase 4
          - 레이아웃 → Phase 2
          - 플로우 → Phase 1 (Brief 수정)
          - 시안 추가 → Phase 2
```

호출 순서: Plan 은 메인 세션, Build 는 phase 수 만큼 병렬 ui-designer, Review 는 3 reviewer 병렬. 정제는 이슈 당 순차, 재검증은 "해당 관점만" 재호출.

## team-product/product-design 과의 관계

- **추측**: team-product 의 `/product-design` 은 PM 관점의 brief 작성 + 기획 승인을 담당하고, 실제 시안 제작은 team-design 의 `/design-create` 로 위임하는 분업 구조로 보인다 (README.md "team-product 연동" 섹션, SKILL.md "Brief가 이미 있는 경우 (team-product에서 전달)" 문구 근거).
- **확인 필요**: team-product 의 product-design SKILL.md 를 별도로 읽고 비교해야 역할 경계가 확정됨. 본 문서는 team-design 쪽 스냅샷만 커버.
- **ax-design stage 적합성 추측**: team-ax 의 ax-design stage 는 "define 산출물 → 시안 → 승인" 을 단일 흐름으로 무개입 처리해야 하는 구조이므로, team-design 의 `design-create` 쪽이 ax-design 의 본체에 가깝다. `product-design` 의 brief 생성 책임은 ax-define 으로 흡수되어야 할 가능성이 높다.

## 편입 제안 (moomoo-ax 의 team-ax 로)

- v0.3 은 design 루프 "엔진 1 cycle" 스코프이므로 design-create 통째 이관은 **범위 밖**. 대신 아래를 v0.3 에 미리 활용:
  1. `visual-reviewer` / `ux-reviewer` / `detail-reviewer` 의 체크리스트를 `labs/ax-design/rubric.yml` 초기 항목으로 그대로 옮겨서 LLM Judge 가 점수 매기도록 구성
  2. `references/design-principles.md` + `trends-2026.md` 를 `labs/ax-design/program.md` 의 "오너 규칙 / 불변 원칙" 소스로 참조
  3. design-plan.md 의 "카피 가이드라인" 섹션 구조를 ax-define 산출물 스키마에 포함 (톤 / 금지 패턴 / 도메인 용어 매핑)
- v0.5 (6 stage 전부 + team-product 대체 선언) 시점에 design-create 오케스트레이션 자체를 team-ax 의 ax-design 스킬로 재작성. 단순 포팅 아닌 **재설계** 권장 (근거: loop.py / judge.py 분리 구조와 plan→build→review 자연어 흐름이 구조적으로 다름).
- **codification 후보** (자연어 → script 로 뺄 수 있는 deterministic 부분):
  1. **폰트 결정 프로토콜** — Brand 지정 여부 / 한국어 여부 / 도메인 태그 입력 → `font-catalog.md` + `korean-fonts.md` + `font-pairing-kr.md` 조회 → 후보 리스트 반환. 자연어 판단 거의 불필요.
  2. **산출물 경로 생성** — `dev/src/app/(mockup)/vX.Y-{기능}-{variant}/`, `dev/versions/vX.Y/design-plan.md` 등 6 종 경로 규약은 `version / feature / variant` 입력받아 기계적으로 생성 가능. SKILL.md 57~66 줄 테이블이 그대로 스펙.
  3. **레이아웃 반복 금지 체크** — phase 별 선택 패턴을 기록하고 다음 phase 에서 제외하는 것은 순수 상태 관리. 현재 자연어 "이전 phase 에서 쓴 레이아웃 반복 금지" 는 LLM 이 매번 재확인하는 낭비.
  4. (선택) **완료 기준 6 체크박스 집계** — 3 리뷰어 출력 파싱 + Flows 커버리지 산정은 스크립트가 더 정확.

## 이관 시 주의점

- **team-product 경로 규약에 하드바운딩**: `dev/src/app/(mockup)/`, `dev/docs/designs/`, `dev/versions/vX.Y/` 는 team-product 가 세팅한 프로젝트 구조 전제. team-ax 는 프로젝트 구조 규약을 자체 정의하거나 ax-init 에서 설정하도록 책임 이관 필요.
- **AskUserQuestion 의존**: Brief 생성이 대화형 인터뷰라서 "의도 캡처는 단 한 번" 이라는 moomoo-ax 핵심 원칙과 충돌. ax-define 이 brief 를 한 번에 생성하고 ax-design 은 받기만 하도록 재구성해야 함.
- **Playwright 필수**: 정제 루프에 Playwright 스크린샷이 하드 요구. team-ax 의 ax-design 에도 렌더링 검증 인프라가 전제됨.
- **claude -p 새 세션 트리거**: "같은 이슈 2 회 실패" 규칙은 levelup loop 의 iteration 규칙과 중복. 통합 필요.
- **reviewer agent 의 tool 제한이 Claude Code 공식 규약과 정합**: read-only reviewer (Read/Grep/Glob) 는 공식 권장 패턴이라 그대로 이식 가능.
- **`{project}/brand/` + `{project}/reference/owner-profile.md` 외부 의존**: 프로젝트 바깥 파일을 skill 이 직접 읽는 구조. team-ax 는 input/ 디렉토리에 미리 복사해 두는 규약이 더 맞음.
- **model: opus 하드코딩**: 4 agent 모두 opus 명시. team-ax 는 stage 별 model 선택을 program.md 로 외부화하는 쪽이 일관성 있음.
- **rubric 불변 원칙 충돌**: team-design 은 리뷰 체크리스트가 SKILL.md + agent.md 양쪽에 산재. moomoo-ax 로 옮길 때 `labs/ax-design/rubric.yml` 단일 SSOT 로 통합해야 "rubric 은 루프 안에서 불변" 원칙이 성립.
