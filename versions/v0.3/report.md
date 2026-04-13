# v0.3 Report

- 범위: product loop 의 `team-ax/ax-implement` 1 stage 완성 + Phase B 마감
- 기간: 2026-04-11 ~ 2026-04-13
- 태그: `v0.3.0` (예정)
- 관련 문서: `versions/v0.3/plan.md`, `notes/2026-04-13-v0.3-phase-a-run.md`

## 한 줄 수확

> `ax-implement` 가 격리 static fixture 에서 skill 1회 호출로 3 태스크 전부 구현·리뷰·커밋·blocking gate 통과까지 완주. **product → meta → levelup 순서 전환** 의 첫 실증.

## 결과 (Phase 별)

| Phase | 결과 | 비고 |
|---|---|---|
| Phase 0 — 리서치 | ✅ | 6 실험 + Path A 판정 리포트 |
| Phase 1a — claude.py 옵션 확장 | ✅ | `--plugin-dir` / stream-json 파서 / tool_events. Phase A 에서 `cwd` / `include_hook_events` / `stdout_path` 추가 확장 |
| Phase 1b — exp-07 Stop hook 실증 | ✅ | v0.3 엔 미사용. v0.4+ 참고용 |
| **Phase A — ax-implement 완성** | ✅ | SKILL.md + scripts 4 + subagents 3 + 드라이버 + fixture + end-to-end 수동 PASS |
| **Phase B — 마감** | 진행 | report / HANDOFF / BACKLOG / BRIEF / 머지+태그 |

## 최종 Phase A run (`1e9ae5a4f9b3`)

- cost: **$3.32**, turns: **63**, duration: **11분 4초**
- subagent: `team-ax:design-engineer` ×3 + `team-ax:reviewer` ×4 (fully-qualified)
- plan.md: 모든 `- [ ]` → `- [x]`, fix task 0 (첫 시도 전부 APPROVE)
- git log: seed + T-001 / T-002 / T-003 + plan chore = 5 commits
- `run_review_checks.sh`: exit 0 (gitleaks / eslint / arch_compliance 전부 pass)
- `run_checks.sh`: lint / typecheck / test (vitest 4/4) / build 전부 pass
- dev server: localhost:3457 HTTP 200, primary + secondary 버튼 렌더 확인

## 시도 이력 (Phase A.7 4회)

| # | run_id | 상태 | 원인 |
|---|---|---|---|
| 1 | `8ffd95a30897` | 🔴 실패 | `parse_stream_json` 에서 content block string 가드 미비 (AttributeError) |
| 2 | `f16376c8b190` | 🟡 no-op | SKILL.md 의 `!`복합명령`` preflight 가 `Bash(which:*)` prefix 매칭 거부 → 즉시 종료 |
| 3 | `2d263949fb2c` | 🟠 부분 | 구현/리뷰/커밋 완주했으나 `run_review_checks.sh` 가 `${CLAUDE_SKILL_DIR}` 치환 안 돼 permission 거부 → reviewer 의 자연어 검증으로 우회 (blocking gate 미실행) |
| 4 | `1e9ae5a4f9b3` | 🟢 **PASS** | 드라이버 allowed_tools 절대경로 + gitleaks 설치 + fixture eslint 8 전환 후 gate 통과 |

## 리뷰 루프

- **Codex adversarial review 4회** 진행 (자체 하네스 밖)
- 1차 ~ 4차 findings 수용 + 3차 일부 revert (v0.3 "돌아가는가 이진 기준" 과 불일치 판단)
- 핵심 방향 전환 중 Codex 가 실행 블로커 (script 경로 / subagent 네임스페이스 / worktree branch 누적) 3건 조기 발견

## 측정치

- 파이썬 회귀 테스트: **95/95 통과** (기존 87 + A.5.3 신규 8)
- 신규 코드 규모: scripts 4 + SKILL.md + 3 agents + 드라이버 + fixture 템플릿 (~1,500 LOC)
- 커밋 수 (main): 6개 (plan 재편 + exp-07 + Phase A 구현 + README/codex-transition + fix 작업)

## 회고

### 잘된 것

1. **순서 뒤집기 결정** — levelup → product → meta 에서 **product → meta → levelup** 으로. v0.2 E 의 공허함을 진단한 메모리 `feedback_loop_build_order.md` 가 근거로 작동함.
2. **Codex 외부 리뷰 루프** — 한 사람(+LLM) 의 눈이 놓친 실행 블로커를 조기 포착. 단 3차 리뷰는 과잉 security 지적이라 revert. 판단 기준 (v0.3 원칙 대비) 이 유효했음.
3. **단순화 방향** — Stop hook 재귀 자체 루프 → skill 1회 + subagent 호출. scripts 10→4. 복잡도 대폭 감축. 오너 루프 ("task 고르기 → 진행 → 체크 or fix task") 보존.
4. **fixture 격리** — `git worktree` 대신 `shutil.copytree + git init` 로 fixture plain 디렉토리 유지. moomoo-ax tree 에서 자연 트래킹. gitlink 문제 회피.
5. **오너 루프 보존** — 실패 시 fix task 삽입 규약이 본 run 에선 발화 안 했지만 SKILL.md 프로토콜로 명시됨. dogfooding 시 검증 가능.

### 개선할 것

1. **plan.md Edit 형식 잔재** — reviewer 가 `### T-001 ... [x]` 처럼 헤더 뒤에 붙임. 원안 `- [ ] T-001 ...` 규칙과 편차. v0.4 에서 SKILL.md 본문에 형식 예시 추가 또는 `find_next_task` 류 structured helper 재검토. 👉 ready
2. **borderWidth 에 `--radius-sm` 재사용** (Button.tsx) — reviewer 의 non-blocking note. DESIGN_SYSTEM 에 border 용 token 없어 발생. 👉 inbox (v0.4 dogfooding 때 고려)
3. **gitleaks 를 setup requirement 로 명시** — 현 플로우는 오너가 수동 설치. v0.4 의 `scripts/ax_bootstrap.sh` 같은 setup 일괄 확인기 필요.
4. **드라이버 자동 판정 없음** — 판정은 전부 수동. v0.4 에선 promise 검출 / 체크박스 파싱 / review gate 성공 여부를 driver 가 자동 판정 (Codex 2/3차 findings 반영).

## v0.3 범위에서 제거된 것 (의도적)

- 관찰 인프라 전체 (Supabase `product_runs` + 대시보드 카드) → Stop hook DB insert idempotency 위험 → **v0.4 이월**
- moomoo-ax 자체 dogfooding → 격리 fixture 부재 + 경로 가드 미존재 → **v0.4 이월**
- Ralph Stop hook 자동 반복 → skill 1회 + subagent 로 충분 → 필요 시 v0.4+
- 자동 판정 로직 → 수동 확인으로 갈음 → **v0.4 이월**
- `R-LEN` / `R-DRY` 같은 AST 검증 규칙 추출 → 타깃 아님 (오너 교정) → 영구 out of scope

## 후속 (v0.3 → v0.4 이월)

`BACKLOG.md` 의 ready / inbox 섹션 참조.

- 관찰 인프라 (Supabase `product_runs` + 대시보드 카드) + parent-side idempotent logging
- moomoo-ax 자체 dogfooding (경로 가드 + ax-implement 가 ax-implement 를 개선하는 실험)
- levelup loop smoke (관찰 데이터 기반 개선 대상 식별 + 1 cycle)
- `ax-qa` 포팅 + Playwright MCP + qa subagent
- `ax-design` / `ax-init` / `ax-deploy` 포팅
- `ax-autopilot` 상위 오케스트레이터
- planner subagent 도입 (fixture 에 plan.md 미내장인 실 프로젝트 대응)
- 자동 판정 로직 (promise + 체크박스 + 커밋 + review gate 결속)
- simplify hook (oh-my-claudecode 패턴)
- plan.md Edit 형식 가이드 강화
- Button `borderWidth` token 카테고리 조정 (fixture 후속)

## v0.3 후속 실험 트랙 (v0.3 범위 밖, v0.4 편입 후보)

- **Codex 런타임 편입 가능성** — 이번 세션에서 `notes/2026-04-13-codex-transition-plan.md` 로 정리. v0.4 에서 team-ax subagent 로 Codex 활용 가능 여부 (모델 다중화 / 비용 분산 / 독립 검토) 실험. 편입 후보로만 기록, v0.3 범위에는 포함하지 않음.

## 한 줄 마감

> "돌아간다" 는 사실을 1 fixture 에서 실증했다. v0.4 는 이 성공을 **관찰 가능** 하게 만들고 **실 프로젝트** 로 확장하는 것.
