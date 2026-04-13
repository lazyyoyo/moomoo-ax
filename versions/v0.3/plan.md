# v0.3 — product loop 먼저 (team-ax/ax-implement 1 stage 완성)

## 한 줄 목표

> **team-product/product-implement 를 team-ax/ax-implement 로 포팅해서 `src/loop.py` (levelup harness) 를 경유하지 않는 단일 stage 를 격리 static fixture 에서 실행. skill 1회 호출이 전체 stage (plan 축소 → preflight → build loop → review → test). 태스크당 fresh context 는 subagent 호출로 제공.**

## 방향 전환 배경

원래 v0.3 plan 은 levelup loop 을 먼저 업그레이드하는 구조였다. v0.2 E 에서 "뭘 개선할지" 가 사전 정의 안 된 채 SKILL.md 를 추상 압축만 해 공허했다. 메모리 `feedback_loop_build_order.md` 의 원칙 — **product → meta → levelup** — 에 따라 순서를 뒤집음. PROJECT_BRIEF 의 3 레이어 정의는 유지, 구축 순서만 변경.

이후 반복적 축소:

- **관찰 인프라 전체 v0.4 이월** (Codex 2차 리뷰) — Stop hook DB insert idempotency 위험. v0.3 는 parent-side 로컬 로그만.
- **Codex 3차 review 는 security/정합성 과잉으로 대부분 revert** — v0.3 원칙 "돌아가는가 이진 기준" 과 불일치.
- **scripts 대폭 축소 (10 → 4)** (Ralph playbook 참고) — plan.md 파싱/갱신은 LLM 이 Read/Edit tool 로 직접. git status / 라이브러리 / CLI 확인은 인라인 쉘.
- **Ralph Stop hook 제거 + 드라이버 축소** — skill 1회 호출이 전체 stage 완주. 태스크당 fresh context 는 subagent 호출 (Task tool) 이 담당. Stop hook 의 block+재주입 자체 루프 불필요.

## 범위 원칙

- **1 stage only**: ax-implement 만. ax-qa / ax-design / ax-init / ax-deploy 는 v0.4~v0.5.
- **product loop 단독 실행**: `src/loop.py` 경유 금지. 전용 드라이버만.
- **이진 기준**: "돌아가는가 / 안 돌아가는가". 비용/시간 최적화는 v0.5+.
- **skill 1회 = stage 1회**: 내부 build loop 에서 태스크 순차 소비. 태스크당 subagent 호출로 fresh context.
- **levelup smoke, 관찰 인프라, dogfooding 은 v0.4 이월**.
- **허브 CLAUDE.md 준수**: rubato / haru / rofan-world 파일 직접 수정 금지. 격리 static fixture 만 사용.
- **labs/ax-qa 동결 유지**. **rnd/ 건드리지 않음** (v1.x).

## Codification 기준

| 자연어로 유지 | script/코드로 분리 |
|---|---|
| spec 해석, gap 분석, 태스크 선택 | 여러 명령 조건부 조합 (lint+typecheck+test+build) |
| plan.md 체크박스 갱신 (Read/Edit tool) | 복잡 파싱 (ARCH.md ↔ package.json ↔ import) |
| fix task 삽입 판단 및 작성 (Edit tool) | 다중 도구 래퍼 (gitleaks + eslint + arch_compliance) |
| 코드 품질 리뷰 | dev server 상태 체크 (pgrep + curl) |

**R-LEN / R-DRY 같은 "검증 규칙 AST 추출" 은 타깃 아님** (v0.2 F 에서 잘못 설정된 방향). 오너 의도는 **절차적 결정론 step 만 script 로 분리**.

## Phase 0 — 리서치 ✅ 완료 (2026-04-11)

- `docs/claude-code-spec/` 9 파일 초안
- `notes/v0.3-experiments/exp-01..06` 실험 로그
- `notes/2026-04-11-v0.3-feasibility.md` — Path A (하이브리드) 채택

## Phase 1a — claude.py 옵션 확장 ✅ 완료 (2026-04-12)

- `src/claude.py` — `allowed_tools` / `permission_mode` / `plugin_dir` / `bare` / `setting_sources` 옵션 + `parse_stream_json()` + `tool_events` 반환
- 단위 테스트 87/87 통과
- **`--bare` 실전 사용 금지** (exp-07 에서 auth 차단 확인). `bare=False` 가 기본값.

## Phase 1b — exp-07 Stop hook 실증 ✅ 완료 (2026-04-13)

- plugin Stop hook 이 `claude -p --plugin-dir` 자식 세션에서 완전 정상 발화 (참고용)
- v0.3 방향 전환 후 Stop hook 자체는 사용하지 않음. 기록만 보존 — v0.4+ 에서 자동 루프 필요할 때 재참조.

---

## Phase A — product loop: team-ax/ax-implement 완성

> **"team-product/product-implement 를 team-ax/ax-implement 로 포팅. skill 1회 호출이 전체 stage. 태스크당 subagent 호출로 fresh context. 격리 static fixture 에서 수동 확인."**

### A.1 SKILL.md 본체 작성

- [ ] **A.1.1 `plugin/skills/ax-implement/SKILL.md` 본문 리팩터**
  - frontmatter `allowed-tools`: `Read, Write, Edit, Grep, Glob, Bash(bash ${CLAUDE_SKILL_DIR}/scripts/*), Bash(python ${CLAUDE_SKILL_DIR}/scripts/*), Bash(git:*), Bash(npm:*), Bash(bun:*), Bash(npx:*), Bash(jq:*), Bash(which:*), Bash(pgrep:*), Bash(curl:*), Task, TodoWrite`
  - 본문 구조 (team-product/product-implement 기반, v0.3 축소):
    - **삭제**: Step 0 (.phase), Step 0a (토큰 스냅샷), [simplify], Codex adversarial-review
    - **[plan] 축소**: fixture 에 plan.md 가 내장되어 있으므로 planner subagent 생략. 대신 `!\`git status --porcelain\`` 로 clean 확인 + Read tool 로 plan.md 훑어 gap 인지만
    - **[preflight]**: 인라인 쉘로 ARCH/DS/라이브러리/CLI 체크. 체크리스트 결과를 plan.md 하단 "preflight 로그" 섹션에 Edit tool 로 추가
    - **[build loop]** (핵심):
      1. Read tool 로 `plan.md` 열고 최상단 `- [ ]` task 1개 선택
      2. 태스크 종류에 따라 `Task(subagent_type="team-ax:executor", ...)` (BE) 또는 `Task(subagent_type="team-ax:design-engineer", ...)` (FE) 호출 — **태스크당 subagent 1회, fresh context**. fully-qualified 네임스페이스 필수 (bare name 은 built-in/프로젝트 agent 와 충돌 가능, `docs/claude-code-spec/agent.md` 참조)
      3. subagent 가 구현 + `!\`bash ${CLAUDE_SKILL_DIR}/scripts/run_checks.sh\`` 통과 + 태스크별 커밋까지 완료
      4. `Task(subagent_type="team-ax:reviewer", ...)` — 태스크 diff 리뷰. APPROVE 시 다음 단계, REQUEST_CHANGES 시 → 6
      5. Edit tool 로 `- [ ]` → `- [x]`
      6. 실패 시 원 태스크 `- [ ]` 유지 + 원 태스크 아래에 `> 실패 (fix-<n>): <reason>` 인용구 추가 + `- [ ] T-FIX-<orig>-<n> <설명>` 삽입. fix depth > 3 이면 오너 개입 요청 후 루프 중단
      7. fix task 완료 시 원 태스크로 자연스럽게 복귀 (최상단 미완료가 원 태스크)
      8. `- [ ]` 전부 소진 시 [review] 로
    - **[review]**: `Task(subagent_type="team-ax:reviewer", ...)` + `!\`bash ${CLAUDE_SKILL_DIR}/scripts/run_review_checks.sh\`` (유일 blocking gate). red 면 필요 태스크 plan.md 에 추가 후 build loop 재진입
    - **[test]**: `!\`bash ${CLAUDE_SKILL_DIR}/scripts/run_checks.sh\`` 전체 + (fixture 에 dev 서버 있을 때) `!\`bash ${CLAUDE_SKILL_DIR}/scripts/dev_server_check.sh <url>\``
  - 가드레일 (team-product 원문 반영): 텍스트/보안 하드코딩 금지, env 파일 읽기 금지, placeholder 금지, backpressure (단계 통과 전 다음 금지)

### A.2 scripts 구현

**4개만 신규**. 나머지 절차 (plan.md 파싱/갱신, git status, 라이브러리 확인, CLI 확인) 는 자연어 + 인라인 쉘로. Progressive Codification 원칙.

위치: `plugin/skills/ax-implement/scripts/`. 각자 stdout 에 JSON, exit code 로 pass/fail.

- [ ] **A.2.1 `run_checks.sh`**
  - `package.json` 의 `scripts` 에서 `lint` / `typecheck` / `test` / `build` 자동 감지 → 존재하는 것만 순차 실행 → 실패 즉시 exit
- [ ] **A.2.2 `arch_compliance.py`**
  - `ARCHITECTURE.md` 의 "기술 스택" 섹션 파싱 → `package.json` 설치 목록 대조 → `src/**` import grep → 3-way 결과 JSON
  - 명시 but 미설치 / 설치 but 미사용 / 미명시 but 설치 3가지 케이스 리포트
  - **단독 호출 금지**. `run_review_checks.sh` 내부에서만 사용
- [ ] **A.2.3 `run_review_checks.sh` (유일 blocking review gate)**
  - 실행 순서: `gitleaks detect --no-banner` → `npx eslint --max-warnings 0 <changed files>` → `python scripts/arch_compliance.py`
  - 셋 중 하나라도 미설치 → **exit 2 (setup failure)**. warn & skip 금지
  - 셋 다 실행되고 하나라도 red → exit 1. 전부 green → exit 0
  - 각 결과 stdout 에 JSON summary 로 누적 출력
- [ ] **A.2.4 `dev_server_check.sh <url>`**
  - `pgrep -f "next dev\|bun dev\|vite"` + `curl -sS -o /dev/null -w "%{http_code}" <url>` → 200 이 아니면 exit 1

각 script 에 `tests/test_*.{py,sh}` 추가. 최소 pass/fail 2 케이스씩.

### A.3 references / templates 이관

team-product 원문을 plugin 경로로 그대로 복사 (자연어 판단용 문서는 수정 없음):

- [ ] **A.3.1 `plugin/skills/ax-implement/references/preflight-checklist.md`** (team-product 원문)
- [ ] **A.3.2 `plugin/skills/ax-implement/references/review-checklist.md`** (원문)
- [ ] **A.3.3 `plugin/skills/ax-implement/references/security-rules.md`** (원문)
- [ ] **A.3.4 `plugin/skills/ax-implement/references/backpressure-pattern.md`** (원문)
- [ ] **A.3.5 `plugin/skills/ax-implement/templates/PLAN_TEMPLATE.md`** (원문, v0.4+ 에서 planner subagent 도입 시 사용)

### A.4 subagents 포팅

태스크당 fresh context 확보. skill 본문은 길지만 subagent 호출 시 컨텍스트 분리됨.

- [ ] **A.4.1 `plugin/agents/executor.md` 신규**
  - team-product/agents/executor.md 기반. BE 구현 전담 (TDD + 태스크별 커밋 + backpressure)
  - tools: `Read, Grep, Glob, Bash, Write, Edit`
  - model: sonnet
- [ ] **A.4.2 `plugin/agents/design-engineer.md` 신규**
  - team-product/agents/design-engineer.md 기반. FE 구현 전담 (목업 → API 연결 + 디자인 시스템 토큰 준수)
  - tools: `Read, Grep, Glob, Bash, Write, Edit`
  - model: sonnet
- [ ] **A.4.3 `plugin/agents/reviewer.md` 신규**
  - team-product/agents/reviewer.md 기반. 읽기 전용 (APPROVE / REQUEST_CHANGES)
  - tools: `Read, Grep, Glob, Bash`
  - model: opus
- [ ] **A.4.4 planner / qa 는 v0.3 생략**
  - fixture 에 plan.md 내장이라 planner 필요 없음
  - qa subagent 는 ax-qa 포팅 (v0.4) 과 같이 도입

### A.5 드라이버 (얇게)

> **"단발 `claude -p` wrapper + worktree 생성/삭제 + 로그 저장. 자동 판정 없음 (v0.3 는 수동 확인)."**

- [ ] **A.5.1 `scripts/ax_product_run.py` 신규 작성**
  - 위치: 프로젝트 루트 `scripts/`
  - 인자: `--fixture <path>`, `--plugin-dir <path>` (기본 `<repo>/plugin`)
  - 동작:
    1. `run_id = uuid4()` 발행
    2. `git -C <fixture_root> worktree add --detach $TMPDIR/ax-run-<run_id>` — **`--detach` 사용으로 branch 생성 없음**. fixture repo 에 `ax-run/*` ref 누적 방지
    3. `src/claude.py:call(cwd=worktree_root, ...)` 호출 — `plugin_dir=<abs>/plugin`, `setting_sources="project,local"`, `output_format="stream-json"`, `permission_mode="acceptEdits"`, `include_hook_events=True`
    4. stream-json stdout 을 `.harness/runs/<run_id>.ndjson` 에 그대로 기록 (파싱 안 함)
    5. worktree 경로를 stdout 에 출력 (사람이 결과 확인용)
    6. try/finally 로 `git -C <fixture_root> worktree remove --force $TMPDIR/ax-run-<run_id>` + `git -C <fixture_root> worktree prune` (stale metadata 정리)
    7. **fixture repo cleanup 검증**: `git -C <fixture_root> for-each-ref refs/heads/ax-run/` 결과가 빈지 + `git -C <fixture_root> worktree list` 에 ax-run 경로 없는지 확인. 남아있으면 stderr 에 WARN 출력
  - exit code: subprocess exit code 그대로 전달 (자동 판정 안 함)
  - **`src/loop.py` 는 호출하지 않음**
- [ ] **A.5.2 `src/claude.py` 에 옵션 추가**
  - `include_hook_events=False` — True 면 CLI 에 `--include-hook-events` 추가
  - `cwd=None` — 지정되면 subprocess 의 cwd 로 전달
  - 단위 테스트 추가
- [ ] **A.5.3 `tests/test_ax_product_run.py`**
  - mock `claude.call()` 로 드라이버 흐름 검증 (worktree 생성/cleanup + cwd 전달 확인)

### A.6 fixture — 격리 static 템플릿 + git worktree

fixture 원본을 readonly 템플릿으로 두고, driver 가 매 run `git worktree add` 로 격리 복사본 생성. 자식 세션 cwd = worktree. 종료 시 worktree 제거. (security sandbox 는 아님 — v0.4+ 별도 이슈)

- [ ] **A.6.1 `labs/ax-implement/input/static-nextjs-min/` 템플릿 신규**
  - 최소 Next.js + TypeScript + ESLint + i18n + DESIGN_SYSTEM 토큰
  - `versions/v0.3-fixture/plan.md` 내장 — T-001~T-003 수준 2~3개 태스크 (예: "T-001 Button 컴포넌트 신규 — primary/secondary variant", "T-002 유닛 테스트", "T-003 스토리북 엔트리")
  - `ARCHITECTURE.md` + `DESIGN_SYSTEM.md` 최소
  - `package.json` scripts: lint / typecheck / test / build 전부 존재
  - **독립 git repo 로 init** (moomoo-ax submodule 아님). 최초 `git init && git commit -m "seed"`
  - 템플릿은 readonly 운영 — 이후 템플릿 원본에 커밋 금지
- [ ] **A.6.2 driver 의 worktree (clean-up 용)**
  - A.5.1 step 2, 6 참조
  - worktree 경로: `$TMPDIR/ax-run-<run_id>/`
  - run 실패해도 try/finally 로 remove best-effort
- [ ] **A.6.3 moomoo-ax dogfooding 은 v0.4 로 명시 이월**

### A.7 end-to-end 수동 확인

- [ ] **A.7.1 첫 run**
  ```bash
  .venv/bin/python scripts/ax_product_run.py \
    --fixture labs/ax-implement/input/static-nextjs-min \
    --plugin-dir plugin
  ```
  - 실행 후 worktree 경로 stdout 에 출력됨
- [ ] **A.7.2 수동 확인**
  - worktree 안의 plan.md: 모든 `- [ ]` 가 `- [x]` 인가? fix task 가 생성됐다면 구조가 올바른가?
  - worktree 안의 git log: 태스크별 커밋이 있는가?
  - `run_review_checks.sh` 가 tool_events 에 호출됐고 마지막 exit 0 인가? (`.harness/runs/<run_id>.ndjson` grep)
  - **subagent 호출이 기대한 fully-qualified 이름인가** — ndjson 에서 `"tool":"Task"` 이벤트의 `subagent_type` 가 정확히 `team-ax:executor` / `team-ax:design-engineer` / `team-ax:reviewer` 중 하나인지 확인. bare name (`executor` 등) 이거나 빌트인 (`Explore`, `general-purpose` 등) 으로 fallback 됐으면 FAIL
  - 태스크마다 subagent 호출이 최소 1회 있는가?
  - moomoo-ax repo 와 fixture 템플릿 원본이 깨끗한가? (`git status` 둘 다)
  - **fixture repo 에 `ax-run/*` branch / worktree metadata 가 남지 않았는가** (`git for-each-ref refs/heads/ax-run/` + `git worktree list` 검증)
- [ ] **A.7.3 결과 노트 `notes/2026-04-1x-v0.3-phase-a-run.md`**
  - 위 체크리스트 통과 여부 + 관찰 + 비용/duration 기록

---

## Phase B — 마감

- [ ] **B.1 `versions/v0.3/report.md`** — Phase A 요약 + 측정치 + 회고
- [ ] **B.2 `HANDOFF.md`** — v0.4 진입용 (관찰 인프라 + dogfooding + levelup smoke + ax-qa/ax-design/planner subagent/자동 판정 스코프)
- [ ] **B.3 `BACKLOG.md` 갱신**
  - ready: product_runs Supabase 테이블 + 대시보드 카드 (v0.4), moomoo-ax dogfooding (v0.4), levelup loop smoke (v0.4), ax-qa 포팅 + qa subagent (v0.4), ax-design 포팅 (v0.5), `ax-autopilot` (v0.4), planner subagent + 자동 판정 (v0.4), simplify hook (v0.4)
  - inbox: v0.3 Phase A 에서 발견된 후속
- [ ] **B.4 `PROJECT_BRIEF.md` 버전 로드맵 업데이트**
- [ ] **B.5 PR 머지 + 태그 `v0.3.0`**

---

## Out of scope (v0.4+)

- **관찰 인프라 전체** (Supabase `product_runs` 테이블, intervention 결합 뷰, 대시보드 카드)
- **moomoo-ax 자체 dogfooding**
- **planner subagent + 자동 판정 (promise 검출 등)**
- **Ralph Stop hook 기반 자동 반복** (v0.3 에서는 수동 호출로 충분)
- **levelup loop smoke**
- **ax-qa 포팅 + Playwright MCP + qa subagent**
- **ax-design / ax-init / ax-deploy 포팅**
- **`ax-autopilot` 상위 오케스트레이터**
- **simplify hook (oh-my-claudecode 패턴)**
- **R-LEN / R-DRY AST 검증** — 타깃 아님
- **재현성 수치 기준선**
- **Claude Code `--resume` / Agent SDK** — 불필요 판정
- **team-ax 플러그인의 MCP 내장화**
- **rnd/** (meta loop trend/gate/evolver) — v1.x

---

## 작업 순서

```
Phase 0  (✅ 2026-04-11)
Phase 1a (✅ 2026-04-12)
Phase 1b (✅ 2026-04-13, Stop hook 실증 — v0.3 엔 미사용, 기록만)
    │
    ├─ Phase A  product loop ax-implement
    │    A.1 SKILL.md 본체
    │    A.2 scripts 4개
    │    A.3 references/templates 이관
    │    A.4 subagents 포팅 (executor, design-engineer, reviewer)
    │    A.5 드라이버 얇게 (worktree + claude -p wrapper)
    │    A.6 격리 static fixture 템플릿
    │    A.7 end-to-end 수동 확인
    │
    └─ Phase B  마감
         B.1 report / B.2 HANDOFF / B.3 BACKLOG / B.4 BRIEF / B.5 머지+태그
```

---

## 리스크

| # | 리스크 | 영향 | Mitigation |
|---|---|---|---|
| R1 | `-p` 슬래시 호출이 multi-line 인자를 못 받음 | 낮 | 단순 `"/team-ax:ax-implement"` 만 호출. 인자 불필요 (fixture 는 cwd) |
| R2 | Claude 가 scripts 를 호출하지 않고 "통과한 척" | 중 | A.7.2 수동 확인에서 `.harness/runs/<run_id>.ndjson` 의 tool_events 에 `run_review_checks.sh` 호출 확인 |
| R3 | subagent 호출 컨텍스트 가 비정상적으로 길어져 cost 폭발 | 중 | v0.3 는 fixture 규모 작음 (2~3 태스크). 실 프로젝트는 v0.4 |
| R4 | `arch_compliance.py` 가 ARCHITECTURE.md 구조 편차 흡수 못함 | 중 | fixture 는 표준 포맷 사용. 프로젝트별 편차는 v0.4 |
| R5 | `git worktree add` 가 기존 브랜치 충돌 / cleanup 실패 | 중 | run_id 기반 임시 브랜치 (`ax-run/<uuid>`) + try/finally remove + 주기적 `git worktree prune` |
| R6 | 무한 fix task 생성 루프 | 중 | SKILL.md Ralph 프로토콜에 fix depth > 3 시 오너 개입 중단 명시 |
| R7 | gitleaks / eslint 미설치 시 review gate 가 우회됨 | 해소 | `run_review_checks.sh` 가 미설치 감지 시 exit 2 (A.2.3) |
| R8 | 격리 static fixture 가 실 프로젝트 신호 부족 | 낮 | v0.3 는 "돌아가는가" 만 검증. 실 프로젝트 dogfooding v0.4 |
| R9 | SKILL.md 본문이 subagent 여러 개 호출하며 길어짐 → context 압박 | 낮 | v0.3 fixture 작음. context 압박 시 v0.4 에서 stage 분할 |
| R10 | subagent bare name (`executor`) 이 빌트인 또는 프로젝트 agent 로 fallback 되어 silent pass | 해소 | fully-qualified `team-ax:executor` 등 사용 (A.1.1 build loop step 2, 4) + A.7.2 수동 체크에서 tool_events 의 subagent_type 정확히 매칭 확인 |
| R11 | script 경로가 상대 (`scripts/run_checks.sh`) 라 fixture worktree 기준으로 찾음 → 실행 안 됨 | 해소 | `${CLAUDE_SKILL_DIR}/scripts/...` 절대 경로로 통일 (A.1.1) + allowed-tools 에 `Bash(bash ${CLAUDE_SKILL_DIR}/scripts/*)` 패턴 일치 |
| R12 | worktree branch (`ax-run/<run_id>`) 가 fixture repo 에 누적 → readonly 주장 깨짐 | 해소 | `git worktree add --detach` 로 branch 안 만듦 + cleanup 시 `worktree prune` + for-each-ref 검증 (A.5.1) |

---

## 성공 기준 (v0.3 전체)

1. **Phase A PASS (수동 확인)** — 격리 static fixture 에서 `scripts/ax_product_run.py` 1회 실행 후:
   - worktree 의 plan.md 태스크가 모두 `- [x]` (fix task 를 거쳐 최종 완료된 경우 포함)
   - worktree git log 에 태스크별 커밋 존재
   - 드라이버가 exit 0 + worktree 가 정상 제거됨
   - tool_events 에 `run_review_checks.sh` 성공 호출 + 태스크마다 subagent 호출 흔적
   - moomoo-ax repo 와 fixture 템플릿 원본은 미수정
2. **Phase B 마감** — report / HANDOFF / BACKLOG 정리 + v0.3.0 태그

북극성 지표 (오너 개입 횟수) 는 v0.3 에서 **측정 인프라 없음**. v0.4 의 관찰 인프라로 이월.

---

## 진행 메모

- 2026-04-11: Phase 0 완료 — 리서치 + 실험 6개 + 판정 리포트 (Path A 채택)
- 2026-04-12: Phase 1a 코드 완료 — claude.py 옵션 확장 + stream-json 파서.
- 2026-04-13: **방향 전환 v1** — product → meta → levelup 순서 확정.
- 2026-04-13: **exp-07 완료** — Stop hook 이 `-p --plugin-dir` 자식 세션에서 정상 발화 증명. 다만 v0.3 엔 사용 안 함.
- 2026-04-13: **Codex 1차 리뷰 반영** — Phase A 를 `src/loop.py` 밖 드라이버로 분리, dogfooding v0.4 이월, 관찰 인프라 v0.4 이월, review gate 단일화.
- 2026-04-13: **Codex 3차 리뷰는 대부분 revert** — security/정합성 과잉. v0.3 원칙과 불일치.
- 2026-04-13: **오너 루프 반영** — 실패 시 fix task 삽입 (원 태스크 `[ ]` 유지) + fix depth > 3 차단.
- 2026-04-13: **scripts 4개로 축소** — plan.md 파싱/갱신은 Read/Edit tool 로 직접, git status / 라이브러리 / CLI 확인은 인라인 쉘.
- 2026-04-13: **Ralph Stop hook 제거 + 드라이버 축소** — skill 1회 호출이 전체 stage 완주. 태스크당 fresh context 는 subagent 호출 (Task tool) 이 담당. 드라이버는 단발 `claude -p` wrapper + worktree 생성/삭제 + 로그 저장. 자동 판정 없음 (수동 확인). subagents 포팅 추가 (A.4).
- 2026-04-13: **Codex 4차 리뷰 반영** — 3 findings 전부 유효 (실행 블로커): (1) script 호출을 `${CLAUDE_SKILL_DIR}/scripts/...` 절대 경로 + allowed-tools 매칭 (R11 해소), (2) subagent 를 `team-ax:<name>` fully-qualified 네임스페이스 + A.7.2 체크에서 정확 매칭 검증 (R10 해소), (3) worktree `--detach` + `prune` + branch 잔존 검증 (R12 해소).
