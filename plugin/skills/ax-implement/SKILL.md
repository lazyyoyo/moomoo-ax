---
name: ax-implement
description: "구현 stage 1회. preflight → build loop (Codex worker 호출) → review → test. Use when: /team-ax:ax-implement, 구현, 빌드"
allowed-tools: Read, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/*), Bash(bash ${CLAUDE_SKILL_DIR}/scripts/*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/*), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*), Bash(git:*), Bash(npm:*), Bash(bun:*), Bash(npx:*), Bash(jq:*), Bash(which:*), Bash(pgrep:*), Bash(curl:*), TodoWrite
---

# /team-ax:ax-implement

구현 stage 1회. skill 1회 호출이 전체 stage (preflight → build loop → review → test).

**핵심 원칙**
- **Claude 는 conductor**. 태스크 선택 / worker 입력 작성 / worker 결과 판정 / fix task 삽입만 담당
- **태스크당 fresh context** 는 Codex worker 1회 호출로 확보. executor 와 reviewer 는 항상 별도 session / 별도 결과 파일
- **plan.md 는 살아있는 문서**. Read tool 로 최상단 미완료 태스크 선택, Edit tool 로 체크박스 갱신 및 fix task 삽입
- **fix task 규약** — 태스크 실패 시 원 태스크는 `- [ ]` 유지. 원 태스크 아래에 fix task 추가. fix 완료 후 원 태스크를 즉시 닫고 reviewer-only 재검증은 만들지 않는다
- **scripts 는 `${CLAUDE_SKILL_DIR}/scripts/...` 절대 경로로 호출**. worker wrapper 는 `run_codex_worker.sh`, task file 생성은 `render_codex_task.py`
- **모델 라우팅은 wrapper 가 자동 선택** — 저위험 page/copy/test 성격 태스크는 `gpt-5.4-mini`, 공용 component/config 는 `gpt-5.3-codex`, `stage-final-review` 는 `gpt-5.4`. 필요할 때만 `--model` 로 override 한다

## 입력

- 구현 대상 repo (cwd) — `plan.md` 내장 필수. `package.json` + `ARCHITECTURE.md` 권장
- `plan.md` 는 `- [ ] T-XXX <설명>` 형식의 태스크 목록
- (선택) `DESIGN_SYSTEM.md`, `API_SPEC.md`, `specs/`, `flows/` 등

## Optional Target-Subdir Mode

호출 프롬프트에 아래 블록이 있으면 target-subdir mode 로 해석한다.

```text
[TARGET_SUBDIR]
dashboard
[/TARGET_SUBDIR]
```

- 현재 `cwd` 는 이미 target-subdir 루트다
- 수정 가능한 범위는 현재 subtree 내부뿐이라고 가정한다
- `plan.md` 와 `.harness/` 는 현재 `cwd` 안에 둔다
- 현재 subtree 와 부모 repo 의 기존 dirty 파일은 모두 baseline 으로 취급하고 blocker 로 삼지 않는다
- `../plugin`, `../src`, `../scripts`, `../labs` 같은 하네스 경로는 절대 수정하지 않는다

## 출력

- 태스크별 구현 코드 + worker 결과 파일 (`.harness/codex/<task-id>/...`)
- 갱신된 `plan.md` (`- [x]` 마킹 + 실패 시 fix task 누적)
- review / test 결과 로그 (Codex worker 결과 + script JSON)

## 동작 순서

### [plan] — gap 인지 (축소)

planner subagent 는 v0.3 엔 생략. fixture 에 `plan.md` 가 이미 내장되어 있다는 가정. 실 프로젝트 대응 (planner 도입) 은 v0.4.

1. Bash tool 로 `git status --porcelain` 실행해서 working tree clean 확인. 미커밋 변경 있으면 오너에게 보고 후 대기
   - 단, target-subdir mode 에서는 현재 `cwd` 기준 `git status --porcelain -- .` 로 baseline 만 파악하고 **block 하지 않는다**
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
- **환경/의존성 복구는 preflight 에서만**:
  - task loop 안에서 `npm install`, `bun add`, lockfile 수정 금지
  - `node_modules` 자체가 없거나 task 수행에 필수 의존성 설치가 명백히 필요한 경우에만 conductor 가 한 번 수행
  - worker 가 dependency missing 을 보고하면 다음 task 로 넘기지 말고 conductor 가 preflight 성격으로 처리
- **디자인 시스템** (`DESIGN_SYSTEM.md` 있을 시): 컴포넌트 목록 참조. 목록에 없는 커스텀은 사유 기록 필수. token-only 스타일링 + i18n 리소스 경유

### [build loop] — 태스크당 Codex worker

**핵심 루프**. `- [ ]` 가 전부 소진될 때까지 반복.

각 iteration:

1. **태스크 선택** — Read tool 로 `plan.md` 열고 최상단 `- [ ] T-XXX` 를 1개 선택
2. **executor task file 생성** — Bash tool 로:
   ```bash
   mkdir -p ".harness/codex/<task-id>/executor"
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_codex_task.py" \
     --role executor \
     --task-id "<task-id>" \
     --task-summary "<plan.md 의 태스크 문장>" \
     --output ".harness/codex/<task-id>/executor/task.md" \
     --relevant-file "plan.md" \
     --constraint "placeholder/stub 금지" \
     --constraint "text hardcoding 금지" \
     --constraint "보안 하드코딩 금지" \
     --constraint "npm install/bun add 같은 환경 복구 금지" \
     --constraint "broad checks 는 conductor 가 수행하므로 구현 중심으로만 작업" \
     --constraint "최종 응답은 JSON만 출력"
   ```
   - relevant_files 는 최소화한다: 현재 task target 파일 + 직접 참조해야 하는 spec 문서만 넘기고, broad repo 탐색을 유도하는 파일 나열은 피한다
3. **executor worker 호출** — Bash tool 로:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/run_codex_worker.sh" \
     --role executor \
     --task-id "<task-id>" \
     --task-summary "<plan.md 의 태스크 문장>" \
     --cd "$PWD" \
     --task-file ".harness/codex/<task-id>/executor/task.md" \
     --log-dir ".harness/codex/<task-id>/executor/logs"
   ```
4. **executor 결과 판정** — Read tool 로 `.harness/codex/<task-id>/executor/logs/result.json` 확인
   - `status=ok` → 5 로
   - `status=failed` → 8 로
   - `status=infra_error` → 기본은 중단. 단 `changed_files[]` 가 있고 conductor checks 가 pass 면 recoverable infra_error 로 간주하고 5 로 진행
   - `changed_files[]` 는 reviewer 입력 범위 계산에 사용
5. **conductor checks 실행** — worker 가 아니라 Claude conductor 가 deterministic script 로 수행:
   - 기본: `lint` + `typecheck`
   - 테스트 파일 변경 시: `test` 추가
   - `src/app/`, `page.tsx`, `layout.tsx`, `next.config.*`, `tsconfig.json` 변경 시: `build` 추가
   - Bash tool 로:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/run_task_checks.sh" \
     --step lint \
     --step typecheck \
     --output ".harness/codex/<task-id>/checks.json"
   ```
   - 필요한 step 만 추가한다. 결과 파일 `.harness/codex/<task-id>/checks.json` 을 reviewer 에 넘긴다
   - executor 가 `infra_error` 였더라도 `changed_files[]` 가 있고 `checks.json.status=pass` 면 recoverable infra_error 로 기록하고 reviewer 로 진행한다
6. **reviewer task file 생성** — Bash tool 로:
   ```bash
   mkdir -p ".harness/codex/<task-id>/reviewer"
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_codex_task.py" \
     --role reviewer \
     --task-id "<task-id>" \
     --task-summary "<plan.md 의 태스크 문장>" \
     --output ".harness/codex/<task-id>/reviewer/task.md" \
     --review-scope ".harness/codex/<task-id>/checks.json" \
     --review-scope ".harness/codex/<task-id>/executor/logs/result.json" \
     --review-scope "<changed-file-1>" \
     --review-scope "<changed-file-2>" \
     --review-scope "spec 정합성, silent failure, 하드코딩, conductor checks 결과 확인" \
     --spec-path "plan.md"
   ```
   - `<changed-file-n>` 은 executor `result.json.changed_files[]` 에서 읽어 반복 전달
7. **reviewer worker 호출 + 판정** — Bash tool 로:
   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/run_codex_worker.sh" \
     --role reviewer \
     --task-id "<task-id>" \
     --task-summary "<plan.md 의 태스크 문장>" \
     --changed-file "<changed-file-1>" \
     --changed-file "<changed-file-2>" \
     --cd "$PWD" \
     --task-file ".harness/codex/<task-id>/reviewer/task.md" \
     --log-dir ".harness/codex/<task-id>/reviewer/logs"
   ```
   이후 Read tool 로 `.harness/codex/<task-id>/reviewer/logs/result.json` 확인:
   - `verdict=APPROVE` → Edit tool 로 `plan.md` 의 해당 `- [ ]` → `- [x]` 변경 후 다음 iteration
   - `verdict=REQUEST_CHANGES` → 8 로
   - `verdict=ERROR` → `[AX_IMPLEMENT_BLOCKED] reviewer error` 로 오너 보고 후 중단
   - selected task 가 `T-FIX-<원태스크 id>-<n>` 패턴이면, `APPROVE` 시 fix task 와 원 태스크를 둘 다 `[x]` 로 닫고 `<orig>-retry` 같은 reviewer-only 재호출을 만들지 않는다
8. **fix task 생성** (실패 시):
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
9. **모든 `- [ ]` 소진** → [review] 로

### [review] — 전체 변경 크로스커팅

**참조**: `${CLAUDE_SKILL_DIR}/references/review-checklist.md`

1. **reviewer subagent 호출** — 이번 stage 의 전체 diff 에 대해 크로스커팅 리뷰:
   - 동일한 Codex reviewer 경로를 사용한다. 단 task id 는 `stage-final-review`
   - `.harness/codex/stage-final-review/reviewer/task.md` 를 생성하고 전체 diff / git log / plan.md 를 review scope 로 넘긴다
   - `stage-final-review` 는 wrapper 가 자동으로 final-review model (`gpt-5.4`) 로 라우팅한다
2. **blocking gate** — Bash tool 로 `bash ${CLAUDE_SKILL_DIR}/scripts/run_review_checks.sh` 실행
   - exit 0 → 통과
   - exit 1 → 필요한 수정 태스크를 `plan.md` 에 새 `- [ ]` 로 추가하고 [build loop] 로 복귀
   - exit 2 → 필수 도구 미설치 (`gitleaks`, `npx`, `python3`, `jq`). 오너에게 알림 후 중단
3. **v0.4 fixture pilot 에서는 stage-final-review 를 비재귀 audit 로 취급**
   - reviewer 판정 `REQUEST_CHANGES` 가 나와도 자동으로 새 태스크를 추가하지 않는다
   - 이 단계의 결과는 run note / backlog 용 evidence 로만 남긴다
   - 새 태스크 생성은 `run_review_checks.sh` 실패 같은 deterministic gate red 일 때만 허용
   - 목적은 fixture pilot 이 원 계획 검증을 넘어 recursive remediation loop 로 확장되는 것을 막는 것이다

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

- **순차 실행**: 태스크 완료 시 conductor 가 Edit tool 로 `- [ ]` → `- [x]` 직접 갱신
- **병렬 실행은 v0.4 비적용** — worker 를 병렬로 호출하지 않는다 (동시 plan.md Edit / cwd 충돌 방지)
- 발견한 버그는 해결하거나 plan 에 기록 (무시 금지)

## 완료

모든 `- [ ]` 가 `- [x]` 가 되고 [review] / [test] 통과하면 이 stage 종료. 드라이버 (`scripts/ax_product_run.py`) 가 결과를 `.harness/runs/<run_id>.ndjson` 에 기록하고 worktree 를 정리한다.

수동 확인 시에는 아래를 우선 본다.

- `.harness/codex/<task-id>/executor/logs/result.json`
- `.harness/codex/<task-id>/checks.json`
- `.harness/codex/<task-id>/reviewer/logs/result.json`
- `.harness/codex/stage-final-review/reviewer/logs/result.json`
- `plan.md` 의 `[ ] → [x]` 전환과 fix task 삽입 여부

## 참조

- `${CLAUDE_SKILL_DIR}/references/preflight-checklist.md` — build 시작 전 체크리스트
- `${CLAUDE_SKILL_DIR}/references/backpressure-pattern.md` — Ralph backpressure + fresh context
- `${CLAUDE_SKILL_DIR}/references/review-checklist.md` — pr-review-toolkit 기반 리뷰 항목
- `${CLAUDE_SKILL_DIR}/references/security-rules.md` — 보안 하드코딩 / 로그 / env 규칙
- `${CLAUDE_SKILL_DIR}/templates/PLAN_TEMPLATE.md` — plan.md 템플릿 (v0.4 planner subagent 도입 시 사용)
- `${CLAUDE_SKILL_DIR}/templates/CODEX_EXECUTOR_TASK_TEMPLATE.md` — executor worker 입력 템플릿
- `${CLAUDE_SKILL_DIR}/templates/CODEX_REVIEWER_TASK_TEMPLATE.md` — reviewer worker 입력 템플릿
