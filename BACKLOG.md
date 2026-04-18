---
last-updated: 2026-04-16
---

# moomoo-ax 백로그

team-ax 플러그인 자체 개발의 인박스. 외부 제품(rubato, rofan-world 등)의 BACKLOG는 각 제품 리포 안에 있다 (혼동 금지).

> **운영 규칙**
> - inbox: 아이디어 캡처. 스프린트 미배정.
> - ready: 다음 스프린트 후보로 정제된 항목 (sprint-N-plan 진입 대기).
> - done: 스프린트/hotfix 종료 시 이관. 스프린트 번호 or hotfix 버전 표기.

## inbox

- [feature] `ax-deploy` 스킬 (sprint-5) — 배포 자동화 + `⏳ planned` 마커 잔존 체크 + CHANGELOG 작성 + define/build 산출물 최종 확인 + **워크트리 분기 작업의 deploy 처리** (워크트리에서 작업 완료 → 머지 → 태그 → 배포까지. 원본 repo 세션 제약 없이 워크트리에서도 실행 가능해야 함. 제품 semver과 독립된 트랙도 지원.)
- [infra] moomoo-ax용 statusline 설정 — 현재 my-agent-office 기준 statusline 사용 중. moomoo-ax 프로젝트에 맞는 statusline 필요.
- [bug] team-design/team-product 플러그인 충돌 — ax-design 실행 시 "UX", "디자인" 키워드가 team-design의 ux-reviewer를 트리거. team-product의 product-design도 동일 문제. 대상 프로젝트에서 team-design/team-product 비활성화 필요. 장기적으로 team-ax가 완전 대체 후 제거.

## ready

### sprint-2/3/4 — 완료 → done 섹션으로 이관

## inbox (장기 후보)

- [dogfood] team-ax 자체 도그푸딩 — rubato 또는 rofan-world에 실제 `/ax-define` 1회 실행, 실측 보고서 작성 (sprint-1 비범위로 미룸)
- [feature] `ax-review pr` 타입 구현 — `references/pr-checklist.md` 본격 작성 + sandbox 정책 확정 (`workspace-read` 추정, ax-deploy 도입 시)
- [feature] Hook 기반 자동 강제 — spec-lifecycle 4종 장치를 PreToolUse 훅으로 차단 (현재는 에이전트 규칙 + review만)
- [feature] 의존성 그래프 기반 merge 순서 자동 관리 (deploy 단계)
- [feature] `ax-help` 스킬 — 플러그인 안내. team-ax가 뭔지, 사용 가능한 스킬 목록, 각 스킬의 역할과 실행 순서, 현재 프로젝트 상태(어느 단계까지 진행됐는지) 표시. `/ax-help` 또는 `/ax` 로 호출.
- [feature] `ax-paperwork` 스킬 — 프로젝트 문서 품질 관리. spec/ARCHITECTURE/BACKLOG/CHANGELOG/flows/DESIGN_SYSTEM 등의 정합성 체크 + 최적화. 코드와 문서 간 불일치 탐지 (spec에 있는데 코드에 없는 것, 코드에 있는데 spec에 없는 것), 중복 문서 식별, 오래된 내용 갱신 제안, 문서 간 참조 깨짐 탐지.
- [feature] `ax-clean` 스킬 — 프로젝트 디렉토리 점검 + 최적화. (1) 불필요한 파일: 미사용 컴포넌트, 고아 시안, 빈 디렉토리, 캐시 잔재 (2) 관리 안 되는 문서: 참조 없는 고아 spec, 오래된 flows/, 미정리 versions/, 미아카이브 레퍼런스 (3) QA/디자인 잔재: Playwright 스크린샷이 루트에 방치되는 문제 — 스크린샷 경로 지정(`.ax/screenshots/`) 또는 deploy 시 정리
- [infra] team-ax 자기 진화 — meta loop, 외부 패턴 자동 흡수 (PROJECT_BRIEF 장기 비전)
- [infra] 대시보드 연동 — 오너 개입 횟수 / 토큰 / iteration 등 북극성 지표 추적

## done

### sprint-4 — 플러그인 v0.4.0 (2026-04-17)

ax-build + ax-qa + ax-review code. 개발팀 역할 전체 사이클.

- B-AXBUILD: `ax-build` 스킬 — 7단계 플로우 (plan → 공통 기반 → 실행 → 오너 확인 → 머지 → 최종 확인 → QA). Phase B를 ax-define에서 이동.
- B-ORCHESTRATOR: `ax-build-orchestrator.sh` — version branch + 워크트리 + tmux 세션 + 머지 자동화
- B-PLANNER: `planner` 에이전트 — gap 분석 + 실행 전략(워크트리 여부) 결정
- B-EXECUTOR: `executor` 에이전트 — TDD + backpressure 구현
- B-AXQA: `ax-qa` 스킬 — 통합 테스트 + code review + PR→main
- B-AXREVIEWCODE: `ax-review code` 타입 — stub → 7종 체크리스트 구현
- B-DESIGNMOD: ax-design SKILL.md 수정 — ax-build 호출 시 워크트리 실행 가능
- B-DEFINEMOD: ax-define SKILL.md 수정 — Phase B 제거 (scope 확정까지만)
- BACKLOG inbox 8건 해소: tmux 세션 관리, 디자인 통합, 스펙 변경 전파, Story 분리 기준, DS 순차성, 포트 할당, 빌드→QA 흐름

### sprint-3 — 플러그인 v0.3.0 (2026-04-16)

ax-design 스킬 신규 구현. 컴포넌트 단위 오너 확정 → 조합 패러다임.

- B-AXDESIGN: `ax-design` 스킬 — 8단계 플로우 (DS 토큰 확인 → 오너 인터뷰 → UX 플로우 → Story별 분기 → 컴포넌트 확정 → 전체 구성 → 게이트 → 프리뷰)
- B-UXDESIGNER: `ux-designer` 에이전트 — UX 플로우 설계 + 컴포넌트 필요 목록 산출
- B-DESIGNBUILDER: `design-builder` 에이전트 — DS 위에서 컴포넌트 개발 + 전체 구성
- B-DSGATE: `ds-completeness-check.sh` + `design-gate.sh` — DS 토큰 완성도 + DS 준수 린트 + 레이아웃 규칙
- B-CHECKEVAL: CheckEval 동적 체크리스트 — UX 기반 Yes/No 자동 생성 + 실패→재작업 자동 변환
- B-HOOKS: UserPromptSubmit DS 자동 주입 + PostToolUse DS 린트 훅
- B-REFS: references 8종 이식 (team-design) + reference-readme-template 부분 태깅 확장

### sprint-2 — 플러그인 v0.2.0 (2026-04-16)

Phase B 인프라 + 버전 전략 재설계 + 병렬 개발 설계.

- B-PHASEB: `phase-b-setup.sh` — Phase A 산출물 커밋 → 폴더 승격 → version branch → Story별 worktree 생성. `ax-define/SKILL.md` Phase B 단계 구현.
- B-VERSTRAT: 버전 전략 재설계 — "JTBD 분리 → 복수 버전" 폐기, minor(Story 분해) + patch(hotfix) 이원 체계. `jtbd.md`, `slc.md`, `semver.md`, `scope.md` 템플릿 갱신.
- B-DOCCHECK: `doc-checklist.md` diff 기준을 version branch 기점으로 변경.
- B-PARSPEC: `docs/specs/parallel-dev-spec.md` — v0.3 Build 오케스트레이션 설계 (파일 의존성/머지 순서/Story별 태스크 계획).

### hotfix v0.1.2 — ax-review doc 평가 대상 한정 (2026-04-16)

yoyowiki v0.1.1 도그푸딩에서 발견. working tree diff에 §수정 계획 밖 잔재가 섞이면 FAIL 오판이 남.

- B-DOCSCOPE: `doc-checklist.md` 검증 입력에 "평가 대상 한정 규칙" 추가 — §수정 계획에 명시된 파일에만 체크리스트 적용, 나머지는 판정하지 않음. `SKILL.md` doc 동작 3번 스텝에도 동일 규칙 명시.

### hotfix v0.1.1 — Phase A 구조 개선 (2026-04-15)

yoyowiki 도그푸딩에서 발견된 버그 3종 수정. sprint 밖 hotfix 진행.

- B-AUQGUARD: `product-owner` 에이전트에 `AskUserQuestion` 미가용 하드 가드 추가 — 실패 시 질문 목록만 작성하고 즉시 중단, 자체 추론 금지. (yoyowiki에서 에이전트가 6개 질문 전부 자답한 사고 대응)
- B-INTERVIEWRT: Phase A 2단계를 B안으로 구조 변경 — 서브에이전트가 interview.md에 질문 목록만 작성 → 메인 세션이 AskUserQuestion 호출 → 답을 다음 Task 호출 입력으로 전달. 작성/인터뷰 엔진 분리 유지.
- B-PHASEAFILE: Phase A 산출물 6개 → 3개로 축소 — `intake.md` / `interview.md` / `scope.md`만 유지. `jtbd.md` / `story-map.md` / `slc.md`는 폐지하고 scope.md 해당 섹션으로 단계별 in-place 기록. (downstream이 읽는 건 scope.md 한 장뿐)

### sprint-1 — 플러그인 v0.1.0 (2026-04-15)

- B-AXDEFINE: `ax-define` 스킬 — Phase A(intake/interview/JTBD/Story Map/SLC/semver) + Phase C(plan/write/review). references 6종 + scope.md 템플릿. 에이전트 2개(`product-owner`, `analyst`)
- B-AXREVIEW: `ax-review` 스킬 — 범용 리뷰 (codex 위임). doc 타입 구현 + code/pr stub
- B-INSTALL: `plugin/scripts/install-local-skills.sh` — Codex `~/.codex/skills/ax-review/` + Claude 플러그인 캐시 동기화
- B-AGENTS: 루트 `AGENTS.md` 신설 — Claude/Codex 호출 규약 정리
