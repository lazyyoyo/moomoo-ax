# team-product 매핑

> moomoo-ax 가 team-ax 로 편입할 때 쓰는 영구 레퍼런스. 2026-04-11 기준 `~/hq/projects/my-agent-office/plugins/team-product/` 스냅샷.

## 개요

team-product 는 `init → define → design → implement → qa → deploy` 6 stage 의 Claude Code 플러그인이다. 각 stage 는 하나의 SKILL.md 로 표현되며, conductor(메인 세션)가 slash command 로 해당 SKILL 을 실행하고, SKILL 내부에서 10종 subagent 를 순차/병렬 호출하는 계층형 구조다.

- **6 stage** (SKILL): product-init, product-define, product-design, product-implement, product-qa, product-deploy
- **10 agent** (subagent): analyst, design-engineer, executor, planner, po, qa, reviewer, ui-designer, ux-designer, ux-writer
- **stage 간 연결**: `.phase` JSON 파일로 현재 단계 기록, 브랜치 규약(`define/vX.Y`, `vX.Y/{설명}`), 루트 BACKLOG/ROADMAP/decisions 가 공유 상태
- **산출물 위치**: `{project}/dev/docs/` (specs/flows/designs + ARCHITECTURE/DESIGN_SYSTEM/API_SPEC/DB_SCHEMA) + `{project}/versions/vX.Y/` (plan/qa-plan/qa-report/changelog) + 루트 산출물(BACKLOG, ROADMAP, decisions)

진짜 병목 (추측, PROJECT_BRIEF 북극성지표 "오너 개입 횟수" 기준):

1. **product-design** (479줄, 6 stage 중 최대) — 시안 N개 격리 세션 + Gemini 리뷰 + reviewer + browser-verify + 오너 프리뷰 루프. "이거 아니야, 내가 할게" 가 가장 자주 나오는 지점.
2. **product-implement** (258줄) — executor/design-engineer 의 태스크별 커밋 루프가 reviewer 한테 reject 당할 때 오너 개입 유발.
3. **product-define** (153줄) — JTBD/Scenario Walkthrough 자체는 자동화되지만 AskUserQuestion 루프가 실제로 최초 의도 캡처 지점이라 "한 번만 캡처" 원칙의 표면.

## Stage 별 요약

### product-init

- **목적**: 프로젝트 부트스트랩. 오너 인터뷰 + 워크스페이스 스캐폴딩 + 인프라 연결 + 초기 define 자동 실행까지 최초 1회.
- **입력**: (없음 — 맨바닥에서 시작) 오너 AskUserQuestion 답변, `references/default-stack.md` 기본값, `references/workspace-structure.md` 디렉토리 규약.
- **출력**: `{project}/` 전체 디렉토리(brand/, strategy/, marketing/, reference/library/, notes/, dev/), ARCHITECTURE.md 초안, .env / .env.example / .gitignore, BACKLOG.md + ROADMAP.md + decisions.md, GitHub repo + Supabase + Vercel 연결, settings.json permission 설정, 끝에 /product-define major 자동 트리거.
- **호출 agent**: PO 단독.
- **주요 자연어 규칙**:
  - 비자명한 질문만 (코드/문서로 확인 가능한 것은 묻지 않음).
  - 기본 스택과 다른 선택이 없으면 묻지 않고 진행.
  - .env 에 실제 값 넣지 않음 (변수명만).
  - 오너 확인 없이 인프라 연결 금지.
  - 모든 stage 공통: `.phase` JSON 갱신 + `phase-usage-logger.sh` 호출 (Step 0/0a).
- **references/**:
  - `default-stack.md` — 기본 기술 스택 (Next.js 등 레퍼런스 스택).
  - `env-setup.md` — .env / .env.local / .env.example 규약.
  - `workspace-structure.md` — `{project}/` 디렉토리 트리 정의.
- **templates/**:
  - `BACKLOG_TEMPLATE.md` — BACKLOG.md 초기 구조 (inbox/ready/done).
  - `DECISIONS_TEMPLATE.md` — decisions.md 초기 구조.
  - `ROADMAP_TEMPLATE.md` — ROADMAP.md 초기 구조 (버전별 스코프).
- **SKILL.md 길이**: 140 줄
- **이관 난이도**: 3 — 기능 자체는 단순하나 Supabase/Vercel/GitHub/Figma MCP 등 외부 인프라 배선이 오너 환경 가정에 크게 의존.
- **편입 우선도 제안**: **low** — moomoo-ax 는 이미 자체 프로젝트로 부트스트랩돼 있고 team-ax 의 product loop 대상은 yoyo/jojo 의 기존 프로젝트가 많음. 전용 `ax-init` 을 최소 버전으로 재작성하는 편이 낫다.

### product-define

- **목적**: 매 버전 시작 시 스코프 결정 + 로드맵 관리. JTBD → Story Map → SLC 프레임으로 분해 후 spec 작성.
- **입력**: BACKLOG.md, ROADMAP.md, dev/docs/specs/, brand/.
- **출력**: specs/ 추가·수정, ARCHITECTURE.md 갱신, ROADMAP.md 업데이트, BACKLOG.md inbox→ready 전환, flows/viz/vX.Y-scenario-walkthrough.html (인터랙티브 HTML), strategy/ (major 시).
- **호출 agent**: PO → analyst. PO 가 인터뷰/스코프 결정 후 analyst 가 spec 작성 + Scenario Walkthrough + Flow Viz HTML 생성.
- **주요 자연어 규칙**:
  - major / minor 분기 (major = v2.0 등, minor = v1.1 등). major 만 JTBD 정의·Story Map 부터 시작.
  - "And 없는 한 문장" 테스트로 spec 범위 검증.
  - 각 JTBD 마다 Scenario Walkthrough 필수 (시작→완료→되돌리기/수정까지).
  - 에이전트 단계마다 개별 커밋 (세션 끊김 대비).
  - codex 플러그인 활성 시 `/codex:adversarial-review` 로 스펙 교차 검토.
  - COLLABGUARD (collab:true 프로젝트 한정) — 타 브랜치 ahead 커밋 확인.
  - define 전용 브랜치 `define/vX.Y` 강제.
- **references/**:
  - `jtbd-storymap-slc.md` — JTBD + Story Map + SLC(Simple/Lovable/Complete) 프레임워크.
  - `roadmap-lifecycle.md` — ROADMAP 생명주기 + 중간 수정 시나리오.
  - `spec-writing-guide.md` — spec 작성 가이드.
  - `flow-viz-template.md` — Flow Viz HTML 표준 구조 (design 과 공유).
- **templates/**: 없음.
- **SKILL.md 길이**: 153 줄
- **이관 난이도**: 2 — 대부분 자연어 프롬프트 + AskUserQuestion. Flow Viz HTML 생성 부분만 분량이 큼.
- **편입 우선도 제안**: **high** — "의도 캡처는 단 한 번" 원칙을 실현하는 핵심 스테이지. moomoo-ax v0.2 의 ax-define 루프가 이미 있으므로 템플릿/references 만 이식하면 됨.

### product-design

- **목적**: define 에서 design 필요로 표시된 경우에만 실행. UX 플로우 + 오너 디자인 인터뷰 + N개 시안 격리 세션 + 리뷰 + 디자인 시스템 확정 + API/DB.
- **입력**: specs/, brand/, dev/docs/DESIGN_SYSTEM.md, `{project}/reference/` (library + 작업별).
- **출력**: flows/ (마크다운 + viz HTML), `dev/docs/designs/` (design-brief + copy-guide + glossary + creative-direction), `(mockup)/vX.Y-{기능}-{variant}/`, DESIGN_SYSTEM.md 신규/업데이트, components/shared/, DB_SCHEMA.md, API_SPEC.md.
- **호출 agent** (순서): ux-designer → ux-writer(카피 가이드) → analyst(기술 타당성) → design-engineer(격리 세션 N개, 병렬) → Gemini CLI(리뷰) → reviewer(자동 리뷰) → design-engineer(수정) → ui-designer(디자인 시스템 확정) → analyst(DB/API).
- **주요 자연어 규칙**:
  - 첫 버전 vs 이후 버전 프롬프트 템플릿 분기 (DESIGN_SYSTEM.md 존재 여부).
  - 시안 N개는 반드시 **격리 CLI 세션** (`claude -p "..." &` 병렬) — 같은 세션의 subagent 가 아님.
  - 레퍼런스는 `{project}/reference/library/` 상시 수집 + `reference/vX.Y-{기능}/` 작업별.
  - Playwright 로 레퍼런스 사이트 캡처 (기본/호버/viewport).
  - **6→7 GATE 스킵 불가**: Gemini 리뷰 + reviewer subagent + agent-browser-verify 3단계 모두 통과해야 오너 프리뷰 진행.
  - 오너 피드백 최대 3회 루프, 수렴 안 되면 오너 최종 결정 강제.
  - 슬롭 금지 (그라디언트/그림자/라운드 남발).
  - 텍스트 하드코딩 절대 금지 (i18n/copy 경유).
  - 토큰-온리 스타일링 (mockup 제외).
- **references/**:
  - `design-system-guide.md` — DESIGN_SYSTEM.md 구조 + 토큰 레지스트리.
  - `slop-prevention.md` — AI 슬롭 금지 목록 + 2차 수렴 방지.
  - `mockup-pattern.md` — (mockup)/ 구조 + 시안 갤러리 + 채택 프로토콜.
  - `motion-principles.md` — 모션 원칙 요약.
  - `creative-direction-example.md` — creative direction 문서 예시.
  - `reference-readme-template.md` — 레퍼런스 README 표준.
- **templates/**: 없음.
- **SKILL.md 길이**: 479 줄
- **이관 난이도**: 5 — 6 stage 중 가장 복잡. 격리 세션 병렬 실행 + Gemini CLI 연동 + Figma MCP + Playwright + preview-shell 등 외부 의존이 최다. moomoo-ax 로 그대로 포팅 불가, 해체 후 재조립 필요.
- **편입 우선도 제안**: **medium** — team-design 플러그인이 별도로 존재하므로 team-ax 는 디자인 생성 자체를 위임하고 "ax-design" 은 design-brief 작성 + 시안 리뷰 오케스트레이션만 담당하는 얇은 래퍼 수준이 현실적. v0.3 에 전체 포팅 금지.

### product-implement

- **목적**: design 산출물 + spec 기반 코드 구현. plan → preflight → build(phase별 반복) → review-architecture → review → simplify → test.
- **입력**: API_SPEC.md, DB_SCHEMA.md, flows/, (mockup)/, specs/, DESIGN_SYSTEM.md, AGENTS.md.
- **출력**: 실제 코드, 테스트, `versions/vX.Y/plan.md` (살아있는 문서).
- **호출 agent** (순서): planner → executor(BE) + design-engineer(FE) → reviewer → qa.
- **주요 자연어 규칙**:
  - working tree 클린 확인 (미커밋 시 stash/commit 제안).
  - plan.md 는 phase 단위 분할 (DB/API 기반 → FE 연결 → 상태/인터랙션 등).
  - preflight 체크리스트: 아키텍처 스택 확인, CLI preflight(supabase/vercel/gh/bun), 디자인 시스템 확인, QA 인프라 감지.
  - build 이터레이션: BE→FE 순, 태스크 1개 선택 → 구현 → lint+typecheck+unit+build 통과 + **태스크 단위 커밋** → reviewer → plan 체크박스 갱신.
  - phase 검증 통과 전 다음 phase 금지 (backpressure).
  - review-architecture: ARCHITECTURE.md 명시 라이브러리 실제 사용 여부 검증 (aporia incident 기반).
  - simplify 단계 = code-simplifier 로 기능 보존 복잡성 정리.
  - test 단계 = lint → typecheck → unit → build → E2E 전체 + agent-browser-verify (QA 인프라 감지 시 qa-login 까지).
  - URL 전달 전 서버 HTTP 200 필수.
  - 병렬 실행 시 subagent 는 plan.md 직접 수정 금지 (경합 방지, v0.26.0 회고).
  - placeholder/stub 금지, 텍스트/보안 하드코딩 절대 금지, .env cat 금지.
  - codex 플러그인 활성 시 `/codex:adversarial-review --background` 병렬 실행.
- **references/**:
  - `preflight-checklist.md` — build 시작 전 체크리스트 (full).
  - `backpressure-pattern.md` — Ralph backpressure + fresh context.
  - `review-checklist.md` — pr-review-toolkit 리뷰 항목.
  - `security-rules.md` — 보안 하드코딩/로그/env 규칙.
- **templates/**:
  - `PLAN_TEMPLATE.md` — versions/vX.Y/plan.md 구조 (phase 분할 + 검증 기준).
- **SKILL.md 길이**: 258 줄
- **이관 난이도**: 3 — 순서 자체는 선형이지만 reviewer 루프 + backpressure + plan.md 살아있는 문서 갱신이 codification 난이도 높음.
- **편입 우선도 제안**: **high** — moomoo-ax v0.2 에서 ax-implement 가 이미 검증됨(`labs/ax-implement`). preflight/review-architecture/simplify 를 스크립트로 뽑기 좋음.

### product-qa

- **목적**: implement 내부 테스트와 별개로 제품 수준 품질 보증. 자동화(functional/visual/viewport/a11y/perf/security) + 수동 사용성 테스트.
- **입력**: flows/, specs/, DESIGN_SYSTEM.md, 전체 코드, 이전 qa-plan.md.
- **출력**: `versions/vX.Y/qa-plan.md`, `versions/vX.Y/qa-report.md`.
- **호출 agent**: qa 단독.
- **주요 자연어 규칙**:
  - [setup] 단계에서 QA 인프라 스캐폴딩 제안 (qa-login, qa/reset, playwright.config) — 오너 승인 없이 자동 생성 금지.
  - [plan] 단계에서 이전 버전 qa-plan FAIL/리그레션 자동 인용 (버전 간 누적).
  - **Happy Path End-to-End phase 필수** — 실제 서비스 의존성(API 키/DB) 포함 실행. 목업/스크린샷만으로 PASS 금지. 외부 서비스 누락 시 BLOCKED + 즉시 보고.
  - [auth setup]: AGENTS.md 의 qa-login 정보 파싱하여 그룹별(미인증/온보딩/핵심기능/엣지) 실행.
  - 모바일 시각 인터랙션 E2E: iPhone SE/14/14 Pro Max 3종 뷰포트 매트릭스 + 가상 키보드/긴 응답/빠른 연속 입력/패널 토글 4종 스트레스 테스트.
  - Functional = Playwright MCP, Visual = LLM-as-judge, a11y = axe-core, 성능 = Lighthouse.
  - SSOT 문서 11종 전수 최신화 검사 (specs/flows/ARCHITECTURE/DESIGN_SYSTEM/API_SPEC/DB_SCHEMA/AGENTS/ROADMAP/BACKLOG/decisions/CLAUDE).
  - URL 전달 전 서버 HTTP 200 필수.
  - 코드 수정 금지 — 이슈는 qa-report 에 기록만.
  - codex 활성 시 `/codex:review --base main --background` 교차 리뷰.
  - 수동 사용성 테스트: 편향 없는 태스크 시나리오 (답 주지 않음) + SUS 점수.
- **references/**:
  - `qa-inventory-guide.md` — QA 인벤토리 작성법.
  - `playwright-patterns.md` — Functional/Visual QA + Viewport fit 패턴.
  - `usability-testing.md` — 수동 사용성 테스트 프로세스.
  - `qa-login-template.ts` — QA 전용 로그인 라우트 템플릿.
  - `qa-reset-template.ts` — 상태 리셋 라우트 템플릿.
  - `playwright-config-template.ts` — E2E 설정 템플릿.
- **templates/**:
  - `QA_PLAN_TEMPLATE.md` — qa-plan.md 구조 (phase별).
  - `QA_REPORT_TEMPLATE.md` — qa-report.md 구조 (signoff 체크리스트 포함).
- **SKILL.md 길이**: 280 줄
- **이관 난이도**: 4 — Playwright MCP + QA 인프라 스캐폴딩(qa-login/reset) + 모바일 뷰포트 매트릭스 등 외부 의존 많음.
- **편입 우선도 제안**: **medium** — v0.4 목표인 qa 루프와 직접 대응. QA 인프라 스캐폴딩 부분은 ax-qa 에 포함시키지 말고 프로젝트별 선택지로 분리하는 편이 깔끔.

### product-deploy

- **목적**: 버전 마감. preview 배포 → 검증 → changelog → tag → GitHub Release → production 배포 → 문서 갱신.
- **입력**: 전체 코드, ROADMAP.md, 루트 CHANGELOG.md.
- **출력**: 배포 URL, `versions/vX.Y/changelog.md`, git tag vX.Y.Z, GitHub Release, 루트 CHANGELOG.md 갱신.
- **호출 agent**: 없음 (conductor 직접).
- **주요 자연어 규칙**:
  - preview 배포 → HTTP 200 확인 (실패 시 `vercel env ls` 로 환경변수 누락 진단 + 오너 가이드 출력).
  - QA 인프라 감지 시 `/auth/qa-login` 307 리다이렉트 확인.
  - production 배포 전 오너 승인 필수.
  - changelog: keepachangelog 형식 6카테고리 (Added/Changed/Deprecated/Removed/Fixed/Security), ISO 8601 날짜, 커밋 로그 복붙 금지.
  - implement 중 Unreleased 섹션에 누적 → deploy 시 버전 섹션으로 이동.
  - 발행된 태그 이동 금지.
  - 실패 시 이전 태그로 Vercel revert + hotfix 브랜치.
  - 배포 완료 후 `.phase` 를 `"done"` 으로 갱신.
- **references/**:
  - `changelog-convention.md` — keepachangelog 규칙 + GitHub Release 절차.
- **templates/**:
  - `CHANGELOG_TEMPLATE.md` — changelog 템플릿.
- **SKILL.md 길이**: 134 줄
- **이관 난이도**: 2 — Vercel/GitHub CLI 의존이지만 커맨드가 거의 고정 스크립트.
- **편입 우선도 제안**: **low** (v0.5 까지) — PROJECT_BRIEF 의 "deploy 는 비용 순 점진 확장 (localhost → preview → production)" 원칙에 따라 최초엔 localhost 만. preview/production 로직은 나중에 이식.

## Agent 별 요약

### po

- **역할**: 제품 오너 대리. 오너 인터뷰 + JTBD/Story Map/SLC 로 스코프 결정 + ROADMAP/BACKLOG 관리.
- **허용 tools**: Read, Grep, Glob, AskUserQuestion, Write, Edit.
- **model**: opus / color: purple.
- **사용하는 skill**: product-init(전체), product-define(major/minor 양쪽의 인터뷰·JTBD·Story Map).
- **길이**: 93 줄
- **편입 가치**: 상 — "의도 캡처 한 번" 원칙의 주체. moomoo-ax ax-define 에 직접 이식 가치 있음.

### analyst

- **역할**: 기술 분석 + spec + API/DB 정의. define/design 양쪽에서 활동.
- **허용 tools**: Read, Grep, Glob, Bash, Write, Edit.
- **model**: opus / color: blue.
- **사용하는 skill**: product-define(specs 작성, Scenario Walkthrough, Flow Viz, ARCHITECTURE 갱신), product-design(기술 타당성 검토, DB_SCHEMA, API_SPEC).
- **길이**: 92 줄
- **편입 가치**: 상 — define + design 을 잇는 기술 브릿지. ax-define 에 포함.

### ux-designer

- **역할**: 사용자 경험 플로우 설계 (specs → flows + 상태 변형 + walkthrough + viz HTML).
- **허용 tools**: Read, Grep, Glob, Write, Edit.
- **model**: opus / color: pink.
- **사용하는 skill**: product-design(step 1, 1b, 1c — UX 플로우, Flow Walkthrough, Flow Viz).
- **길이**: 87 줄
- **편입 가치**: 중 — 디자인을 team-design 에 위임한다면 ux-designer 역할만 ax-design 에 남기는 편.

### ux-writer

- **역할**: UX 카피 + 톤앤매너 + 용어집 + i18n 키 구조 설계.
- **허용 tools**: Read, Grep, Glob, Write, Edit, Bash, WebSearch, WebFetch.
- **model**: opus / color: pink.
- **사용하는 skill**: product-design(step 3a — copy guide + glossary 작성, 추후 카피 검증).
- **길이**: 106 줄
- **편입 가치**: 중 — 텍스트 하드코딩 금지 원칙이 ax 전반에도 유효. 별도 스킬로 뽑을 수 있음.

### ui-designer

- **역할**: 비주얼 기준 디자인 시스템 + creative direction.
- **허용 tools**: Read, Grep, Glob, Write, Edit.
- **model**: opus / color: purple.
- **사용하는 skill**: product-design(step 9 — DESIGN_SYSTEM.md 신규/업데이트, creative-direction 문서).
- **길이**: 92 줄
- **편입 가치**: 하 — team-design 의 주 영역. team-ax 로 독립 이식할 필요 낮음.

### design-engineer

- **역할**: UI/UX 요청을 코드로 구현. 시안 생성 + 프리뷰 인프라 + implement FE.
- **허용 tools**: Read, Grep, Glob, Bash, Write, Edit.
- **model**: opus / color: cyan.
- **사용하는 skill**: product-design(step 4 프리뷰 인프라, step 6 시안 격리 세션, step 10 컴포넌트 등록), product-implement(FE build, agent-browser-verify).
- **길이**: 118 줄
- **편입 가치**: 상 (implement FE 한정) — ax-implement 에 executor 와 병행해서 포함.

### planner

- **역할**: 구현 계획 작성 (gap 분석 + phase 분할 + 검증 기준).
- **허용 tools**: Read, Grep, Glob, Bash, Write, Edit.
- **model**: sonnet / color: yellow.
- **사용하는 skill**: product-implement([plan] 단계 — versions/vX.Y/plan.md 생성).
- **길이**: 88 줄
- **편입 가치**: 상 — plan.md "살아있는 문서" 개념이 moomoo-ax 하네스와 직접 호환.

### executor

- **역할**: 백엔드 TDD 구현 + 태스크별 커밋 + CLI preflight + backpressure 준수.
- **허용 tools**: Read, Grep, Glob, Bash, Write, Edit.
- **model**: sonnet / color: green.
- **사용하는 skill**: product-implement(BE build 단계).
- **길이**: 118 줄
- **편입 가치**: 상 — ax-implement 의 실행 주체. 이미 labs/ax-implement 로 검증됨.

### reviewer

- **역할**: 코드 리뷰 + 디자인 QA. 읽기 전용.
- **허용 tools**: Read, Grep, Glob, Bash.
- **model**: opus / color: red.
- **사용하는 skill**: product-implement([review] 최종 + [review-architecture] 단계), product-design(step 7a 디자인 자동 리뷰).
- **길이**: 134 줄 (가장 김)
- **편입 가치**: 상 — moomoo-ax judge(rubric) 와 겹치는 영역. 이관보다는 "levelup judge 의 일부 규칙이 reviewer 로부터 유래"로 매핑하는 게 맞음.

### qa

- **역할**: 자동화 QA (functional/visual/viewport/a11y/perf/security) + 수동 사용성 테스트 지원.
- **허용 tools**: Read, Grep, Glob, Bash, Write, Edit.
- **model**: opus / color: orange.
- **사용하는 skill**: product-implement([test] 단계), product-qa(전체 단독 에이전트).
- **길이**: 114 줄
- **편입 가치**: 중 — v0.4 ax-qa 에서 사용. Playwright MCP 의존은 이관 시 옵션 처리 필요.

## 의존 그래프

Stage 간 흐름:

```
product-init
  └─(마지막에 자동 호출)─> product-define (major)
                           │
                           ├─ design 필요 ──> product-design ──> product-implement
                           │                                          │
                           └─ design 불필요 ─> product-implement <────┘
                                                   │
                                                   ├─ (implement 내부 [test]) ──┐
                                                   ↓                             │
                                                  product-qa  <──────────────────┘
                                                   │
                                   ┌───────────────┼──────────────────┬──────────────┐
                                   ↓               ↓                  ↓              ↓
                                 bug 수정     시각 미조정         flow 변경       기능 변경
                               (→ implement) (→ qa 자동화만)     (→ design)     (→ define)
                                   │                                              │
                                   └──────────> OK ────────────> product-deploy ──┘
                                                                     │
                                                                     └─> (다음 버전) product-define
```

Agent 호출 (stage 별):

```
product-init:        po
product-define:      po → analyst
product-design:      ux-designer → ux-writer → analyst → design-engineer(병렬 N) → Gemini CLI → reviewer → design-engineer → ui-designer → analyst
product-implement:   planner → (executor + design-engineer) → reviewer → code-simplifier → qa
product-qa:          qa
product-deploy:      (agent 없음 — conductor 직접)
```

공유 상태:

- `.phase` JSON (모든 stage 가 Step 0에서 갱신)
- `{project}/BACKLOG.md + ROADMAP.md + decisions.md` (define 쓰기, 타 stage 읽기)
- `{project}/dev/docs/specs/ + flows/ + designs/ + ARCHITECTURE.md + DESIGN_SYSTEM.md + API_SPEC.md + DB_SCHEMA.md + AGENTS.md` (stage 간 이어달리기)
- `{project}/versions/vX.Y/` (plan.md, qa-plan.md, qa-report.md, changelog.md)

## 편입 제안 (moomoo-ax 의 team-ax 로)

### 옵션 A — 최소 (ax-implement 1개만)

- **이관 대상**: product-implement SKILL 의 plan/preflight/build/review/simplify/test 흐름 + planner/executor/design-engineer/reviewer/qa agent. `references/preflight-checklist.md`, `review-checklist.md`, `security-rules.md`, `backpressure-pattern.md` 이식. `PLAN_TEMPLATE.md` 복사.
- **제외**: design/qa/deploy stage, design-engineer 의 시안 생성 로직, qa 의 QA 인프라 스캐폴딩.
- **난이도**: 3 (labs/ax-implement 에 이미 일부 있음) / **소요**: 1~2 sprint.
- **적합 버전**: **v0.3** (+ 기존 ax-implement 심화). v0.3 design 루프는 별도 최소 스펙으로 시작하고, 여기서는 implement 만 강화.

### 옵션 B — 중간 (implement + qa + define 뼈대)

- **이관 대상**: A + product-define(major/minor 분기, JTBD/Story Map/SLC) + product-qa(자동화 테스트 카테고리 + qa-plan/qa-report 템플릿). po/analyst agent 추가. `references/jtbd-storymap-slc.md`, `spec-writing-guide.md`, `qa-inventory-guide.md` 이식.
- **제외**: product-design 전체, product-deploy, QA 인프라 스캐폴딩 (qa-login/reset 템플릿), 수동 사용성 테스트.
- **난이도**: 3.5 / **소요**: 3~4 sprint.
- **적합 버전**: **v0.4** (qa 루프 + ax-autopilot implement→localhost→preview 목표와 정합).

### 옵션 C — 전체 (6 stage 다)

- **이관 대상**: 6 SKILL + 10 agent 전부. `.phase` 스키마, `{project}/` 디렉토리 규약, SSOT 문서 11종, Flow Viz HTML, preview-shell, QA 인프라 스캐폴딩까지.
- **제외**: 없음 (다만 team-design 과 중복되는 ui-designer/ux-writer 는 얇은 래퍼).
- **난이도**: 5 / **소요**: 6~8 sprint.
- **적합 버전**: **v0.5** (6 stage 전부 + team-product 대체 선언 목표) — 단, 6 stage 의 **형태만** 포팅하고 내부 로직은 moomoo-ax 의 codification 루프로 재작성한다. 1:1 복사는 실패.

## 이관 시 주의점

### team-product 고유 개념 중 moomoo-ax 에 맞지 않는 것

- **계층형 subagent 호출** — team-product 는 SKILL 이 subagent 를 순차/병렬로 직접 호출하는 구조. moomoo-ax 는 levelup loop 가 범용 엔진(`src/loop.py`)이고 대상별 차이는 `labs/{target}/program.md + rubric.yml` 로만 표현. 이관 시 "agent 호출 순서"를 rubric 항목 + program 규칙으로 재해석해야 함.
- **`.phase` JSON + `phase-usage-logger.sh`** — team-plugin 의존. moomoo-ax 는 자체 DB(Supabase) + dashboard 로 관찰 — 이 훅은 삭제하고 levelup loop 의 DB 로깅으로 대체.
- **세션 격리 병렬 실행 (`claude -p "..." &`)** — product-design step 6. moomoo-ax 의 levelup 루프는 `subprocess.run` 단일 호출이 원칙. 시안 N개 생성을 이식하려면 `src/loop.py` 에 병렬 런처 추가 필요.
- **Gemini CLI 의존** (product-design step 7) — moomoo-ax 는 judge = LLM Judge(Claude) 이고 이종 모델 교차 검토는 선택지. Gemini 의존 그대로 옮기지 말 것.
- **codex 플러그인 훅** — define/design/implement/qa 모두 `/codex:adversarial-review` 등을 스킵 가능한 선택지로 포함. moomoo-ax 에서는 codex 가 필수가 아니므로 동일하게 "optional" 유지.
- **Figma MCP + Playwright MCP + qa-login/reset** — 프로젝트 환경 의존. team-ax skill 에 포함시키지 말고 프로젝트별 `program.md` 에서 선언.
- **AGENTS.md 운영 학습 메모** — team-product 고유 개념. moomoo-ax 는 SKILL.md (자연어) + scripts/ (deterministic) + references/ 가 공식 규약. AGENTS.md 개념은 `notes/` 또는 `references/` 로 흡수.

### 원본 SKILL.md 의 자연어 중 "deterministic 스크립트로 뽑기 좋은" 규칙 (codification 타깃)

Progressive Codification 메모리에 따라 자연어 → script 추출 후보:

1. **`.phase` JSON 갱신 + 토큰 사용량 스냅샷 (모든 stage Step 0/0a)** — 6 SKILL 에 동일 코드 중복. `scripts/phase-transition.sh {stage} {version}` 으로 일원화.
2. **preflight CLI 체크** (product-implement [preflight] step 5) — `which supabase && supabase projects list` 등은 스크립트 `scripts/preflight-cli.sh` 로 추출하고 SKILL 에서는 결과 파일만 참조.
3. **architecture compliance 검사** (product-implement [review-architecture]) — "ARCHITECTURE.md 라이브러리 vs package.json vs 실제 import" 대조. `scripts/check-arch-compliance.py` 로 deterministic 하게.
4. **SSOT 문서 동기화 검사** (product-qa [signoff] + 11종 문서 목록) — 문서 11종 스캔 + 갱신 여부 체크. `scripts/ssot-check.py`.
5. **changelog 카테고리 검증** (product-deploy) — keepachangelog 6 카테고리 + ISO 8601 날짜 + 커밋 로그 복붙 여부. `scripts/lint-changelog.py`.
6. **(보너스) spec "And 없는 한 문장" 테스트** (product-define) — 정규식으로 간이 검출 가능 (`/\b(?:and|그리고|및)\b/i` 포함 문장 flag). `scripts/spec-and-check.py`.

위 6개는 codification 로드맵의 상위 후보. SKILL.md 자연어 토큰을 줄이고 judge 기준도 명확해짐.

### Claude Code 공식 skill 규약 (`SKILL.md + scripts/ + references/`) 과 team-product 구조의 차이

- team-product 는 `scripts/` 가 **플러그인 루트**에만 있고 각 skill 하위에는 없다. 공식 규약은 skill 하위에 `scripts/` 권장.
- team-product 는 `agents/` 를 skill 과 분리된 플러그인 루트에 둠. 공식 규약은 skill 별 subagent 를 skill 폴더 안에 두는 예시가 많지만, 공유 agent 는 루트에 두는 게 재사용에 유리 — team-product 패턴 유지 가치 있음.
- team-product 의 `templates/` 가 일부 skill 에만 존재(define 은 없음). moomoo-ax 이관 시 일관되게 두거나 전부 제거하고 SKILL.md 내 인라인 템플릿으로 바꿀 수 있음.
- `description` 필드에 "Use when:" 형태로 키워드 나열 — 공식 규약과 일치. 유지.
- team-product 는 conductor 세션(메인) + subagent 역할 분리가 강함. moomoo-ax 의 levelup loop 는 외부 orchestrator(`src/loop.py`)가 conductor 역할을 맡으므로, team-ax SKILL 은 "conductor 가 한다" 대신 "엔진이 한다" 로 언어 변경 필요.

---

**v0.3 에 대한 결론 (추측):** 옵션 A(ax-implement 심화) 만 v0.3 에 편입하고, design 루프는 team-design 을 직접 호출하는 얇은 래퍼로 시작. define/qa/deploy 의 구체 이관은 v0.4 이후로 미룬다. 이 문서는 그 시점마다 해당 stage 섹션만 다시 읽어 편입 여부를 판단하는 레퍼런스로 사용.
