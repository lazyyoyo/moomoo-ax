# v0.3 — product loop 먼저 (team-ax/ax-implement) + meta loop 조회 인프라

## 한 줄 목표

> **team-product/product-implement 를 team-ax/ax-implement 로 포팅해서 실제 돌아가는 product loop 1 stage 완성 + meta loop 조회 인프라로 실행 관찰. levelup loop 은 관찰 데이터가 쌓인 뒤 v0.4 에서 개시.**

## 방향 전환 배경

원래 v0.3 plan (2026-04-11 Phase 0 직후) 은 levelup loop 을 먼저 업그레이드하는 구조였다. 그런데:

- v0.2 E 에서 "뭘 개선할지" 사전 정의 없이 SKILL.md 를 추상 압축만 한 결과, levelup 이 공허했다.
- 메모리 `feedback_loop_build_order.md` 원칙: **product → meta → levelup**. levelup 우선은 대상 공허화 함정.
- PROJECT_BRIEF 의 3 레이어 정의는 유지. **구축 순서만 뒤집음**.

따라서 v0.3 는:

1. **Phase A**: product loop 의 ax-implement 를 먼저 완성 — team-product 원문을 자연어/script 기준으로 이관, Ralph Stop hook 패턴으로 plan.md 체크박스 소비 루프.
2. **Phase B**: meta loop 의 조회 인프라 — 실행을 DB/대시보드에서 관찰.
3. **Phase C**: 마감 + levelup loop smoke 를 v0.4 로 이월.

## 범위 원칙

- **1 stage only**: ax-implement 만. ax-qa / ax-design / ax-init / ax-deploy 는 v0.4~v0.5.
- **이진 기준**: "돌아가는가 / 안 돌아가는가". 비용/시간 최적화는 v0.5+.
- **levelup smoke 는 v0.4 이월**. v0.3 는 product + meta 까지만.
- **허브 CLAUDE.md 준수**: rubato / haru / rofan-world 파일 직접 수정 금지. Fixture 는 (1) moomoo-ax 자체 dogfooding 또는 (2) 격리 static fixture 에서만.
- **labs/ax-qa 동결 유지**. **rnd/ 건드리지 않음** (v1.x).

## Codification 기준 (이번 세션 재정의)

자연어 vs script 분리 원칙 (메모리 `feedback_progressive_codification.md`):

| 자연어로 유지 (LLM 강점) | script/코드로 분리 (결정론) |
|---|---|
| spec 어떻게 작성할지 판단 | git 명령, 파일 쓰기 |
| 에지 케이스 열거 | 템플릿 복사 |
| 코드 품질 판단 | 테스트/린트/빌드 실행 |
| 요구사항 해석 | plan.md 체크박스 파싱/갱신 |
| 반복 패턴 3회+ 의미 판정 | package.json ↔ ARCH.md ↔ import 정적 대조 |

**R-LEN / R-DRY 같은 "검증 규칙 AST 추출" 은 타깃 아님** (v0.2 F 에서 잘못 설정된 방향). 오너 의도는 **절차적 결정론 step 을 script 로 빼는 것**.

## Phase 0 — 리서치 ✅ 완료 (2026-04-11)

- `docs/claude-code-spec/` 9 파일 초안
- `notes/v0.3-experiments/exp-01..06` 실험 로그
- `notes/2026-04-11-v0.3-feasibility.md` — Path A (하이브리드) 채택

## Phase 1a — claude.py 옵션 확장 ✅ 완료 (2026-04-12)

당초 levelup 호출 업그레이드로 썼으나 **방향 전환 후 meta loop 호출 인프라로 재배치**. product loop 의 자식 세션 호출에 동일하게 쓰임.

- `src/claude.py` — `allowed_tools` / `permission_mode` / `plugin_dir` / `bare` / `setting_sources` 옵션 + `parse_stream_json()` + `tool_events` 반환
- `src/loop.py` — program.md 의 `call_options` 를 env 로 script.py 에 전달
- 단위 테스트 87/87 통과

---

## Phase A — product loop: team-ax/ax-implement 완성

> **"team-product/product-implement 구조를 team-ax/ax-implement 로 이관하되, 자연어와 script 를 명시적으로 분리. Ralph Stop hook 으로 plan.md 체크박스 소비 루프를 자식 세션 내부에서 자체 구동. end-to-end 로 실제 태스크 1개를 완주."**

### A.1 SKILL.md 본체 작성

- [ ] **A.1.1 `plugin/skills/ax-implement/SKILL.md` 본문 리팩터**
  - frontmatter `allowed-tools`: `Read, Write, Edit, Grep, Glob, Bash(scripts/**), Bash(git:*), Bash(npm:*), Bash(bun:*), Task, TodoWrite`
  - 본문은 team-product/product-implement/SKILL.md 를 기반으로 하되 다음 수정:
    - **삭제**: Step 0 (.phase 파일), Step 0a (토큰 스냅샷), [simplify] 단계 전체
    - **유지 (자연어)**: [plan] 의 gap 분석·phase 분할 판단, [preflight] 의 DS·ARCH 해석 판단, [build] 의 태스크 선택·구현, reviewer 판단, [verify] URL 전달 전 자연어 체크
    - **script 호출로 교체**: 하단 "scripts 호출 규약" 표 참고
  - Ralph 루프 프로토콜 명시: plan.md 에 `- [ ]` 가 남아있으면 최상단 1개 소비, 모두 `- [x]` 면 `<promise>AX_IMPLEMENT_DONE</promise>` 출력
- [ ] **A.1.2 scripts 호출 규약 섹션**
  - SKILL.md 본문에 표로 삽입:
    ```markdown
    | 시점 | 호출 |
    |---|---|
    | plan 시작 전 | !`python scripts/check_git_clean.py` |
    | preflight | !`python scripts/check_lib_installed.py <lib>` / !`python scripts/cli_preflight.py` |
    | build iter 시작 | !`python scripts/find_next_task.py plan.md` |
    | build iter 후 | !`bash scripts/run_checks.sh` / !`python scripts/mark_task_done.py plan.md <task_id>` |
    | review | !`python scripts/arch_compliance.py` / !`bash scripts/run_review_checks.sh` |
    | verify | !`python scripts/dev_server_check.py <url>` |
    ```

### A.2 scripts 구현

9개 신규 script. 각자 stdout 에 JSON 결과, exit code 로 pass/fail.

- [ ] **A.2.1 `plugin/skills/ax-implement/scripts/check_git_clean.py`**
  - `git status --porcelain` → 비어있으면 exit 0, 아니면 변경 목록 JSON + exit 1
- [ ] **A.2.2 `scripts/check_lib_installed.py <lib>`**
  - `package.json` 의 `dependencies` + `devDependencies` 에 `<lib>` 존재 여부
- [ ] **A.2.3 `scripts/cli_preflight.py`**
  - `which supabase` / `which vercel` / `which gh` / `which bun` + 각 `auth status` 확인 → JSON
- [ ] **A.2.4 `scripts/find_next_task.py <plan.md>`**
  - plan.md 파싱 → 최상단 `- [ ] T-XXX …` 반환 (task id + 본문). 없으면 exit 2 (ALL_DONE)
- [ ] **A.2.5 `scripts/mark_task_done.py <plan.md> <task_id>`**
  - 해당 T-XXX 라인의 `- [ ]` → `- [x]` 치환
- [ ] **A.2.6 `scripts/run_checks.sh`**
  - `package.json` 의 `scripts` 에서 `lint` / `typecheck` / `test` / `build` 자동 감지 후 존재하는 것만 순차 실행. 실패 즉시 exit
- [ ] **A.2.7 `scripts/arch_compliance.py`**
  - `ARCHITECTURE.md` 의 "기술 스택" 섹션 파싱 → `package.json` 설치 목록 대조 → `src/**` import grep → 3-way 결과 JSON
  - 명시 but 미설치 / 설치 but 미사용 / 미명시 but 설치 3가지 케이스 리포트
- [ ] **A.2.8 `scripts/run_review_checks.sh`**
  - `gitleaks detect --no-banner` + `npx eslint --max-warnings 0 <changed files>` + `python scripts/arch_compliance.py` 순차 실행
  - 셋 다 실패시에도 각자 결과는 JSON 으로 수집 (early exit 없음)
- [ ] **A.2.9 `scripts/dev_server_check.py <url>`**
  - `pgrep -f "next dev\|bun dev\|vite"` + `curl -sS -o /dev/null -w "%{http_code}" <url>` → 200 이 아니면 exit 1

각 script 에 `tests/test_*.py` 추가. 최소 pass/fail 2 케이스씩.

### A.3 references / templates 이관

team-product 원문을 plugin 경로로 그대로 복사 (자연어 판단용 문서는 수정 없음):

- [ ] **A.3.1 `plugin/skills/ax-implement/references/preflight-checklist.md`** (team-product 원문)
- [ ] **A.3.2 `plugin/skills/ax-implement/references/review-checklist.md`** (원문)
- [ ] **A.3.3 `plugin/skills/ax-implement/references/security-rules.md`** (원문)
- [ ] **A.3.4 `plugin/skills/ax-implement/references/backpressure-pattern.md`** (원문)
- [ ] **A.3.5 `plugin/skills/ax-implement/templates/PLAN_TEMPLATE.md`** (원문)

### A.4 Ralph Stop hook

- [ ] **A.4.1 `plugin/hooks/hooks.json` 초안 작성**
  - `ralph-loop/hooks/stop-hook.sh` 참고. ax-implement 전용이므로 상태 파일 경로: `.claude/ax-implement.local.md`
  - completion promise: `AX_IMPLEMENT_DONE` (고정)
  - max iterations: 기본 30, env var `AX_MAX_ITER` 로 override
- [ ] **A.4.2 Stop hook 스크립트 `plugin/hooks/ax-stop.sh`**
  - Ralph 로직과 동일 구조 (frontmatter 파싱 + transcript 의 마지막 assistant 메시지에서 `<promise>AX_IMPLEMENT_DONE</promise>` 탐지 + 재주입)
  - 재주입되는 prompt: "plan.md 에서 다음 `- [ ]` 태스크 1개 소비. 모두 `- [x]` 면 promise 출력."
- [x] **A.4.3 `--plugin-dir` 조합에서 Stop hook 이 실제로 걸리는지 실험** ✅ 2026-04-13
  - 실험 파일: `notes/v0.3-experiments/exp-07-ralph-hook-in-bare.md`
  - **결과**: Stop hook 정상 발화 + block+reason 재주입 루프 동작 확인. R3 해소.
  - **부가 발견**: `--bare` 는 auth credential 까지 끊음 → 사용 금지. `--setting-sources project,local` 만으로 재현성 확보.

### A.5 fixture 및 end-to-end 검증

- [ ] **A.5.1 Fixture 결정**
  - **1차 후보**: moomoo-ax 자체 dogfooding — dashboard/ 에 소형 태스크 1개 (예: product_runs 테이블 카드 UI 최소 버전)
  - **2차 후보**: 격리 static fixture `labs/ax-implement/input/static-nextjs/` (Next.js + i18n + DS 토큰 기본 세팅 포함)
  - rubato/haru 사용 금지 (허브 CLAUDE.md)
- [ ] **A.5.2 plan.md 및 specs 준비**
  - fixture 안에 `versions/v0.3-fixture/plan.md` 작성 (T-001~T-003 수준 2~3개 태스크)
  - 필요 시 간이 `ARCHITECTURE.md` + `DESIGN_SYSTEM.md` + specs 준비
- [ ] **A.5.3 첫 run**
  ```bash
  .venv/bin/python src/loop.py ax-implement --user yoyo \
    --fixture dogfood:dashboard-product-runs-card \
    --input <fixture path> \
    --max-iter 1 --threshold 0.5
  ```
  - 실제 호출: `claude --plugin-dir plugin -p "/team-ax:ax-implement <args>" --allowedTools ... --permission-mode acceptEdits --output-format stream-json --verbose --include-hook-events --setting-sources project,local` (⚠️ `--bare` 는 auth 를 끊으므로 제외 — exp-07 참조)
  - 자식 세션 내부에서 Ralph Stop hook 이 돌며 plan.md 체크박스 소비
- [ ] **A.5.4 판정 (이진 기준)**
  - PASS: plan.md 태스크 모두 `- [x]` + `<promise>AX_IMPLEMENT_DONE</promise>` 출력 + git log 에 태스크별 커밋 존재
  - FAIL: 그 외 모든 경우 — 원인 분석하여 A.1~A.4 로 복귀
- [ ] **A.5.5 결과 노트 `notes/2026-04-1x-v0.3-phase-a-run.md`**
  - 실행 로그, tool_events 분포, 비용, iteration 수, 실패 사례 기록

---

## Phase B — meta loop: 조회 인프라

> **"Phase A 에서 만든 product loop 실행을 DB/대시보드에서 관찰. 개선은 v0.4+ 의 levelup loop 이 하고, 이번 Phase 는 관찰만."**

### B.1 product_runs 수집

- [ ] **B.1.1 Supabase `product_runs` 테이블**
  - 컬럼: id, stage, target_project, started_at, ended_at, duration_sec, cost_usd, num_turns, tool_call_stats (JSONB), intervention_count, exit_status, fixture_id, session_id
  - 마이그레이션 파일 `supabase/migrations/<ts>_product_runs.sql`
- [ ] **B.1.2 수집 hook**
  - 옵션 1: Stop hook (ax-stop.sh) 종료 시점에 `scripts/log_run.py` 호출하여 Supabase insert
  - 옵션 2: `src/loop.py` 가 자식 세션 결과 (tool_events + usage) 를 받아서 insert
  - Phase A 의 Stop hook 에 이미 logic 있으므로 옵션 1 우선
- [ ] **B.1.3 `scripts/log_run.py`**
  - stream-json 으로 수집된 `tool_events` → tool 이름별 집계 → product_runs row
  - env: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (하드코딩 금지)

### B.2 interventions 결합

- [ ] **B.2.1 기존 `/ax-feedback` interventions 와 product_runs join**
  - 시간 범위 기준 매칭 (started_at ~ ended_at 안의 intervention)
  - product_runs.intervention_count 업데이트 (triggers 또는 집계 뷰)
- [ ] **B.2.2 stage 별 집계 뷰 `v_stage_interventions`**

### B.3 대시보드 확장

- [ ] **B.3.1 기존 카드 레이아웃 재사용**
  - `dashboard/app/` 에 product_runs 요약 카드 추가 (levelup_runs 카드와 병렬)
  - 표시: 최근 run / cost / duration / intervention_count / tool 분포 요약 배지
- [ ] **B.3.2 전체 재설계 금지** — 기존 구조에 카드 1개 추가 수준만

### B.4 북극성 지표 베이스라인

- [ ] **B.4.1 Phase A 의 run 들에서 intervention_count 측정**
- [ ] **B.4.2 숫자 기록만** — 개선 목표는 v0.4~v0.5 의 levelup 이 담당
- [ ] **B.4.3 `notes/2026-04-1x-v0.3-baseline.md` 기록**

---

## Phase C — 마감

- [ ] **C.1 `versions/v0.3/report.md`** — Phase A/B 요약 + 측정치 + 회고 (잘된 것 / 개선할 것)
- [ ] **C.2 `HANDOFF.md`** — v0.4 진입용 (levelup loop smoke + ax-qa/ax-design 포팅 스코프)
- [ ] **C.3 `BACKLOG.md` 갱신**
  - ready: levelup loop smoke (v0.4), ax-qa 포팅 (v0.4), ax-design 포팅 (v0.5), simplify hook 도입 (v0.4), `ax-autopilot` (v0.4)
  - inbox: v0.3 에서 발견된 후속
- [ ] **C.4 `PROJECT_BRIEF.md` 버전 로드맵 업데이트**
- [ ] **C.5 PR 머지 + 태그 `v0.3.0`**

---

## Out of scope (v0.4+)

- levelup loop smoke (v0.4)
- ax-qa 포팅 + Playwright MCP (v0.4)
- ax-design / ax-init / ax-deploy 포팅 (v0.5)
- `ax-autopilot` 상위 오케스트레이터 (v0.4)
- simplify hook 도입 (oh-my-claudecode 패턴) (v0.4)
- R-LEN / R-DRY AST 검증 (타깃 아님 — 재검토 불필요)
- 재현성 수치 기준선 (v0.4)
- Claude Code `--resume` / Agent SDK (불필요 판정, Phase 0)
- team-ax 플러그인의 MCP 내장화 (v0.4)
- rnd/ (meta loop trend/gate/evolver, v1.x)

---

## 작업 순서

```
Phase 0 (✅ 2026-04-11)
Phase 1a (✅ 2026-04-12, meta loop 호출 인프라로 재배치)
    │
    ├─ Phase A  product loop ax-implement
    │    A.1 SKILL.md 본체
    │    A.2 scripts 9개 구현
    │    A.3 references/templates 이관
    │    A.4 Ralph Stop hook (+ bare 호환 실험)
    │    A.5 fixture + end-to-end 판정
    │
    ├─ Phase B  meta loop 조회 인프라   ← Phase A PASS 후
    │    B.1 product_runs 테이블 + 수집 hook
    │    B.2 interventions 결합
    │    B.3 대시보드 카드 추가
    │    B.4 북극성 지표 베이스라인
    │
    └─ Phase C  마감
         C.1 report / C.2 HANDOFF / C.3 BACKLOG / C.4 BRIEF / C.5 머지+태그
```

---

## 리스크

| # | 리스크 | 영향 | Mitigation |
|---|---|---|---|
| R1 | `-p` 슬래시 호출이 multi-line 인자를 못 받음 | 중 | fixture 경로만 인자로 넘기고 SKILL.md 가 Read tool 로 읽음 |
| R2 | ~~`--bare` 가 plugin hooks (Stop) 을 차단~~ → **다른 이유로 `--bare` 사용 금지**: exp-07 에서 `--bare` 가 auth credential 까지 끊어 `"Not logged in"` 으로 즉시 종료. `--setting-sources project,local` 만으로 재현성 확보. | 해소 | exp-07 참조 |
| R3 | ~~Ralph Stop hook 이 자식 세션에서 재주입 못 함~~ → **해소** (exp-07): plugin Stop hook 이 `-p` 자식 세션에서 완전 정상 발화. block+reason 재주입 루프 동작 확인. | 해소 | exp-07 참조 |
| R4 | arch_compliance.py 가 ARCHITECTURE.md 구조 편차를 흡수 못함 | 중 | 최소 기능 — "기술 스택" / "Dependencies" 섹션 헤더만 파싱. 프로젝트별 편차는 v0.4 |
| R5 | Claude 가 scripts 를 호출하지 않고 "통과한 척" | 높 | Stop hook + product_runs 의 tool_call_stats 에서 기대 script 미호출 감지 시 intervention flag |
| R6 | moomoo-ax 자체 dogfooding 시 재귀 문제 (ax-implement 가 ax-implement 수정 가능) | 중 | fixture 는 `dashboard/` 하위로만 제한. `plugin/` / `src/` / `labs/` 접근 금지 플래그 |
| R7 | Supabase migration 이 기존 row 와 호환 안 됨 | 낮 | product_runs 는 신규 테이블이라 영향 없음 |
| R8 | dev_server_check.py 가 bun/next/vite 외 서버 못 잡음 | 낮 | 최소 기능 — pgrep 패턴 env 로 override 가능 |
| R9 | gitleaks / eslint 가 프로젝트에 설치 안 됨 | 중 | run_review_checks.sh 에서 미설치 시 경고 후 skip (block 아님) |

---

## 성공 기준 (v0.3 전체)

1. **Phase A PASS** — fixture 에서 `claude -p "/team-ax:ax-implement …"` 가 plan.md 태스크를 모두 소비하고 `<promise>AX_IMPLEMENT_DONE</promise>` 출력 + 태스크별 커밋 존재
2. **Phase B 조회** — product_runs 테이블에 Phase A run 들이 기록되고 대시보드에서 카드로 조회 가능
3. **Phase C 마감** — report / HANDOFF / BACKLOG 정리 + v0.3.0 태그

북극성 지표 (오너 개입 횟수) 는 **측정만**. 개선은 v0.4~v0.5 의 levelup loop 몫.

---

## 진행 메모

- 2026-04-11: Phase 0 완료 — 리서치 + 실험 6개 + 판정 리포트 (Path A 채택)
- 2026-04-12: Phase 1a 코드 완료 — claude.py 옵션 확장 + stream-json 파서. 원래 levelup 호출 업그레이드로 썼으나 방향 전환 후 **meta loop 호출 인프라로 재배치**.
- 2026-04-13: **방향 전환** — product → meta → levelup 순서 확정. plan 전면 재편. Ralph Stop hook 패턴 차용. scripts 9개로 축소 (R-LEN/R-DRY AST 제외, simplify 제외, phase/토큰스냅샷 제외).
- 2026-04-13: **exp-07 완료** — Phase A.4.3 선실행. Stop hook 이 `-p --plugin-dir` 자식 세션에서 완전 정상 발화 + block+reason 재주입 루프 동작 (`EXP07_HELLO` → `EXP07_AFTER_HOOK`, num_turns=2, cost $0.21). R3 해소. 부가 발견: `--bare` 는 auth 까지 끊음 → 전면 사용 금지. `--setting-sources project,local` 만으로 재현성 확보. R2 도 해소.
