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

(없음)

## ready

### sprint-2 — 완료 → done 섹션으로 이관

### sprint-3 후보

(버전 전략 변경으로 분리 감지/의존성 분석 폐기 — v0.2에서 "하나의 minor + Story 분해" 모델로 전환)

## inbox (장기 후보)

- [dogfood] team-ax 자체 도그푸딩 — rubato 또는 rofan-world에 실제 `/ax-define` 1회 실행, 실측 보고서 작성 (sprint-1 비범위로 미룸)
- [feature] `ax-build` 스킬 — 제품 사이클의 build 단계 (Story Map의 Story 단위 worktree 분기 포함, 플러그인 v0.3+)
- [feature] `ax-design` / `ax-qa` / `ax-deploy` 스킬 — 나머지 제품 사이클 단계 (CHANGELOG 작성, `⏳ planned` 마커 제거 포함)
- [feature] `ax-review code` 타입 구현 — `references/code-checklist.md` 본격 작성 (ax-build 도입 시)
- [feature] `ax-review pr` 타입 구현 — `references/pr-checklist.md` 본격 작성 + sandbox 정책 확정 (`workspace-read` 추정, ax-deploy 도입 시)
- [feature] Hook 기반 자동 강제 — spec-lifecycle 4종 장치를 PreToolUse 훅으로 차단 (현재는 에이전트 규칙 + review만)
- [feature] Story 단위 worktree 병렬 실행 오케스트레이션 (플러그인 v0.3+)
- [feature] 의존성 그래프 기반 merge 순서 자동 관리 (플러그인 v0.3+ deploy)
- [infra] team-ax 자기 진화 — meta loop, 외부 패턴 자동 흡수 (PROJECT_BRIEF 장기 비전)
- [infra] 대시보드 연동 — 오너 개입 횟수 / 토큰 / iteration 등 북극성 지표 추적

## done

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
