# v0.3 — Hybrid loop + Progressive Codification + ax-qa 포팅

## 한 줄 목표

> **"Phase 0 리서치로 드러난 하이브리드 모델 (Python 하네스 + `--plugin-dir plugin` + stream-json) 로 levelup loop 을 업그레이드하고, SKILL.md 의 자연어 규칙 중 최소 2개를 실제 script 로 추출하고, ax-qa 를 MCP 포함해서 포팅한다."**

v0.2 는 **두 벽** 을 실증하며 마감했다:
1. 자연어 압축 ≠ codification
2. `claude -p` one-shot ≠ Claude Code tool loop

v0.3 Phase 0 리서치 (`notes/2026-04-11-v0.3-feasibility.md`) 가 밝힌 결론:
- **벽 2 는 반박됨** → `src/claude.py:38` 의 플래그 누락이 원인. fix 는 한 줄 근방.
- **벽 1 은 유효** → SKILL.md 안의 deterministic rule 을 `scripts/*.py` 로 빼는 것이 본 작업.

따라서 v0.3 는 **전면 재설계가 아니라 점진 리팩터 + deterministic 추출 + ax-qa 포팅**이다.

## 범위 원칙

- **Phase 단위로 쪼갠다**: 리서치 (완료) → 베이스라인 회귀 → codification 1축 → codification 2축 → ax-qa 포팅 → 마감. 각 Phase 는 단독으로 체크 가능한 완료 기준.
- **Phase 간 skip 금지**: Phase 1 의 베이스라인 회귀 없이 Phase 2 의 scripts 분리 효과를 측정할 수 없다. Phase 2 없이 Phase 3 의 rubric 가중치를 조정하면 안 된다.
- **v0.2 의 `labs/ax-implement` 를 직접 비교 대상으로 유지**. 같은 fixture (haru-7475bef) + 같은 rubric 구조 + 새 하이브리드 호출 → 점수/비용/토큰 비교.
- **Phase 4 (ax-qa 포팅) 전까지 `labs/ax-qa` 건드리지 않음**. v0.1 동결 유지.
- **허브 CLAUDE.md 규칙 준수**: rubato / haru / rofan-world 프로젝트 파일 직접 수정 금지. 실전 투입은 각 프로젝트 BACKLOG 에 태스크 요청 형태로.
- **프로젝트 경계**: v0.3 구현 산출물은 moomoo-ax 자체에만 반영 (labs, plugin, src, docs). dogfooding 은 **참고만**.

## 핵심 아키텍처 변경 (요약)

```
v0.2 (as-is):
  loop.py → claude.py:call()
             └─ subprocess.run(["claude", "-p", prompt, "--output-format", "json"])
             └─ tool 없음, plugin 없음, MCP 없음

v0.3 (to-be):
  loop.py → claude.py:call()
             └─ subprocess.run([
                   "claude", "-p", f"/team-ax:{stage} {args}",
                   "--plugin-dir", "plugin",
                   "--allowedTools", <stage 별 화이트리스트>,
                   "--permission-mode", "acceptEdits",
                   "--output-format", "stream-json", "--verbose",
                   "--bare",                      # 재현성
                   "--setting-sources", "project,local",
                ])
             └─ tool loop + plugin skill + MCP (stage 의존)
             └─ per-tool_use / tool_result event 수집
             └─ per-tool cost 분해
```

SKILL.md 의 자연어 HARD RULES 중 최소 2개 (R-LEN, R-DRY) 를 deterministic scripts 로 분리:

```
plugin/skills/ax-implement/
├── SKILL.md              # allowed-tools 에 Bash(scripts/*) 추가
│                         # HARD RULES 섹션의 자연어 → !`scripts/check_r_len.py`
├── scripts/
│   ├── check_r_len.py    # AST 기반 함수 길이 검사
│   └── check_r_dry.py    # AST + regex 기반 중복 상수/리터럴 검사
└── references/           # v0.3 도 장식 상태 유지. inline 합치기는 v0.4
```

## Phase 로드맵

### Phase 0 — 리서치 ✅ 완료 (2026-04-11)

- [x] `docs/claude-code-spec/` 9개 파일 초안
- [x] `notes/v0.3-experiments/exp-01..06` 실험 로그
- [x] `notes/2026-04-11-v0.3-feasibility.md` 판정 리포트
- [x] **결론**: Path A (하이브리드) 채택. 벽 2 반박, 벽 1 유효.

### Phase 1 — 베이스라인 회귀 (Path A 실증)

> **"플래그 3~4개 추가만으로 v0.2 E 의 run 과 동일/더 좋은 결과가 나오는지 직접 비교한다. 여기서 막히면 Phase 2~4 모두 무의미."**

#### 완료 기준

- [ ] **1.1 `src/claude.py:call()` 시그니처 확장** — 키워드 인자로 option 세트를 받는다
  - 기본값: `allowed_tools=["Read","Write","Edit","Bash","Grep","Glob"]`, `permission_mode="acceptEdits"`, `output_format="stream-json"`, `plugin_dir=None`, `bare=False`, `setting_sources=None`
  - 반환 shape 확장: `{success, output, tokens, cost_usd, duration_sec, tool_events: [...], error}` — `tool_events` 는 stream-json 의 tool_use/tool_result pair 리스트
  - 기존 `output_format="json"` 폴백 유지 (호환성)
  - 단위 테스트 추가 (fixture 기반 stream-json 파싱)
- [ ] **1.2 stream-json 파서 작성**
  - `src/claude.py` 내부 헬퍼: stdout line 단위 JSON parse → `{type,subtype}` 라우팅
  - `system/init` 이벤트에서 cwd/session_id/model/permissionMode/plugins 추출
  - `assistant/tool_use` → tool_events 에 `{tool_name, tool_input, usage_per_msg}` 누적
  - `user/tool_result` → 가장 가까운 tool_events entry 에 `tool_result` 병합
  - `result` → 기존 필드 (result/total_cost_usd/usage/num_turns) 추출
  - `rate_limit_event` → log 에 WARN 출력 + db 에 status 기록 (optional)
- [ ] **1.3 `src/loop.py` 의 Claude 호출 경로 업데이트**
  - `run()` 이 `plugin_dir=<abs path to plugin>` 을 주입
  - stage 별 allowed_tools 는 `labs/{stage}/program.md` frontmatter 에서 읽음 (`allowed_tools:` 필드 신규)
  - 호출 커맨드를 `/team-ax:{stage} {args}` 슬래시 호출 형태로 빌드
  - 기존 "프롬프트 안에 SKILL.md 내용을 통째로 주입" 경로는 삭제
- [ ] **1.4 `labs/ax-implement/program.md` frontmatter 에 `allowed_tools` 추가**
  - `improve_target: ../../plugin/skills/ax-implement/SKILL.md` 유지
  - `allowed_tools: [Read, Write, Edit, Bash, Grep, Glob]` 신규
- [ ] **1.5 `labs/ax-implement/script.py` 를 얇은 wrapper 로 재작성**
  - fixture 를 자식 세션이 접근할 수 있게 파일로만 전달 (stdin 금지)
  - Claude 호출은 `src/claude.py:call()` 만 부르고, 슬래시 호출 프롬프트를 빌드
  - 이전 "SKILL.md 텍스트 주입" 로직 제거 (이제 plugin-dir 로 자동 로드)
- [ ] **1.6 v0.2 E 와 직접 비교 실행**
  - 같은 fixture `haru-7475bef`, 같은 rubric, `--max-iter 3 --threshold 0.95`
  - 기준: v0.2 E run 결과 (iter1 0.886 → iter2 1.0, cost $0.xx)
  - v0.3 Phase 1 run 결과 저장: `labs/ax-implement/logs_v0.3-phase1/`
  - 점수/비용/토큰/num_turns/tool call 수 비교 표를 `notes/2026-04-1x-v0.3-phase1-baseline.md` 에 기록
- [ ] **1.7 회귀 판정**
  - PASS 조건: 점수 ≥ v0.2 E + 비용 ≤ v0.2 E × 1.5 (tool loop 오버헤드 감안)
  - FAIL 조건 시 원인 분석 + plan 수정 (Phase 2 진입 blocking)

#### 리스크 / 미지수

- **R1**: `-p` 모드에서 `/team-ax:ax-implement` 슬래시 호출이 **인자 전달 규약**에 맞는가? exp-04 에선 canary 스킬 + 단순 문자열만 테스트. 복잡한 multi-line fixture 주입은 실험 없음. → 1.5 에서 fixture 를 파일 경로로만 넘기고 SKILL.md 가 Read tool 로 읽게 설계.
- **R2**: v0.2 E 의 rubric 이 "tool 사용 여부" 를 점수화하지 않음 → 하이브리드 run 이 tool 을 많이 써도 점수에 반영 안 될 수 있다. Phase 3 에서 rubric 축 추가 고려.
- **R3**: baseline cost 가 v0.2 대비 크게 뛰면 (1.5× 상회) Phase 2~4 cost 예산 재산정 필요.

---

### Phase 2 — Progressive Codification 1축 (R-LEN)

> **"자연어 규칙 'R-LEN: 공개 함수 본체 60줄 이하' 를 deterministic `scripts/check_r_len.py` 로 분리한다. 동일 fixture 에서 Phase 1 run 보다 점수/비용/일관성이 개선되는지 측정."**

#### 완료 기준

- [ ] **2.1 `plugin/skills/ax-implement/scripts/check_r_len.py` 작성**
  - 인자: 체크할 `.ts`/`.py`/`.js` 파일 경로
  - 동작: AST (Python) 또는 `@typescript-eslint/parser` (TS) 로 함수 정의 순회 → 본문 라인 수 측정 → 60 초과 시 `{path, func_name, line_start, line_end, line_count}` 를 stderr 에 JSON 출력 + exit 1
  - 통과 시 stdout 에 `R_LEN_OK {count}` + exit 0
  - v0.3 에선 Python AST 만 우선. TS 는 최소 regex fallback (function/arrow 선언 끝 찾기).
  - `tests/test_check_r_len.py` — pass/fail 각 3 케이스
- [ ] **2.2 `plugin/skills/ax-implement/SKILL.md` 의 HARD RULES 섹션 리팩터**
  - R-LEN 규칙의 자연어 설명을 **호출 명령어 1줄로 교체**:
    ```markdown
    ## HARD RULES — R-LEN (function length)
    Before finalizing, run: !`python scripts/check_r_len.py <output_file>`
    If exit != 0, refactor flagged functions and re-run until it passes.
    ```
  - SKILL.md frontmatter `allowed-tools` 에 `Bash(python scripts/check_r_len.py:*)` 추가
- [ ] **2.3 re-run `labs/ax-implement` 를 Phase 1 과 동일 fixture 로**
  - iter 수 / script 호출 횟수 / 점수 / 비용 비교
  - `logs_v0.3-phase2/` 로 분리 저장
- [ ] **2.4 비교 분석 노트 작성**
  - `notes/2026-04-1x-v0.3-phase2-rlen.md`
  - "Claude 가 스크립트를 실제로 호출했는가 (tool_events 로 검증)", "R-LEN 위반 자진 fix 가 발생했는가", "자연어 시절 대비 비용 차이"
- [ ] **2.5 hook 검증 (선택)**
  - `plugin/hooks/hooks.json` 초안 — `PostToolUse` + `if: Bash(python scripts/check_r_len.py:*)` + 강제 검증 스크립트. v0.3 에선 실험 수준.

#### 리스크

- **R4**: Claude 가 스크립트를 **호출하지 않고 "통과한 것처럼" 답할 수 있다**. tool_events 에 `check_r_len.py` 호출이 없으면 자동 fail 처리하는 검증 레이어 필요 (Phase 2.5 hook 또는 rubric 축).
- **R5**: scripts 가 fixture 의 TS 코드를 잘 못 parse → false positive. v0.3 는 Python AST 만 확신하고 TS 는 warning.

---

### Phase 3 — Progressive Codification 2축 (R-DRY) + per-tool 회계

> **"R-DRY 규칙을 두 번째 script 로 분리하고, 동시에 v0.2 에 없던 per-tool_use 비용 로깅을 `levelup_runs` 에 저장한다."**

#### 완료 기준

- [ ] **3.1 `plugin/skills/ax-implement/scripts/check_r_dry.py` 작성**
  - 인자: 파일 경로
  - 동작: AST 로 string/number literal 수집 → 같은 값이 3회 이상 등장 + 상수 선언 없음 → 위반
  - 또는 import 문 중복 검출
  - `tests/test_check_r_dry.py` — pass/fail 케이스
- [ ] **3.2 SKILL.md HARD RULES — R-DRY 리팩터**
  - Phase 2 와 동일 패턴: 자연어 → `!`python scripts/check_r_dry.py <file>``
- [ ] **3.3 `src/db.py` schema 확장**
  - `levelup_runs` 테이블에 `tool_call_stats JSONB` 컬럼 추가
  - shape: `{ "Read": {"count": N, "tokens_in": ..., "tokens_out": ...}, "Write": {...}, "Bash": {...}, "mcp__plugin_playwright_playwright__browser_navigate": {...}, ... }`
  - Supabase migration 작성 + 적용
- [ ] **3.4 `src/loop.py` 가 per-tool stats 집계**
  - `claude.py` 의 `tool_events` 에서 tool 이름별 그룹화 → usage 누적
  - `log_run()` 에 `tool_call_stats` 전달
- [ ] **3.5 동일 fixture 재실행 + 분석**
  - `logs_v0.3-phase3/` 저장
  - 비교 노트: `notes/2026-04-1x-v0.3-phase3-rdry.md`
  - "R-LEN/R-DRY 두 script 를 Claude 가 자진 호출했는가" + "tool call 분포 (Read/Write/Bash/script)"
- [ ] **3.6 대시보드 cost breakdown 섹션 (최소)**
  - `dashboard/app/*` — 기존 `levelup_runs` 카드에 tool_call_stats 요약 배지 추가
  - 전체 재설계 X. 기존 카드에 1 줄 추가 수준.

#### 리스크

- **R6**: Supabase 스키마 변경이 v0.2 기존 row 와 호환 안 되면 마이그레이션 조심. `tool_call_stats` 는 nullable 로.
- **R7**: R-DRY 는 일반화가 어려움 (프레임워크마다 "중복" 기준 다름). v0.3 는 최소 버전만 — import 중복 + 같은 string literal 3회+.

---

### Phase 4 — ax-qa 포팅 (MCP 포함)

> **"v0.1 labs/ax-qa 동결을 풀고, team-product/product-qa 를 team-ax/ax-qa 로 포팅. 하이브리드 호출 + Playwright MCP 실사용을 haru 또는 격리 fixture 에서 검증."**

#### 완료 기준

- [ ] **4.1 team-product/skills/product-qa/SKILL.md 포팅**
  - `plugin/skills/ax-qa/SKILL.md` 작성
  - 필수 tool: `Bash`, `Read`, Playwright MCP (`mcp__plugin_playwright_playwright__*`), 필요 시 axe-core CLI / Lighthouse
  - `allowed-tools` frontmatter 에 MCP tool 이름 명시 (exp-06 에서 검증된 문법)
- [ ] **4.2 `labs/ax-qa` 재활성화**
  - v0.1 동결본은 `labs/ax-qa-v0.1-frozen/` 로 보존 (mv)
  - 새 `labs/ax-qa/` — program.md (`improve_target: ../../plugin/skills/ax-qa/SKILL.md`, `allowed_tools: [Read, Bash, mcp__plugin_playwright_playwright__*]`), rubric.yml (team-product/product-qa 의 완료 기준 재사용)
- [ ] **4.3 fixture 선정**
  - 우선 후보: haru 의 최근 UI 변경 commit OR 별도 격리 static site
  - 격리 우선: `labs/ax-qa/input/static-fixture/` 로 순수 HTML 몇 페이지 준비. 외부 프로젝트 의존성 제거.
- [ ] **4.4 첫 run**
  - `.venv/bin/python src/loop.py ax-qa --user yoyo --fixture static:v1 --max-iter 2 --threshold 0.9`
  - tool_events 에 `mcp__plugin_playwright_playwright__browser_navigate` / `_snapshot` / `_close` 가 실제로 나타나는지 확인
  - 비용 상한 $1.5/run 예상
- [ ] **4.5 `notes/2026-04-1x-v0.3-phase4-axqa.md`**
  - MCP 실사용 증거, 점수, 비용, 병렬 browser 인스턴스 관찰
- [ ] **4.6 R-LEN/R-DRY 수준의 codification 1개** (선택, stretch)
  - 예: "a11y 위반 수" 를 axe-core CLI 로 자동 측정 + stderr JSON → SKILL.md 가 호출

#### 리스크

- **R8**: Playwright MCP 가 자식 세션에서 spawn 될 때 browser 실행 오버헤드가 $0.5+ 라 비용 상한 재산정 필요.
- **R9**: haru 실전 투입 금지 → 격리 fixture 를 준비해야 함. 시간 비용 +1.
- **R10**: axe-core / Lighthouse 를 CLI 로 호출할 때 npm 설치 필요. team-ax 플러그인이 사용자 환경에 의존 → v0.4 에서 `bin/` 또는 `scripts/bootstrap.sh` 로 재검토.

---

### Phase 5 — v0.3 마감 (retro + BACKLOG 정리)

- [ ] **5.1 `versions/v0.3/report.md`** — Phase 1~4 요약 + 측정치 + 회고
- [ ] **5.2 BACKLOG.md 갱신** — v0.3 에서 식별된 후속 작업 (ax-design 포팅, `ax-autopilot`, 대시보드 v2) 을 inbox/ready 로 정리
- [ ] **5.3 PROJECT_BRIEF.md 버전 로드맵 섹션 업데이트** (v0.3 상태 반영)
- [ ] **5.4 HANDOFF.md 작성** — v0.4 진입 시 다음 세션이 바로 시작 가능하도록
- [ ] **5.5 PR 머지 + 태그 `v0.3.0`**

## Out of scope (v0.4+)

- **ax-design / ax-init / ax-deploy 포팅** → v0.4~0.5
- **`ax-autopilot` 상위 오케스트레이터** → v0.4
- **대시보드 v2 (카탈로그, Live auto-poll 등)** → v0.4 판단
- **rnd/ (meta loop 의 trend 수집 / gate / evolver)** → v1.x
- **재현성 수치 기준선 확정** → v0.4
- **team-ax 플러그인의 MCP 내장화** (사용자 환경 MCP 의존 탈피) → v0.4
- **Claude Code `--resume` 로 loop 연속성** → 불필요 판정 (exp-03)
- **Claude Agent SDK 도입** → 불필요 판정 (subprocess 패턴으로 충분)
- **R-LEN/R-DRY 외 추가 rule 의 codification** → 첫 2축 효과 측정 후 v0.4 로
- **TS AST 기반 정밀 check_r_len** (v0.3 는 regex fallback) → v0.4
- **자식 세션의 cache reuse 최적화** (`--exclude-dynamic-system-prompt-sections` 실험 포함) → 별도 실험 세션
- **product_runs 자동 수집** (ax-autopilot 종속) → v0.4

## 작업 순서

```
Phase 0 (✅ 완료)
  │
  ├─ Phase 1 (baseline regression)   ← blocking. 이게 PASS 해야 나머지 의미 있음
  │    └─ 1.1 claude.py 확장
  │    └─ 1.2 stream-json 파서
  │    └─ 1.3 loop.py 업데이트
  │    └─ 1.4 program.md frontmatter
  │    └─ 1.5 script.py 얇게
  │    └─ 1.6 직접 비교 실행
  │    └─ 1.7 PASS/FAIL 판정
  │
  ├─ Phase 2 (R-LEN codification)    ← Phase 1 PASS 후
  │    └─ 2.1 check_r_len.py
  │    └─ 2.2 SKILL.md 리팩터
  │    └─ 2.3 재실행
  │    └─ 2.4 비교 노트
  │    └─ 2.5 hook 검증 (optional)
  │
  ├─ Phase 3 (R-DRY + per-tool 회계) ← Phase 2 와 일부 병렬 가능
  │    └─ 3.1 check_r_dry.py
  │    └─ 3.2 SKILL.md 리팩터
  │    └─ 3.3 db schema
  │    └─ 3.4 loop.py 집계
  │    └─ 3.5 재실행
  │    └─ 3.6 대시보드 최소 추가
  │
  ├─ Phase 4 (ax-qa 포팅)            ← Phase 3 완료 후. Phase 1~3 의 패턴을 MCP 에 적용
  │    └─ 4.1 SKILL.md 포팅
  │    └─ 4.2 labs 재활성
  │    └─ 4.3 fixture
  │    └─ 4.4 첫 run
  │    └─ 4.5 분석
  │    └─ 4.6 codification (optional)
  │
  └─ Phase 5 (마감)                  ← Phase 4 완료 후
       └─ report / BACKLOG / BRIEF / HANDOFF / PR 머지
```

## 리스크 요약 (전체)

| # | 리스크 | 영향 | Mitigation |
|---|---|---|---|
| R1 | `-p` 모드 슬래시 호출 인자 규약 불일치 | 중 | fixture 를 파일 경로로만 넘김 |
| R2 | rubric 이 tool 사용을 반영 안 함 | 낮 | Phase 3 에 축 추가 고려 |
| R3 | baseline cost 1.5× 초과 | 중 | Phase 1 에서 판정, 초과 시 plan 수정 |
| R4 | Claude 가 스크립트 실 호출 없이 "통과한 척" | 높 | tool_events 검증 + hook 으로 강제 |
| R5 | TS AST parse 부정확 | 낮 | Python 만 확신, TS 는 warning |
| R6 | Supabase migration 기존 row 호환 | 낮 | nullable 컬럼만 추가 |
| R7 | R-DRY 일반화 어려움 | 중 | 최소 버전만 (import 중복 + string literal 3+) |
| R8 | Playwright browser spawn 비용 | 중 | Phase 4 에서 $1.5/run 상한 |
| R9 | haru 실전 금지 → 격리 fixture 구성 비용 | 낮 | static HTML 3~5 페이지 |
| R10 | axe-core/Lighthouse CLI 사용자 환경 의존 | 중 | v0.4 로 내장화 이월 |
| R11 | Phase 1 에서 `--bare` 가 예상 외 기능 차단 | 낮 | 1.6 실행 시 `--bare` 없이 비교 테스트 |
| R12 | stream-json 대량 출력이 stdout buffer 넘침 | 낮 | claude.py 에서 iterative read 또는 file redirect |

## 성공 기준 (v0.3 전체)

1. Phase 1 회귀 PASS — v0.2 E 대비 점수 유지 + 비용 ≤ 1.5×
2. Phase 2 에서 R-LEN 자연어 규칙이 deterministic script 로 완전 대체 + Claude 가 tool_events 에 `check_r_len.py` 호출을 보임
3. Phase 3 에서 R-DRY 두번째 script + per-tool 비용 분해가 `levelup_runs` 에 저장
4. Phase 4 에서 ax-qa 가 Playwright MCP 를 실 호출하며 첫 run 점수 ≥ 0.8
5. Phase 5 에서 v0.3.0 태그 + HANDOFF 작성

북극성 지표 (오너 개입 횟수) 는 v0.3 에선 측정만. 개선 여부 판정은 v0.4~v0.5 에서.

## 진행 메모

(구현 중 업데이트)

- 2026-04-11: Phase 0 완료 — 리서치 + 실험 6개 + 판정 리포트. Path A 채택.
- 2026-04-11: plan v1 작성 — Phase 1~5 골격 확정.
