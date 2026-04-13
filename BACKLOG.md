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

### 🔬 v0.3 후속 실험 트랙 (편입 여부 v0.4 에서 결정)
- **Codex 런타임 편입 가능성** — v0.3 에서 adversarial review 용으로 4회 활용. team-ax subagent 중 하나 (reviewer 우선 후보) 를 Codex 호출로 대체해 모델 다중화 / 비용 분산 / 독립 검토 가능한지 실험. 레퍼런스: `notes/2026-04-13-codex-transition-plan.md`. v0.3 범위에는 포함되지 않음. → v0.4 편입 후보

### 📦 team-ax 플러그인 카탈로그 뷰
- **대시보드 "Plugin" 탭** — team-ax 플러그인 소개 페이지. 6 stage 맵, 각 skill 의 SKILL.md 본문 렌더, lineage (hash 계보), 알려진 이슈, 개선 후보, 에이전트 리스트. product loop 사용자 시점 카탈로그. → v0.4~0.5 (대시보드 v2 재설계와 묶어 판단)

### 🧪 재현성 / 지표
- **재현성 체크**: 같은 fixture 로 3회 돌려 score 편차 관측 → v0.4
- **다른 fixture 확장**: FE 외 BE 태스크 / 혼합 케이스에서도 일반성 확인 → v0.4
- **북극성 지표 기준선 첫 설정** — 실전 데이터 2~3건 쌓인 뒤 목표치 제안 → v0.4

### 🧹 문서/구조
- **`labs/{stage}/input/` 디렉토리 구조 표준 문서화** — 모든 stage 가 따를 입력 레이아웃 → v0.4
- **improve tokens 로깅 bug fix** — `logs/{iter}.json` 의 `tokens.improve` 가 0 으로 찍힘 (v0.2 잔존). `loop.py` 에서 `log_data` serialize 를 improve 호출 후로 이동. → v0.4 small

---

## ready (v0.4)

> 다음 버전 후보. 트랙 A (관찰 인프라) 가 최우선 — 관찰 없이 levelup 개선 대상이 공허해지는 v0.2 E 회귀 위험.

### 트랙 A: 관찰 인프라 🎯 최우선
- **`product_runs` Supabase 테이블** — 컬럼: `id / stage / target_project / started_at / ended_at / duration_sec / cost_usd / num_turns / tool_call_stats (JSONB) / intervention_count / exit_status / fixture_id / session_id`. 마이그레이션 파일 신규.
- **Parent-side idempotent logging** — 드라이버 `scripts/ax_product_run.py` 가 run 종료 시 1회 insert. Stop hook 기반 아님 (exp-07 에서 block+재주입 시 2회+ 호출 확인 → hook insert 는 중복 위험). env: `SUPABASE_SERVICE_ROLE_KEY` (기존 `src/db.py` 와 동일).
- **intervention 결합 뷰** — `interventions` × `product_runs` 시간 범위 기반 join. stage 별 개입 횟수 집계.
- **대시보드 `product_runs` 카드** — 기존 `levelup_runs` 카드와 병렬. 전체 재설계 금지, 추가 배지 수준.

### 트랙 B: moomoo-ax dogfooding
- **`--target-subdir` 옵션** — 드라이버에 경로 가드 추가. Write/Edit allow 패턴을 런타임에 해당 subdir 로 제한 (plugin / src / labs 외).
- **dogfooding 첫 대상** — `dashboard/` 하위 소형 태스크. product_runs 테이블 UI 카드 개선 등 (트랙 A 완료 후).
- **재귀 차단** — ax-implement 가 ax-implement 자체 (SKILL.md / scripts) 를 수정 못하게.

### 트랙 C: ax-qa 포팅
- **`plugin/skills/ax-qa/`** — team-product/skills/product-qa 기반 SKILL.md. Playwright MCP (`mcp__plugin_playwright_playwright__*`) + axe-core + Lighthouse.
- **`plugin/agents/qa.md`** — team-product/agents/qa.md 기반 포팅.
- **labs/ax-qa 동결 해제** — v0.1 동결본은 `labs/.archive/ax-qa-v0.1-frozen/` 로 이동. 새 `labs/ax-qa/` 에서 drive.
- **fixture `static-nextjs-min` 에 flows/ 추가** — QA 대상 지정.

### 트랙 D: levelup loop smoke (트랙 A 선행 필수)
- **levelup 대상 식별 기준** — intervention_count 높은 태스크 패턴, 반복 실패 script 등. 관찰 데이터 기반.
- **labs/ax-implement 재활성** — `.archive/` 에서 script.py / program.md / rubric.yml 복원 + v0.3 기준으로 재작성.
- **rubric 축 추가** — "구현 성공률", "오너 개입 횟수", "script 호출 실효성".
- **levelup 1 cycle 완주** — SKILL.md or scripts 1개 자동 개선 실증.

### 트랙 E: 자동화 보강
- **planner subagent** — fixture 에 plan.md 내장 안 된 실 프로젝트 대응. team-product/agents/planner.md 기반 포팅.
- **드라이버 자동 판정** — promise 검출 + 체크박스 파싱 + 태스크 커밋 존재 + review gate 성공 여부 전수 확인 후 exit 0. Codex 2/3차 findings 일부 편입.
- **simplify hook** — oh-my-claudecode 패턴. Stop hook 이 git diff modified 파일 뽑아 Task(code-simplifier) 위임. 단 v0.3 에서 의도적 생략한 블록+재주입 재귀의 연장이므로 보수적으로 설계.

### 트랙 F: `ax-autopilot` 상위 오케스트레이터
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
