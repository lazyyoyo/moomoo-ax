# HANDOFF — v0.3 마감, v0.4 진입

**작성 시점**: 2026-04-13
**기준 태그**: `v0.3.0` (머지 + 태그는 B.5 에서 오너 승인 후)
**다음 세션 작업**: v0.4 착수. 먼저 트랙 A(관찰 인프라) spec → plan → 구현. 이후 Codex executor+reviewer pilot 과 dogfooding 순으로 확장.

## 한 줄 요약

v0.3 에서 `team-ax/ax-implement` skill 이 격리 fixture 에서 3 태스크 end-to-end 완주 (실 run `1e9ae5a4f9b3`, $3.32, 11분). v0.4 는 이 실행을 **관찰 가능** 하게 만들고, **Claude 는 conductor**, 기존 reviewer → executor 루프의 구현/검토 주체는 **Codex worker** 로 제한 편입한 뒤, **실 프로젝트** (moomoo-ax dogfooding) 로 확장하는 트랙.

## 먼저 읽을 문서 (순서대로)

1. **이 HANDOFF**
2. **`PROJECT_BRIEF.md`** — 3 레이어 정의. v0.3 에서 업데이트된 로드맵 반영됨
3. **`CLAUDE.md`** — 실행 규칙
4. **`versions/v0.3/report.md`** — v0.3 전체 결과 + 회고 + 후속 이월 목록
5. **`versions/v0.3/plan.md`** — v0.3 최종 plan (Phase A 구조)
6. **`notes/2026-04-13-v0.3-phase-a-run.md`** — 실 run 상세 기록 (4회 시도 이력 포함)
7. **`BACKLOG.md`** — ready (v0.4) + inbox (후속 아이디어)
8. **`docs/claude-code-spec/`** — CLI / skill / hook / plugin / agent 영구 레퍼런스
9. (메모리) `feedback_progressive_codification.md`, `feedback_loop_build_order.md`

## v0.3 에서 정립된 것 (유지할 것)

### 구조

- **product loop 독립 드라이버**: `scripts/ax_product_run.py`. `src/loop.py` (levelup) 미경유. `shutil.copytree + git init` 로 fixture 격리
- **skill 1회 = stage 1회**: Ralph Stop hook 재귀 아님. 태스크당 fresh context 는 `Task(subagent_type="team-ax:<name>")` 로
- **scripts 4개** (`run_checks.sh`, `arch_compliance.py`, `run_review_checks.sh`, `dev_server_check.sh`) + `references/` 5개 + `templates/` 1개 + `agents/` 3개 (`executor` / `design-engineer` / `reviewer`)
- **fixture**: `labs/ax-implement/input/static-nextjs-min/` (Next.js + TS + ESLint 8 + vitest), plain 디렉토리, `versions/v0.3-fixture/plan.md` 내장
- **오너 루프**: task 선택 → subagent 구현 → reviewer → APPROVE 시 `[x]` / REQUEST_CHANGES 시 fix task 삽입 (원 `[ ]` 유지, depth > 3 시 차단)
- **`${CLAUDE_SKILL_DIR}` 대신 절대경로**: permission rule 은 env 치환 안 함. 드라이버가 `plugin_dir.resolve()` 기반 allowed_tools 구성
- **`--bare` 사용 금지**: auth 까지 끊음 (exp-07)
- **`gitleaks` setup requirement**: `brew install gitleaks`

### 기록 / 증거

- Supabase `interventions` 테이블 (v0.2): 여전히 유효. `/ax-feedback` 명시적 피드백 수집
- `.harness/runs/<run_id>.ndjson`: 드라이버가 stream-json stdout 저장. 자동 파싱 없음, 수동 검증용
- product_runs 테이블 / 대시보드 카드: **v0.4 에서 도입**

## v0.4 우선순위 트랙

오너 선호: **선계획 후실행**. 트랙은 1개씩 닫는다. 우선순위는 A → B → C 이고, D 이후는 A~C 결과를 본 뒤 착수.

### 트랙 A: 관찰 인프라

v0.4 핵심. 관찰 없이는 levelup 개선 대상이 공허해짐 (v0.2 E 회귀 위험).

- Supabase `product_runs` 테이블 마이그레이션 (`duration_sec`, `cost_usd`, `num_turns`, `tool_call_stats`, `intervention_count`, `fixture_id`, `session_id`)
- **Parent-side idempotent logging** (드라이버에서 1회 insert, Stop hook 기반 아님 — exp-07 에서 Stop hook 이 블록+재주입 시 2회+ 호출되므로 hook insert 는 중복 위험)
- env 이름 통일: 기존 `src/db.py` 는 `SUPABASE_SERVICE_ROLE_KEY`. 드라이버도 동일 이름 사용
- 대시보드 (`dashboard/app/`) 에 `product_runs` 카드 추가 — 기존 `levelup_runs` 카드 옆에 병렬. 전체 재설계 X
- intervention 결합 뷰 (시간 범위 기반 join)

### 트랙 B: Codex executor+reviewer pilot

기존 `task 선택 → executor 구현 → reviewer 판정 → fix task` 루프는 유지한다. 바꾸는 건 executor / reviewer 의 실행 백엔드다. **Claude 는 conductor** 로만 남긴다.

- **대상 범위는 implement stage 한정** — executor + reviewer 만 Codex worker 로 대체. qa / autopilot 로 확장 금지
- **executor 결과 계약 고정** — `status(ok|failed|infra_error)` + `summary` + `changed_files[]` + `checks_run[]`
- **결과 계약 고정** — `verdict(APPROVE|REQUEST_CHANGES|ERROR)` + `blocking_issues[]` + `non_blocking_issues[]` + `summary`
- **호출 방식** — 외부 Codex worker 를 one-shot 으로 호출하고, lead 가 결과 파일을 읽어 fix task 생성 여부를 결정
- **tmux 는 host/debug 용**. 판정은 `events.jsonl` / `meta.json` / `last-message.txt` 기준
- **독립성 유지** — executor 와 reviewer 는 항상 fresh session, 별도 task file, 별도 결과 파일 사용
- **1차는 fixture pilot** — `static-nextjs-min` 에서 Codex executor → Codex reviewer 루프를 먼저 붙이고, 통과 후 dogfooding 으로 확장
- **현재 상태** — fixture green 은 달성했고 latency 는 `20m 48s`, model-routing rerun 은 `22m 24s` 로 느리다. 그러나 이는 v0.4 에서 known issue 로 수용하고, `Track C` dogfooding 진입을 막는 하드 게이트로 두지 않는다
- 레퍼런스: `notes/2026-04-13-codex-transition-plan.md`, `notes/2026-04-13-codex-worker-poc-scope.md`, `notes/2026-04-13-codex-worker-smoke.md`, `notes/2026-04-13-codex-tmux-host-poc.md`, `notes/2026-04-13-codex-tmux-smoke.md`

### 트랙 C: moomoo-ax dogfooding

ax-implement 가 moomoo-ax 자체를 개선하게 함. 단 재귀 위험 → 경로 가드 필요.

- fixture 가 아닌 **moomoo-ax 내 특정 디렉토리** (예: `dashboard/`) 를 대상으로
- 드라이버에 `--target-subdir` 옵션 + 자식 세션이 해당 subdir 밖은 못 건드리게 가드 (Write/Edit allow 패턴을 런타임에 제한)
- 트랙 A/B 완료 후 진행. dogfooding 때 Codex executor/reviewer 루프를 그대로 재사용 가능

### 트랙 D: ax-qa 포팅

v0.1 `labs/ax-qa` 동결 해제 + team-product/skills/product-qa 기반 신규.

- Playwright MCP / axe-core / Lighthouse 실 호출 (exp-06 에서 MCP 작동 검증됨)
- qa subagent 포팅 (team-product/agents/qa.md 기반)
- fixture 에 QA 대상 추가 (예: static-nextjs-min 에 flows/ 작성)

### 트랙 E: levelup loop smoke

관찰 데이터 기반으로 ax-implement SKILL.md / scripts 를 자동 개선하는 1 cycle. 트랙 A 선행 필수.

- 대상 식별 기준: intervention_count 높은 태스크 패턴
- labs/ax-implement/ 재활성 (`.archive/` 에서 script.py / program.md / rubric.yml 복원)
- rubric 에 "구현 성공률" / "오너 개입 횟수" 축 추가

### 트랙 F: planner subagent + 자동 판정 + simplify hook

v0.3 에서 의도적 생략. dogfooding 시점에 필요도 재평가.

- planner subagent (fixture 에 plan.md 내장 안 된 실 프로젝트 대응)
- 드라이버 자동 판정 (promise + 체크박스 + 커밋 + review gate 결속)
- simplify hook (oh-my-claudecode 패턴)

## 현재 git 상태

- 브랜치: `main`
- v0.3 관련 최근 커밋:
  ```
  (B.1~B.4 문서 커밋 예정)
  6dfbccb README + codex-transition-plan 노트
  3eb49a3 v0.3 Phase A 구현 — skill + scripts + subagents + 드라이버 + fixture
  1b52853 v0.3 plan — Codex 4차 findings 반영
  44fde93 v0.3 plan 단순화 — Stop hook 제거, subagent 기반
  bce921b v0.3 plan 재편 + exp-07 (Stop hook in -p)
  ```

## 테스트 현황

- 파이썬 회귀: **95/95 통과** (기존 87 + A.5.3 신규 8)
- scripts 단위 테스트: bash -n 구문 검증 + 실 fixture run 에서 호출 확인 (전용 단위 테스트 없음 → v0.4 에서 fixture 기반 snapshot 테스트 검토)

## 금지 / 주의 사항 (v0.4 도 유지)

- **태스크 tool 사용 금지** (메모리 가드라인)
- **rubato / haru / rofan-world 파일 직접 수정 금지** — 허브 CLAUDE.md. dogfooding 은 moomoo-ax 내부에서만
- **커밋/주석/문서 한글**, 변수/함수명 영문
- **키/토큰 하드코딩 금지** (환경 변수만)
- **labs/ax-qa 동결** — 트랙 C 착수 전까지
- **rnd/** (meta loop trend/gate/evolver) 건드리지 말 것 — v1.x
- **세션 종료 제안은 토큰 기반으로만**
- **`--bare` 사용 금지** (auth 차단)
- **Stop hook 자동 반복 패턴 금지** — v0.3 에서 의도적 제거. 필요하면 v0.4 에서 별도 실험 트랙으로

## 새 세션에서 절대 하지 말 것

- v0.3 의 SKILL.md / scripts / subagents 구조를 대폭 바꾸지 말 것 — 이번 PASS run 이 baseline. 점진 개선만
- 관찰 인프라를 Stop hook insert 로 구현 금지 — 중복 위험. parent-side only
- fixture 원본 (`labs/ax-implement/input/static-nextjs-min/`) 에 직접 커밋 금지 — readonly 운영
- v0.3 이월된 범위 (Out of scope) 를 v0.4 에서 한꺼번에 전부 하려 들지 말 것. 트랙 1개씩

## 커밋 치트시트

```bash
# 테스트 회귀
.venv/bin/python -m pytest tests/ -q   # 95 passed 기대

# ax-implement run (fixture)
.venv/bin/python scripts/ax_product_run.py \
  --fixture labs/ax-implement/input/static-nextjs-min \
  --timeout 3600 [--keep]

# post-commit hook dry-run
MOOMOO_AX_DRY_RUN=1 .venv/bin/python scripts/ax_post_commit.py /path/to/target

# /ax-feedback
.venv/bin/python scripts/ax_feedback.py --priority high --stage v0.4-plan "..."
```

## 이번 세션 한 줄 수확

> "돌아간다" 는 걸 1 fixture 에서 실증. 다음은 "보인다" + "실제 대상에 적용".
