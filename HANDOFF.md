# HANDOFF — v0.2 마감 → 다음 세션 (v0.3 Phase 0 리서치)

**작성 시점**: 2026-04-11 (v0.2 E/F 마감 직후)
**다음 작업**: **v0.3 Phase 0 — 리서치** (코드 구현 아님, 문서/실험 중심)

## 이전 세션 요약 (1줄)

v0.2 E 로 levelup loop 파이프 검증 성공 (iter 1 0.886 → improve → iter 2 1.0), **동시에 구조 결함 2개 실증**: (1) 자연어 압축 ≠ codification, (2) `claude -p` one-shot ≠ Claude Code tool loop. F/G 이월. v0.3 는 리서치부터.

## 반드시 먼저 읽을 문서 (순서대로)

1. **`notes/2026-04-11-v0.2-e-f-codification-insight.md`** ⭐ 이번 세션 회고 본체. 두 결함의 정의 + 하이브리드 구조 제안.
2. **`notes/2026-04-11-v0.3-research-scope.md`** ⭐ v0.3 Phase 0 리서치의 3 축 / 6 실험 / 산출물 / 종료 기준. **다음 세션 진입점.**
3. **`versions/v0.2/plan.md`** — E 체크박스 모두 ✅, F/G 이월 사유 명시.
4. **`BACKLOG.md`** — v0.3 Phase 0 (리서치) + Phase 1+ (재설계) 구조로 정돈됨.
5. **`PROJECT_BRIEF.md`** — v1.0 까지의 로드맵.
6. **`CLAUDE.md`** — 3 레이어 / 6 stage / Gotchas.
7. 메모리: `feedback_progressive_codification.md` — SKILL.md 자연어 vs script 원칙 (이번 세션에서 "자연어 압축은 codification 아님" 으로 더 정교화됨).

## 현재 환경 상태

### git

- 브랜치: `main`
- 직전 커밋:
  ```
  (예정) v0.2 마감 — F/G 이월 + 구조 결함 2개 실증 + v0.3 리서치 스코프
  4764f1e v0.2 E — ax-implement (C') 파이프 검증 + codification 인사이트
  0ae1f8d HANDOFF.md — v0.2 중반 세션 → 다음 세션 인계
  3174902 v0.2 D — /ax-feedback CLI + team-ax 첫 실제 skill
  ```

### 코드 / 파일

- `plugin/skills/ax-implement/SKILL.md` — **원본 295줄 복구** (hash `6a441acf`). team-product 포팅 상태.
- `plugin/skills/ax-implement/SKILL.iter2-snapshot.md` — v0.2 E 에서 levelup loop 가 생성한 54줄 압축본. v0.3 비교 참고용 보관.
- `labs/ax-implement/` — program.md + rubric.yml (범용) + script.py + `input/haru-7475bef/` + logs/ + best/
- `labs/ax-qa/` — v0.1 동결 상태 (건드리지 않음)
- 단위 테스트 52 케이스 모두 통과 (`.venv/bin/python -m pytest tests/ -q`)

### Supabase (project id `aqwhjtlpzpcizatvchfb`)

| 테이블 | row 수 | 비고 |
|---|---|---|
| `levelup_runs` | v0.1 + v0.2 A (ax-qa) + v0.2 E (ax-implement) 2 run 총 누적 | E 의 iter 1 / iter 2 / summary 포함 |
| `interventions` | 0 | F 이월로 실 수집은 v0.3 후 |
| `feedback_backlog` | 1 | v0.2 D smoke row 보존 |
| `product_runs` | 0 | v0.3 |

### Python / 환경

- `.venv/bin/python` 활성
- `.env`: SUPABASE_URL + ANON_KEY + SERVICE_ROLE_KEY
- 테스트: `.venv/bin/python -m pytest tests/ -q` → 52 통과

## 이번 세션 (v0.2 E/F) 이 배운 것

### 결함 1 — 자연어 압축 ≠ codification (E)

- levelup loop 가 SKILL.md 를 295줄 → 54줄 로 압축 + HARD RULES R-LEN/R-DRY 섹션 추가
- 하지만 R-LEN/R-DRY 는 여전히 자연어 — Claude 가 매번 해석
- **진짜 codification** 은 자연어가 `[run: scripts/check_r_len.py]` 로 교체돼야 함
- 이번 run 은 "자연어 → 자연어(압축)" 까지만. **codification 0 단계**.

### 결함 2 — `claude -p` one-shot ≠ Claude Code tool loop (F)

- `team-product/skills/product-qa/SKILL.md` (280줄) 은 `[setup] → [plan] → [execute] → [signoff]` multi-step
- 필수 도구: Playwright MCP, axe-core, Lighthouse, 서버 제어, 스크린샷
- v0.1 `labs/ax-qa` 는 `subprocess.run → claude -p` one-shot 이라 이 도구 전부 원천 접근 불가
- fixture text 보고 "diff 기반 코드 리뷰 요약" 만 뽑음 → QA 가 아니라 "review summary 자동화" 수준
- 이는 ax-qa 고유 문제가 아니라 **levelup loop 전체의 실행 환경 한계**

### 공통 원인

> `subprocess.run(["claude", "-p", prompt])` 는 Claude Code 의 tool loop 이 아니라 single-shot LLM 호출이다.

Claude Code 런타임 안에서만 되는 것 (`claude -p` 에서 불가):
- Bash/Read/Write tool call
- MCP server (Playwright, Supabase)
- Agent tool (서브에이전트 호출)
- Skill load / `/command` 호출
- interactive tool loop

### 오너가 지적한 과거 경험

my-agent-office 에서 Ralph loop 을 Python script 로 하려다 제약 많아 skill 로 풀었던 경험과 **동일한 벽**. moomoo-ax 가 "Python 만으로 가능" 가정한 v0.1~v0.2 의 전제가 깨진 지점.

## 다음 세션 — v0.3 Phase 0 리서치 시작점

`notes/2026-04-11-v0.3-research-scope.md` 를 읽고 그대로 수행.

**3 축**:
1. `docs/claude-code-spec/` 레퍼런스 구축 (skill/plugin/command/agent/hook/cli/permissions)
2. Claude Code CLI tool-enabled 호출 가능성 탐색 (`--allowedTools`, skill load, 재귀 호출 등)
3. 하이브리드 loop 실험 6개 (echo / stateful / recursion / skill-load / cost / MCP)

**종료 기준**:
- 축 2 의 7개 문서 초안
- 축 1 의 세부 질문 모두 "확인/불가능/조건부" 판정
- 축 3 의 실험 6개 모두 결과 기록
- `notes/2026-04-12-v0.3-feasibility.md` — Path A (하이브리드) vs Path B (완전 skill) 선택 + 근거

**범위 밖** (판정 전 코드 구현 금지):
- `labs/ax-implement` 재설계
- 새 stage 포팅
- 대시보드 카탈로그

### 첫 세션 권장 순서

1. `notes/2026-04-11-v0.3-research-scope.md` 재확인
2. `docs/claude-code-spec/` 디렉토리 생성 + README.md
3. `claude --help` 풀 출력 + 각 flag 조사 → `docs/claude-code-spec/cli.md` 초안
4. `claude-code-guide` 플러그인 호출해 skill/plugin/hook/command/agent 규약 수집 → 각 md 초안
5. 실험 1 (echo) — Python 이 `claude --allowedTools Read -p "Read file X and echo it"` 실 호출 + 결과 분석

## 금지 사항

- **v0.3 코드 구현 금지** (리서치 판정 전)
- **rubato 에 ax-* 산출물 적용 금지** — 여전히 유효. 원칙 재확인.
- **labs/ax-qa/ 건드리지 말 것** — v0.1 smoke test 로 동결. ax-qa 포팅은 v0.3 재설계 후.
- **태스크 tool 사용 금지** — 메모리 가드라인.
- **`/ax-diff` 수동 명령 구현 금지** — v0.3.
- **대시보드 v2 재설계 금지** — Phase 0 리서치 후 판단.

## v0.2 Retro 한 줄

> E 로 파이프를 증명했고 F 로 Python one-shot 의 한계를 실증했다. 수확은 파이프 1건이 아니라 **"벽 2개의 위치" 를 정확히 찍었다는 것**. v0.3 는 그 벽을 피하거나 넘는 설계를 해야 하며, 그 판단은 리서치 결과에 달려있다.

## 커맨드 치트시트

```bash
# 테스트 회귀
.venv/bin/python -m pytest tests/ -q

# ax-implement 재실행 (참고)
.venv/bin/python src/loop.py ax-implement --user yoyo --fixture haru:7475bef \
  --input labs/ax-implement/input/haru-7475bef --max-iter 3 --threshold 0.95

# /ax-feedback 수동
.venv/bin/python scripts/ax_feedback.py --priority high --stage v0.3-research "..."

# post-commit hook dry-run
MOOMOO_AX_DRY_RUN=1 .venv/bin/python scripts/ax_post_commit.py /path/to/target
```
