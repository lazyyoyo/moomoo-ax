# BACKLOG

moomoo-ax 프로젝트 백로그.

- **inbox**: 새로 들어온 항목 (아직 분류/정제 전)
- **ready**: 다음 버전에서 구현 가능한 상태 (spec/의존성 정리됨)
- **done**: 완료 (버전 태그 포함)

각 항목은 `[버전-접두] 제목 — 요약`.
항목 source: retro, 실전 사용 피드백, 외부 이슈, 설계 논의.

---

## inbox

### 🔄 stage 포팅 / (C') 확산 (v0.3+)
- **ax-qa 포팅** — v0.1 `labs/ax-qa` 는 동결. team-product/skills/product-qa → `plugin/skills/ax-qa/` 시딩 + labs 래퍼 재설계. v0.2 에서 정립한 (C') 패턴 2번째 적용. → v0.3
- **ax-define / ax-design / ax-init / ax-deploy 순차 포팅** — 각 stage 별 team-product 시딩 + labs 래퍼. → v0.3~0.5
- **자연어 규칙 → script 자동 추출** — v0.2 E5 에서 식별한 "script 후보" 를 실제로 `plugin/skills/ax-*/scripts/` 로 분리하는 자동 경로. 토큰 효율 rubric 축 기반 판정. → v0.3+

### 🧬 v0.3 재설계 (v0.2 E + F 에서 발견한 2가지 구조 결함)
> 상세: `notes/2026-04-11-v0.2-e-f-codification-insight.md`. 결함 1 (E): 자연어 압축 ≠ codification. 결함 2 (F): `claude -p` one-shot ≠ Claude Code tool loop. 둘 다 Python one-shot 전제의 한계. v0.3 는 리서치부터 시작.

#### Phase 0 — 리서치 (v0.3 착수 **전** 필수)
> 상세: `notes/2026-04-11-v0.3-research-scope.md`. v0.3 재설계의 모양이 Claude Code CLI 실 기능/제약에 달려있어 가설 검증 먼저.
- **[선행] 축 2 — `docs/claude-code-spec/` 레퍼런스 구축** — skill/plugin/command/agent/hook/cli/permissions 공식 규약. 원본: `claude-code-guide`, 공식 docs, `~/.claude/plugins/` 실 예시.
- **[선행] 축 1 — Claude Code CLI tool-enabled 호출 가능성 탐색** — `--allowedTools`, `--permission-mode`, skill 강제 load, 재귀 호출, stdin/stdout 제약, output JSON 의 cost/token 반환.
- **[선행] 축 3 — 하이브리드 loop 실험 6개** — echo / stateful / 재귀 / skill-load / 비용집계 / MCP 상속. 각 실험 로그는 `notes/v0.3-experiments/`.
- **[선행] 판정 리포트** — `notes/2026-04-12-v0.3-feasibility.md`. Path A (하이브리드 Python+Claude Code) vs Path B (완전 skill 기반) 중 선택 + 근거.

#### Phase 1+ — 재설계 구현 (판정 결과에 따라)
- **skill invoke 메커니즘 재설계** — 하이브리드 or 완전 skill. v0.2 E/F 의 결함 2 해결. → Phase 0 후
- **SKILL.md `[run: ...]` 규약 + 최소 1개 script 추출** — 첫 추출 후보: `scripts/check_r_len.py` (공개 함수 본체 60줄, AST 기반). rubric 에 "결정적 규칙이 script 로 추출되었는가" 축 추가. v0.2 E 결함 1 해결. → Phase 0 후
- **improve_target → skill bundle (multi-file)** — 단일 파일에서 `SKILL.md + scripts/** + references/** + (v0.4+) agents/**` 묶음 단위 개선으로 확장. `improve_artifact` multi-file diff, lineage hash bundle 단위. → Phase 0 후
- **ax-qa 포팅 (F 재시도)** — skill invoke 재설계 이후에만 의미. Playwright MCP / axe / Lighthouse 접근 가능한 구조로. → Phase 0 + skill invoke 재설계 후
- **improve tokens 로깅 bug fix** — `logs/{iter}.json` 의 `tokens.improve` 가 0 으로 찍힘. `loop.py` 에서 `log_data` serialize 를 improve 호출 후로 이동. `total_cost_usd` 는 이미 정상. → v0.3 small
- **references/ 의 주입 경로 결정** — 현재 장식 상태. inline 합치기 / script.py 확장 / tool read 중 선택. skill invoke 재설계 결과에 연동. → Phase 0 후

### 📦 team-ax 플러그인 카탈로그 뷰
- **대시보드 "Plugin" 탭** — team-ax 플러그인 소개 페이지. 6 stage 맵, 각 skill 의 SKILL.md 본문 렌더, lineage (hash 계보), 알려진 이슈(failed_items 누적), 개선 후보(script 추출 대상), 에이전트 리스트. product loop 사용자 시점 카탈로그. 기존 대시보드(개발자 시점 로그)와 관점 분리. → v0.3~0.4 (대시보드 v2 재설계 시점과 묶어 판단)

### 🧪 재현성 / 지표
- **재현성 체크**: 같은 fixture 로 3회 돌려 score 편차 관측 → v0.3
- **다른 fixture 확장**: refactor 외 케이스에서도 일반성 확인 → v0.3
- **북극성 지표 기준선 첫 설정** — 실전 데이터 2~3건 쌓인 뒤 목표치 제안 → v0.3

### 🚰 수집 인프라 (v0.3+)
- **`/ax-diff` 수동 명령** — post-commit hook 누락 보조용. ad-hoc 비교/리플레이. → v0.3
- **`product_runs` 수집** — team-ax 플러그인 호출 시 자동 row insert. → v0.3

### 📊 대시보드 개선
- **Levelup 탭 score 추이 차트** — iter 별 점수 변화. → v0.3
- **Feedback 탭 직접 입력 폼** — 대시보드 입력. v0.2 는 CLI 만. → v0.3
- **대시보드 v2 필요 여부 판단** — v0.2~0.3 데이터 누적 후 유지/재설계 판단. → v0.3

### 🧹 문서/구조
- **`labs/{stage}/input/` 디렉토리 구조 표준 문서화** — 모든 stage 가 따를 입력 레이아웃. → v0.3
- **`program.md` 스키마 문서화** — `improve_target` 필드 등 v0.2 에서 추가된 구조를 명문화. → v0.3

---

## ready (v0.2)

### 🪲 엔진 / 안정성
- **A. R5 `improve_script()` fix + `improve_target` 추상화** (critical) — 프롬프트 강화 + 언어별 구조 체크(python/markdown) + 백업 + 최소 줄수 가드 + 실패 기록. `improve_target` 필드로 덮어쓰기 대상을 stage 별 선언. 회귀 테스트 포함. `src/loop.py`.
- **B. Token 집계 조사 (rubric 입력 격상)** — `src/claude.py` prompt caching 필드 확인. 결정 (a)/(b)/(c) + **rubric 토큰 효율 축 설계**. `notes/v0.2-token-investigation.md`.

### 🚰 수집 인프라
- **C. 자동 diff post-commit hook** — `scripts/install-ax-diff-hook.sh` + `scripts/ax_post_commit.py`. `.ax-generated` 매니페스트 기반. `interventions` 자동 insert.
- **D. `/ax-feedback` CLI** — `plugin/skills/ax-feedback/SKILL.md` + `scripts/ax_feedback.py`. priority 옵션, `feedback_backlog` insert.

### 🎯 stage / 실전 (v0.2 에서 이월)
- **F. haru 실전 첫 적용 (v0.1 labs/ax-qa 버전)** ⏭ **v0.3 이월** — team-product /product-qa 가 Playwright MCP / axe / Lighthouse / 서버 제어 multi-step 이 필수라 v0.1 labs/ax-qa 의 `claude -p` one-shot 구조로는 원천 재현 불가. v0.3 skill invoke 재설계 후 재시도.

### 📊 대시보드 (v0.2 에서 이월)
- **G. Live 탭 30초 auto-poll** ⏭ **v0.3 이월** — F 가 이월되어 수집할 실전 데이터 없음. v0.3 skill invoke 재설계 + 실 데이터 수집과 묶어서 재검토.

---

## done

### v0.2 (마감 2026-04-11)

- [x] **A. R5 fix + `improve_target` 추상화** — `improve_artifact` 리팩터 + 언어별 구조 체크 + 백업 + 단위 테스트 23 케이스. labs/ax-qa 회귀 0.96→1.0.
- [x] **B. 토큰 집계 조사 + cache 필드 분리** — `claude.py` tokens shape 4 필드 (input/output/cache_creation/cache_read). rubric "토큰 효율" 축 설계안 E 로 전달. `notes/v0.2-token-investigation.md`.
- [x] **C. 자동 diff post-commit hook** — `.ax-generated` 매니페스트 + `install_ax_diff_hook.sh` + `ax_post_commit.py`. pytest 15 케이스 + smoke test 완료.
- [x] **D. `/ax-feedback` CLI** — `plugin/skills/ax-feedback/SKILL.md` (team-ax 첫 실제 skill) + `scripts/ax_feedback.py`. pytest 14 케이스 + 첫 실 feedback row 1개 보존.
- [x] **E. `ax-implement` (C') 패턴 — 파이프 검증** — team-product 포팅 + labs 래퍼 + haru:7475bef fixture + 범용 rubric + iter 1 0.886 → improve → iter 2 1.0. **파이프 검증 완료. 결함 1 (자연어 압축 ≠ codification) 실증.**
- [⏭] **F. haru 실전 첫 적용** — v0.3 이월. **결함 2 (`claude -p` one-shot ≠ tool loop) 실증.** team-product/product-qa 의 multi-step + Playwright MCP 필수 흐름을 v0.1 labs/ax-qa 로 원천 재현 불가.
- [⏭] **G. 대시보드 Live poll** — v0.3 이월. F 데이터 의존.
- 📝 **v0.2 의 수확**: 파이프 증명 1건 + 구조 결함 실증 2건. v0.3 는 리서치(Phase 0) 먼저. 상세: `notes/2026-04-11-v0.2-e-f-codification-insight.md`, `notes/2026-04-11-v0.3-research-scope.md`.

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
