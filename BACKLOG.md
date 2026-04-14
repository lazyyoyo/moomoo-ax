# BACKLOG

moomoo-ax 프로젝트 백로그.

- **inbox**: 새로 들어온 항목 (아직 분류/정제 전)
- **ready**: 다음 버전에서 구현 가능한 상태 (spec/의존성 정리됨)
- **done**: 완료 (버전 태그 포함)

각 항목은 `[버전-접두] 제목 — 요약`.
항목 source: retro, 실전 사용 피드백, 외부 이슈, 설계 논의.

---

## inbox

### 💬 v0.3 Phase A run 에서 남은 후속
- **Button.tsx `borderWidth: var(--radius-sm)` token 카테고리 mismatch** — fixture run 에서 reviewer 의 non-blocking note. DESIGN_SYSTEM.md 에 border 용 token 없어서 `--radius-sm` 을 borderWidth 로 재사용. v0.4 dogfooding 이나 fixture 보완 시 조정 (border 용 token 추가 or 기존 상수 삭제). → v0.4 소재
- **plan.md Edit 형식 잔재** — reviewer 가 원래 `- [ ] T-XXX` → `- [x] T-XXX` 원칙을 어기고 `### T-001 ... [x]` 로 헤더 뒤에 붙임. SKILL.md 프로토콜 표현을 더 명확히 하거나 `find_next_task` structured helper 재도입 검토. → v0.4
- **gitleaks 를 setup requirement 로 문서화** — 현재는 오너 수동 설치. `scripts/ax_bootstrap.sh` 같은 일괄 확인기 도입 or README 명시. → v0.4

### ⏱️ v0.4 Track B latency 후속
- **Track B pilot latency 회귀** — 첫 Codex executor+reviewer pilot (`69ddd1eb0aa4`) 이 원 3-task fixture 에서 약 43분 소요. 이후 rerun 은 `20m 48s`, model-routing rerun 은 `22m 24s`. 구조는 green 이지만 속도/비용은 known issue 로 남는다. 레퍼런스: `notes/2026-04-14-track-b-pilot-partial.md`, `notes/2026-04-14-track-b-latency-reduction-plan.md`, `notes/2026-04-14-track-b-model-routing-rerun.md`.
- **model routing 후속 보정** — `e0f0a5be8b5a` 에서 저위험 task 는 `gpt-5.4-mini`, stage-final-review 는 `gpt-5.4` 로 라우팅됨. 라우팅 자체는 유효했지만 elapsed 개선은 제한적. dogfooding 이후 실전 데이터로 다시 판단. 레퍼런스: `notes/2026-04-14-track-b-model-routing-rerun.md`.
- **fix approve 후 reviewer 재호출 제거** — `T-FIX-T-001-1` approve 뒤 `T-001-retry` reviewer-only 재검증이 발생. 동일 logical task 중복 호출 제거 필요. → v0.4
- **worker 의 dependency 복구 금지** — `T-002` executor 가 구현보다 `npm install`/캐시 확인에 시간을 소모. dependency/infra 복구는 preflight 또는 conductor 경로로 이동. → v0.4
- **orphan `product_runs.status=running` 회수 경로** — long run 수동 kill 시 driver `finally` 전 인터럽트로 row 가 `running` 으로 고립. 기동 시 orphan row 를 `cancelled` 로 전이하는 recovery 또는 signal-safe finish 경로 필요. → v0.4
- **stage-final-review blocking 2건 fixture 후속** — runtime design tokens 부재, `tsconfig` 의 vitest globals 누수. v0.4 pilot 에선 non-recursive audit evidence 로만 남겼으므로 backlog 에 명시적으로 승격 필요. → v0.4 또는 v0.5

### 🔬 v0.3 후속 실험 트랙
- **Codex 런타임 편입 자산 정리** — one-shot worker smoke + tmux host PoC 까지 완료. `codex exec --json`, `last-message.txt`, `events.jsonl`, `meta.json`, stopped-case 관찰성까지 확보. 이제 이 항목은 "가능성 조사" 가 아니라 **v0.4 Track B executor+reviewer pilot 의 선행 자산** 으로 취급. 레퍼런스: `notes/2026-04-13-codex-transition-plan.md`, `notes/2026-04-13-codex-worker-poc-scope.md`, `notes/2026-04-13-codex-worker-smoke.md`, `notes/2026-04-13-codex-tmux-host-poc.md`, `notes/2026-04-13-codex-tmux-smoke.md`.

### 📦 team-ax 플러그인 카탈로그 뷰
- **대시보드 "Plugin" 탭** — team-ax 플러그인 소개 페이지. 6 stage 맵, 각 skill 의 SKILL.md 본문 렌더, lineage (hash 계보), 알려진 이슈, 개선 후보, 에이전트 리스트. product loop 사용자 시점 카탈로그. → v0.4~0.5 (대시보드 v2 재설계와 묶어 판단)

### 🧪 재현성 / 지표
- **재현성 체크**: 같은 fixture 로 3회 돌려 score 편차 관측 → v0.4
- **다른 fixture 확장**: FE 외 BE 태스크 / 혼합 케이스에서도 일반성 확인 → v0.4
- **북극성 지표 기준선 첫 설정** — 실전 데이터 2~3건 쌓인 뒤 목표치 제안 → v0.4

### 🧹 문서/구조
- **`labs/{stage}/input/` 디렉토리 구조 표준 문서화** — 모든 stage 가 따를 입력 레이아웃 → v0.4
- **improve tokens 로깅 bug fix** — `logs/{iter}.json` 의 `tokens.improve` 가 0 으로 찍힘 (v0.2 잔존). `loop.py` 에서 `log_data` serialize 를 improve 호출 후로 이동. → v0.4 small
- **Codex PoC helper / normalize 초안** — `scripts/poc/` 에서 `events.jsonl` + `last-message.txt` + `meta.json` 을 읽어 `sandbox_block`, `thread_id`, usage, 최종 요약 JSON 을 추출하는 helper 유지. 본선 `src/runtime/normalize.py` 착수 전 선행 실험 자산. → v0.4 소재

---

## ready (v0.4)

> 다음 버전 후보. 오너 선호는 **선계획 후실행**. 트랙은 1개씩 닫고, 우선순위는 A → B → C. A 없이는 B/C 판단 근거가 약해진다.

### 트랙 A: 관찰 인프라 🎯 최우선
- **`product_runs` Supabase 테이블** — 컬럼: `id / stage / target_project / started_at / ended_at / duration_sec / cost_usd / num_turns / tool_call_stats (JSONB) / intervention_count / exit_status / fixture_id / session_id`. 마이그레이션 파일 신규.
- **Parent-side idempotent logging** — 드라이버 `scripts/ax_product_run.py` 가 run 종료 시 1회 insert. Stop hook 기반 아님 (exp-07 에서 block+재주입 시 2회+ 호출 확인 → hook insert 는 중복 위험). env: `SUPABASE_SERVICE_ROLE_KEY` (기존 `src/db.py` 와 동일).
- **intervention 결합 뷰** — `interventions` × `product_runs` 시간 범위 기반 join. stage 별 개입 횟수 집계.
- **대시보드 `product_runs` 카드** — 기존 `levelup_runs` 카드와 병렬. 전체 재설계 금지, 추가 배지 수준.

### 트랙 B: Codex executor+reviewer pilot
- **역할 분리 고정** — Claude 는 conductor, Codex 는 executor / reviewer worker.
- **executor result schema 고정** — `status(ok|failed|infra_error)` + `summary` + `changed_files[]` + `checks_run[]`.
- **review result schema 고정** — `verdict(APPROVE|REQUEST_CHANGES|ERROR)` + `blocking_issues[]` + `non_blocking_issues[]` + `summary`.
- **외부 worker adapter** — 기존 task → executor → reviewer → fix task 루프는 유지하고, executor / reviewer 결과만 파일 기반으로 normalize 해서 lead 가 판정.
- **fresh session 분리** — executor / reviewer 각각 별도 task file / 별도 결과 파일 / 별도 session.
- **tmux 는 옵션형 host** — 기본 판정 채널은 `events.jsonl` + `meta.json` + `last-message.txt`.
- **1차는 fixture pilot** — `static-nextjs-min` 에서 Codex executor → Codex reviewer 루프를 붙이고, green 후 dogfooding.
- **latency 지표** — fixture elapsed / cost / turns 는 계속 기록한다. 다만 v0.4 에서는 dogfooding 진입 차단 기준이 아니라 known issue/최적화 항목으로 취급한다.
- **checks/conductor 분리** — deterministic checks 는 worker 밖으로 이동.
- **stage-final-review 범위 제한** — fixture pilot 단계에선 recursive remediation loop 확장을 막아야 함.

### 트랙 C: moomoo-ax dogfooding
- **`--target-subdir` 옵션** — 드라이버에 경로 가드 추가. Write/Edit allow 패턴을 런타임에 해당 subdir 로 제한 (plugin / src / labs 외).
- **dogfooding 첫 대상** — `dashboard/` 하위 소형 태스크. product_runs 테이블 UI 카드 개선 등 (트랙 A 완료 후).
- **재귀 차단** — ax-implement 가 ax-implement 자체 (SKILL.md / scripts) 를 수정 못하게.

### 트랙 D: ax-qa 포팅
- **`plugin/skills/ax-qa/`** — team-product/skills/product-qa 기반 SKILL.md. Playwright MCP (`mcp__plugin_playwright_playwright__*`) + axe-core + Lighthouse.
- **`plugin/agents/qa.md`** — team-product/agents/qa.md 기반 포팅.
- **labs/ax-qa 동결 해제** — v0.1 동결본은 `labs/.archive/ax-qa-v0.1-frozen/` 로 이동. 새 `labs/ax-qa/` 에서 drive.
- **fixture `static-nextjs-min` 에 flows/ 추가** — QA 대상 지정.

### 트랙 E: levelup loop smoke (트랙 A 선행 필수)
- **levelup 대상 식별 기준** — intervention_count 높은 태스크 패턴, 반복 실패 script 등. 관찰 데이터 기반.
- **labs/ax-implement 재활성** — `.archive/` 에서 script.py / program.md / rubric.yml 복원 + v0.3 기준으로 재작성.
- **rubric 축 추가** — "구현 성공률", "오너 개입 횟수", "script 호출 실효성".
- **levelup 1 cycle 완주** — SKILL.md or scripts 1개 자동 개선 실증.

### 트랙 F: 자동화 보강
- **planner subagent** — fixture 에 plan.md 내장 안 된 실 프로젝트 대응. team-product/agents/planner.md 기반 포팅.
- **드라이버 자동 판정** — promise 검출 + 체크박스 파싱 + 태스크 커밋 존재 + review gate 성공 여부 전수 확인 후 exit 0. Codex 2/3차 findings 일부 편입.
- **simplify hook** — oh-my-claudecode 패턴. Stop hook 이 git diff modified 파일 뽑아 Task(code-simplifier) 위임. 단 v0.3 에서 의도적 생략한 블록+재주입 재귀의 연장이므로 보수적으로 설계.

### 트랙 G: `ax-autopilot` 상위 오케스트레이터
- **`plugin/skills/ax-autopilot/`** — `implement → localhost 확인 → preview` 자동 구간. team-product/skills/product-autopilot 있다면 참고.

---

## done

### v0.3 (마감 2026-04-13)

- [x] **Phase 0 — 리서치** — 6 실험 (exp-01~06) + `docs/claude-code-spec/` 9 파일 + Path A 판정 리포트.
- [x] **Phase 1a — claude.py 옵션 확장** — `--plugin-dir`, stream-json 파서, tool_events 반환. Phase A 에서 `cwd / include_hook_events / stdout_path` 추가 확장.
- [x] **Phase 1b — exp-07 Stop hook 실증** — `-p --plugin-dir` 자식 세션에서 Stop hook 정상 발화 확인. v0.3 엔 미사용.
- [x] **Phase A — `team-ax/ax-implement` 완성** — SKILL.md + scripts 4 + references 5 + templates 1 + agents 3 (`executor` / `design-engineer` / `reviewer`) + 드라이버 `scripts/ax_product_run.py` + fixture `labs/ax-implement/input/static-nextjs-min/`.
- [x] **Phase A.7 end-to-end run PASS** — run_id `1e9ae5a4f9b3`, $3.32 / 11분 / 3 task 전부 APPROVE + 커밋 + review gate (gitleaks / eslint / arch_compliance 전부 exit 0).
- [x] **파이썬 회귀 95/95** — 기존 87 + A.5.3 신규 8 (드라이버 mock 테스트).
- 📝 **v0.3 수확**: product loop 1 stage 실증 + "돌아가는가 이진 기준" 달성. 관찰 인프라 / dogfooding / levelup 은 v0.4 이월 (의도적). 상세: `versions/v0.3/report.md`, `notes/2026-04-13-v0.3-phase-a-run.md`.

### v0.2 (마감 2026-04-11)

- [x] **A. R5 fix + `improve_target` 추상화** — `improve_artifact` 리팩터 + 언어별 구조 체크 + 백업 + 단위 테스트 23 케이스. labs/ax-qa 회귀 0.96→1.0.
- [x] **B. 토큰 집계 조사 + cache 필드 분리** — `claude.py` tokens shape 4 필드. rubric "토큰 효율" 축 설계안.
- [x] **C. 자동 diff post-commit hook** — `.ax-generated` 매니페스트 + `install_ax_diff_hook.sh` + `ax_post_commit.py`. pytest 15 케이스.
- [x] **D. `/ax-feedback` CLI** — `plugin/skills/ax-feedback/SKILL.md` + `scripts/ax_feedback.py`. pytest 14 케이스 + 첫 실 feedback row 1개 보존.
- [x] **E. `ax-implement` (C') 패턴 — 파이프 검증** — team-product 포팅 + labs 래퍼 + haru:7475bef fixture + 범용 rubric + iter 1 0.886 → improve → iter 2 1.0.
- [⏭] **F. haru 실전 첫 적용** — v0.3 이월 → **v0.4 로 재이월** (관찰 인프라 선행 필요).
- [⏭] **G. 대시보드 Live poll** — v0.3 이월 → **v0.4 로 재이월** (트랙 A 와 묶음).
- 📝 **v0.2 수확**: 파이프 증명 1건 + 구조 결함 실증 2건. 상세: `notes/2026-04-11-v0.2-e-f-codification-insight.md`.

### v0.1 (2026-04-11)

- [x] **3 레이어 재정의** (meta/levelup/product) — PROJECT_BRIEF.md 전면 재작성
- [x] **배포 제품명 확정**: team-ax
- [x] **디렉토리 재편**: strategy→dogfooding, labs/ax-*, plugin/skills/ax-*, rnd/
- [x] **Supabase 스키마 재설계**: iterations drop + 4 테이블 생성 + RLS 분리
- [x] **src/db.py, src/loop.py 리팩토링**: 새 스키마 + user_name/fixture_id
- [x] **labs/ax-qa 스켈레톤**: program.md + rubric.yml + script.py + fixture
- [x] **첫 levelup run 성공**: rubato:0065654, 1 iter score 0.96, cost $0.90
- [x] **dashboard v0.1 재설계**: 6 내비 + 서버 컴포넌트 + Vercel 재배포
- [x] **docs/north-star.md**: 북극성 지표 측정 방식 정의
