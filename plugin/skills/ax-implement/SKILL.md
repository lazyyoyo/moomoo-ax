---
name: ax-implement
description: "구현 stage 1회. preflight → build loop (subagent 호출) → review → test. Use when: /team-ax:ax-implement, 구현, 빌드"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(bash ${CLAUDE_SKILL_DIR}/scripts/*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/*), Bash(git:*), Bash(npm:*), Bash(bun:*), Bash(npx:*), Bash(jq:*), Bash(which:*), Bash(pgrep:*), Bash(curl:*), Task, TodoWrite
---

# /team-ax:ax-implement

구현 stage 1회. skill 1회 호출이 전체 stage (preflight → build loop → review → test).

**핵심 원칙**
- **태스크당 fresh context** 는 subagent 호출 (`Task` tool) 로 확보. SKILL.md 본문은 계속 돌되, 매 태스크마다 executor 또는 design-engineer subagent 에 구현을 위임
- **plan.md 는 살아있는 문서**. Read tool 로 최상단 미완료 태스크 선택, Edit tool 로 체크박스 갱신 및 fix task 삽입
- **fix task 규약** — 태스크 실패 시 원 태스크는 `- [ ]` 유지. 원 태스크 아래에 fix task 추가. fix 완료 후 원 태스크 재시도 (최상단 미완료로 자연 복귀)
- **scripts 는 `${CLAUDE_SKILL_DIR}/scripts/...` 절대 경로로 호출**. cwd 는 구현 대상 repo

## 입력

- 구현 대상 repo (cwd) — `plan.md` 내장 필수. `package.json` + `ARCHITECTURE.md` 권장
- `plan.md` 는 `- [ ] T-XXX <설명>` 형식의 태스크 목록
- (선택) `DESIGN_SYSTEM.md`, `API_SPEC.md`, `specs/`, `flows/` 등

## 출력

- 태스크별 구현 코드 + 커밋
- 갱신된 `plan.md` (`- [x]` 마킹 + 실패 시 fix task 누적)
- review / test 결과 로그 (subagent 판정 + script JSON)

## 동작 순서

### [plan] — gap 인지 (축소)

planner subagent 는 v0.3 엔 생략. fixture 에 `plan.md` 가 이미 내장되어 있다는 가정. 실 프로젝트 대응 (planner 도입) 은 v0.4.

1. Bash tool 로 `git status --porcelain` 실행해서 working tree clean 확인. 미커밋 변경 있으면 오너에게 보고 후 대기
2. Read tool 로 `plan.md` 훑기 — 태스크 목록 파악. design 산출물 (flows/, mockup/, specs/) 있으면 대조해 gap 인지

### [preflight]

**참조**: `${CLAUDE_SKILL_DIR}/references/preflight-checklist.md`

Bash tool 로 필요한 체크만 **순차 실행** (복합 명령 `&&` 대신 단계별 실행 — permission prefix 매칭 때문):

- **ARCHITECTURE.md 기술 스택**: Read tool 로 읽고 이번 태스크에 필요한 라이브러리 식별
- **라이브러리 설치 여부**:
  1. Bash tool 로 `jq -r '.dependencies + .devDependencies | keys[]' package.json` 실행 → stdout 에 설치된 목록
  2. 목록에 원하는 `<lib>` 없으면 `npm install <lib>` (또는 `bun add <lib>`) 실행 + ARCHITECTURE.md 에 기록
  3. 신규 의존성은 문서 먼저 → 설치 순서 준수
- **CLI preflight** (필요한 것만. 각 단계 분리 실행):
  1. Bash tool 로 `which supabase` — exit 0 이면 Bash tool 로 `supabase projects list` 별도 호출. exit 1 이면 skip
  2. `which vercel` 동일 패턴 → `vercel whoami`
  3. `which gh` 동일 패턴 → `gh auth status`
  - CLI 있고 인증됨 → 직접 수행. 없거나 실패 → 해당 작업만 오너에게 요청 (전체 block 아님)
- **디자인 시스템** (`DESIGN_SYSTEM.md` 있을 시): 컴포넌트 목록 참조. 목록에 없는 커스텀은 사유 기록 필수. token-only 스타일링 + i18n 리소스 경유

### [build loop] — 태스크당 subagent

**핵심 루프**. `- [ ]` 가 전부 소진될 때까지 반복.

각 iteration:

1. **태스크 선택** — Read tool 로 `plan.md` 열고 최상단 `- [ ] T-XXX` 를 1개 선택
2. **subagent 호출** (fully-qualified 네임스페이스 필수):
   - BE / API / 데이터 태스크:
     ```
     Task(subagent_type="team-ax:executor",
          description="T-XXX 구현",
          prompt="<태스크 본문 + 관련 spec 경로 + 검증 기준 + AGENTS.md 경로>")
     ```
   - FE / 목업 / UI 태스크:
     ```
     Task(subagent_type="team-ax:design-engineer", ...)
     ```
3. subagent 가 **구현 + Bash tool 로 `bash ${CLAUDE_SKILL_DIR}/scripts/run_checks.sh` 실행해 통과 확인 + 태스크별 커밋** 까지 완료 후 결과 보고
4. **reviewer subagent 호출** — 태스크 diff 리뷰:
   ```
   Task(subagent_type="team-ax:reviewer",
        description="T-XXX 리뷰",
        prompt="diff 범위 + spec 경로. APPROVE 또는 REQUEST_CHANGES 로 판정")
   ```
5. **판정별 처리**:
   - APPROVE → Edit tool 로 `plan.md` 의 해당 `- [ ]` → `- [x]` 로 변경 후 다음 iteration (1 로)
   - REQUEST_CHANGES → 단순 이슈면 해당 subagent 에 재위임 (최대 1회). 구조적 이슈면 → 6
6. **fix task 생성** (실패 시):
   - 원 태스크 라인은 `- [ ]` 그대로 유지
   - 원 태스크 라인 바로 아래에 다음 2줄 삽입 (Edit tool):
     ```
     > 실패 (fix-<n>): <간결한 원인 요약>
     - [ ] T-FIX-<원태스크 id>-<n> <수정 할 일 설명>
     ```
   - `<n>` 은 이 원 태스크에 대해 기존 fix 개수 +1
   - **fix depth <n> 가 3 을 초과하면** 오너에게 개입 요청 메시지 출력 후 **loop 중단**:
     ```
     [AX_IMPLEMENT_BLOCKED] T-XXX 가 3회 fix 시도에도 완료되지 않음. 오너 확인 필요.
     ```
   - 이후 다음 iteration (1 로). 최상단 미완료가 새로 삽입된 fix task 이므로 자연스럽게 fix 를 먼저 소비
   - fix task 가 완료되면 원 태스크가 다시 최상단 미완료가 되어 재시도
7. **모든 `- [ ]` 소진** → [review] 로

### [review] — 전체 변경 크로스커팅

**참조**: `${CLAUDE_SKILL_DIR}/references/review-checklist.md`

1. **reviewer subagent 호출** — 이번 stage 의 전체 diff 에 대해 크로스커팅 리뷰:
   ```
   Task(subagent_type="team-ax:reviewer",
        description="stage 전체 리뷰",
        prompt="git log + diff 범위. spec 정합성, 보안, silent failure, 텍스트 하드코딩, 반복 패턴 검출")
   ```
2. **blocking gate** — Bash tool 로 `bash ${CLAUDE_SKILL_DIR}/scripts/run_review_checks.sh` 실행
   - exit 0 → 통과
   - exit 1 → 필요한 수정 태스크를 `plan.md` 에 새 `- [ ]` 로 추가하고 [build loop] 로 복귀
   - exit 2 → 필수 도구 미설치 (`gitleaks`, `npx`, `python3`, `jq`). 오너에게 알림 후 중단
3. reviewer 판정 REQUEST_CHANGES 면 해당 이슈도 plan.md 에 태스크로 추가 후 [build loop] 복귀

### [test]

**참조**: `${CLAUDE_SKILL_DIR}/references/backpressure-pattern.md`

1. **전체 체크 재실행** — Bash tool 로 `bash ${CLAUDE_SKILL_DIR}/scripts/run_checks.sh` 실행. 모두 pass 확인
2. **dev 서버 검증** (fixture / 프로젝트에 dev 서버가 있으면):
   - 서버 기동 확인 후 Bash tool 로 `bash ${CLAUDE_SKILL_DIR}/scripts/dev_server_check.sh <url>` 실행
   - 오너에게 URL 안내 전 HTTP 200 확인 필수. 서버 미실행 시 URL 전달 금지

## 가드레일

**참조**: `${CLAUDE_SKILL_DIR}/references/security-rules.md`

- **텍스트 하드코딩 절대 금지** — 모든 UI 텍스트는 i18n / copy 시스템 경유
- **보안 하드코딩 절대 금지** — 키/토큰/시크릿/쿠키값은 환경 변수로만
- **민감정보 로그 출력 금지**
- **env 파일 읽기 금지** — `.env` 는 cat/read 하지 않는다. 변수명만 `.env.example` 에서 확인
- **placeholder/stub 금지** — `// TODO: implement later` 남기지 말 것
- **backpressure** — lint + typecheck + test + build 통과 전 다음 태스크 진행 금지. 태스크 = 커밋 하나
- **DESIGN_SYSTEM 토큰-only** — 색상/간격/폰트 직접 값 금지
- **반복 패턴 3회 이상** → 오너 보고 (reviewer 판단)

## plan.md 갱신 규칙

- **순차 실행**: 태스크 완료 시 SKILL.md 본문이 Edit tool 로 `- [ ]` → `- [x]` 직접 갱신
- **병렬 실행은 v0.3 비적용** — subagent 를 병렬로 호출하지 않는다 (동시 plan.md Edit 시 경합)
- 발견한 버그는 해결하거나 plan 에 기록 (무시 금지)

## 완료

모든 `- [ ]` 가 `- [x]` 가 되고 [review] / [test] 통과하면 이 stage 종료. 드라이버 (`scripts/ax_product_run.py`) 가 결과를 `.harness/runs/<run_id>.ndjson` 에 기록하고 worktree 를 정리한다.

## 참조

- `${CLAUDE_SKILL_DIR}/references/preflight-checklist.md` — build 시작 전 체크리스트
- `${CLAUDE_SKILL_DIR}/references/backpressure-pattern.md` — Ralph backpressure + fresh context
- `${CLAUDE_SKILL_DIR}/references/review-checklist.md` — pr-review-toolkit 기반 리뷰 항목
- `${CLAUDE_SKILL_DIR}/references/security-rules.md` — 보안 하드코딩 / 로그 / env 규칙
- `${CLAUDE_SKILL_DIR}/templates/PLAN_TEMPLATE.md` — plan.md 템플릿 (v0.4 planner subagent 도입 시 사용)
