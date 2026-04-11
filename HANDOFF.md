# HANDOFF — v0.2 중반 → 다음 세션

**작성 시점**: 2026-04-11 (v0.2 D 커밋 직후)
**다음 작업**: v0.2 E (ax-implement (C') 패턴 정립) 준비 — **오너 sync 필요**

## 이전 세션 요약 (1줄)

v0.2 를 (C') Progressive Codification 패턴으로 방향 전환하고 A (R5 fix + `improve_target` 추상화) / B (토큰 집계 조사) / C (자동 diff post-commit hook) / D (`/ax-feedback` CLI) 4 블록을 연속 완료. **4/7 완료**. 엔진 안전, 수집 인프라 2 채널 가동, 첫 실 피드백 row 1개 확보.

## 반드시 먼저 읽을 문서 (순서대로)

1. **`PROJECT_BRIEF.md`** — v0.2 방향(C' 패턴) 반영된 최신 로드맵. v1.0 성공 기준에 "SKILL.md deterministic 규칙의 script 추출" 항목 추가됨. 사용자 섹션에 "실험 vs 공개 제품" 가드라인 명문화 (**haru 우선, rubato 는 v0.5+**).
2. **`versions/v0.2/plan.md`** — A/B/C/D 체크박스 전부 ✅, E/F/G 남음. **"(C') Progressive Codification" 섹션** 꼭 읽을 것. 여기에 SKILL.md 자체 개선 + deterministic 규칙의 script 추출 패턴이 설명돼 있음.
3. **`CLAUDE.md`** — 3 레이어 / 6 stage 메뉴 / Gotchas
4. **`notes/v0.2-token-investigation.md`** — 토큰 집계 조사 결과. **rubric 토큰 효율 축 설계안이 E 로 전달되는 지점** — E2 rubric.yml 작성 시 이 문서 참고.
5. 메모리: `feedback_progressive_codification.md` — SKILL.md 자연어 vs script 의 원칙. E 작업 전체의 기둥.

(선택) `versions/v0.1/report.md` 는 v0.1 종료 상태 스냅샷. 필요 시만.

## 현재 환경 상태

### git

- 브랜치: `main` (origin 동기 X — 이번 세션 커밋 5개가 로컬. push 여부 오너 판단)
- 이번 세션 커밋 5개:
  ```
  3174902 v0.2 D — /ax-feedback CLI + team-ax 첫 실제 skill
  e60aff7 v0.2 C — 자동 diff 수집 post-commit hook
  aa72722 v0.2 B — 토큰 집계 조사 + cache 필드 분리
  d432bbe v0.2 A — R5 fix + improve_target 추상화 + 단위 테스트
  0eab6f8 v0.2 방향 확정 — (C') Progressive Codification + haru 실험장
  ```

### 코드

- `src/loop.py` — `improve_artifact` 경로 일반화 (python + markdown 지원, 구조 체크 + 백업 + skip 로그). `program.md` frontmatter 에서 `improve_target` 읽음. AX_VERSION v0.2.
- `src/claude.py` — tokens dict 4 필드 shape (`input`/`output`/`cache_creation`/`cache_read`). 기존 input/output 키 유지 → 대시보드 호환.
- `src/judge.py` — empty tokens 4 필드 shape.
- `src/db.py` — `log_intervention()`, `log_feedback()` 추가. `AX_VERSION = "v0.2"`. `log_feedback` 는 `return=representation` 으로 row id 회수.
- `labs/ax-qa/program.md` — frontmatter `improve_target: script.py` 추가 (기존 동작 명시).
- `scripts/ax_generated.py` — `.ax-generated.jsonl` 매니페스트 + `.ax-artifacts/` 헬퍼.
- `scripts/ax_post_commit.py` — post-commit hook 본체. `__file__` 기반 moomoo-ax 루트 해석. `MOOMOO_AX_DRY_RUN=1` 지원. hook 실패가 커밋 깨지 않도록 항상 0 exit.
- `scripts/install_ax_diff_hook.sh` — 대상 프로젝트 설치. post-commit marker 블록 idempotent append + `.gitignore` 자동 갱신.
- `scripts/ax_feedback.py` — `/ax-feedback` CLI 본체. arg / stdin / env / git 매핑 자동 추출.
- `plugin/skills/ax-feedback/SKILL.md` — team-ax 의 **첫 실제 skill**. 나머지 `plugin/skills/ax-*/` 는 아직 빈 폴더.
- `tests/` — pytest 52 케이스 (A 23 + C 15 + D 14), 전부 통과. 실행: `.venv/bin/python -m pytest tests/ -q`

### Supabase (project id `aqwhjtlpzpcizatvchfb`)

| 테이블 | row 수 | 비고 |
|---|---|---|
| `levelup_runs` | 2 runs (iter + summary 다수) | v0.1 첫 run + v0.2 A 회귀 run (1.0 score) |
| `interventions` | 0 | C 에서 smoke 후 정리. F (haru 실전) 에서 첫 실 row 예정 |
| `feedback_backlog` | **1** | D smoke 로 남긴 첫 실 피드백 (id `2a412956-dd69-44fd-bc22-45efafd5de19`, content 에 "v0.2 D 스모크" 포함). 대시보드 empty state 해제 검증 겸 보존 중. |
| `product_runs` | 0 | v0.3 에서 수집 시작 |

### Vercel

- https://moomoo-ax.vercel.app — 이전 세션 배포 그대로. 이번 세션 dashboard 코드 변경 없음.
- Feedback 탭 / North Star 탭이 실 feedback_backlog row 를 자동으로 읽음 → 새 세션 시작하기 전에 한 번 열어보면 empty state 해제 확인 가능.

### Python 환경

- `.venv/bin/python` — pyyaml, pytest 포함. 항상 venv 로 실행.
- `.env`: `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_ROLE_KEY` 3개 세팅됨.

## 이번 세션이 배운 것

### 방향 전환 (가장 중요)

**(C') Progressive Codification 패턴**이 v0.2 의 설계 기둥. 두 세션 대화의 수렴 결과:
- team-product 스킬을 seed 로 포팅해서 쓰자 (밑바닥 발명 X)
- levelup loop 가 SKILL.md 자체 개선 + **자연어 규칙의 script 추출** 둘 다 담당
- 자연어는 AI 자의적 해석 + 토큰 낭비의 원인. deterministic 한 단계를 코드로 굳혀가는 게 "하네스 자기 진화"의 실체.
- v0.2 범위는 **ax-implement 1 stage 만** 으로 축소 (패턴 정립이 과업).
- v1.0 성공 기준에도 이 항목 추가됨.

**실험장 원칙**: private 제품 우선 (haru), public 제품(rubato) 은 v0.5+. 나쁜 AI 산출물이 public 으로 흘러가는 리스크 회피.

### 기술적 발견

- **"input 5 token" 미스터리는 버그가 아니라 필드 해석 오류**였음. Claude CLI 는 system prompt + 도구 정의를 자동으로 cache layer 에 분리 → `input_tokens` 는 "이번 호출에서 새로 흘러들어온 non-cached" 만 찍힘. "print hello" 최소 프롬프트에도 `cache_creation_input_tokens = 36,796` (세션 baseline). 이제 4 필드 전부 수집. `total_cost_usd` 가 가장 정확한 단일 지표.
- **R5 fix 핵심 가드**: `extract_code_block` 이 여러 코드 블록 중 **가장 긴 것** 을 선택. 짧은 예시 블록이 전체 파일 덮어쓰는 사고 방지. + 언어별 구조 체크 (python: main/`__name__`, markdown: frontmatter name 또는 H2 2+). + 백업 (`.prev`).
- **post-commit hook 의 `.gitignore` 자동 추가 는 필수**. smoke 1회차에서 `.ax-generated.jsonl` 과 `.ax-artifacts/` 가 커밋에 같이 들어가는 문제 발견. install 스크립트에서 `.gitignore` 블록 자동 갱신하도록 추가함.
- **R6 해결**: post-commit hook 이 product_runs 에 의존하지 않도록 `.ax-generated.jsonl` 매니페스트 파일 기반으로 판정. v0.2 범위에 product_runs 자동 수집 없이도 동작.
- **`lazyyoyo` → `yoyo` 매핑**: `ax_feedback.py:GIT_USER_TO_AX_USER` 에 등록. jojo 추가 예정.

### 테스트 패턴

- pytest 52 케이스 모두 실 Claude 호출 없는 mock 기반 — 빠르고 저렴 (0.64s).
- subprocess 기반 임시 git repo fixture (`tmp_git_repo`) 로 post-commit hook end-to-end 검증.
- `types.SimpleNamespace` 로 db 모듈 mock — argparse 주입 + monkeypatch 조합.

## 다음 액션: v0.2 E 시작 준비

### 오너 인터뷰 / sync 먼저 필요

1. **haru fixture 선정** — ax-implement 의 첫 cycle fixture 로 쓸 haru 의 **작은 feature 커밋 1건** (30~100 줄 수준). 후보 조건:
   - 구현 의도가 명확 (decisions.md / BACKLOG.md 에 맥락 남아 있는 것)
   - 단일 파일 또는 2~3 파일 미만
   - 리팩토링 X, 순수 추가 또는 기능 추가
   - refactor/fix 가 아닌 feature (implement 는 "없던 걸 만드는" 성격)
   - 너무 단순(1-2줄 변경)이면 rubric 구분력 떨어짐

   **새 세션에서 할 일**: `~/hq/projects/journal/` 에 들어가서 git log + BACKLOG.md + HANDOFF.md 같이 보면서 후보 2~3개 뽑고 오너와 함께 선정.

2. **product-implement 포팅 시 버릴 것 확인** — team-product/skills/product-implement/SKILL.md 의 일부는 moomoo-ax 컨텍스트에서 불필요:
   - conductor 메인세션 / subagent planner/executor 구조는 그대로 안 들어감 (`src/loop.py` 가 Claude CLI 직접 호출이라 에이전트 계층 없음)
   - preflight 의 일부 체크리스트는 script 로 추출 가능한 후보
   - Codex Adversarial 리뷰 단계는 v0.2 범위 밖
   
   → **v0.2 에서는 복사 후 "불필요한 것 주석만"** 최소 편집 원칙 (plan R12). 본격 재구성은 levelup loop 가 담당.

### 인터뷰 없이 확정된 것 (plan v2.1 / notes / 전 세션 대화 기반)

- E1 포팅 → E2 래퍼 → E3 fixture → E4 첫 run → E5 improve 경로 검증 순서
- `labs/ax-implement/program.md` frontmatter: `improve_target: ../../plugin/skills/ax-implement/SKILL.md`
- rubric 축: 오너 기대치 + 정량 (타입/빌드/lint) + **토큰 효율** (`total_cost_usd` 권장, `output_tokens` 보조). 첫 run 을 기준선, 상대 비교로 감점. absolute threshold 는 v0.3.
- fixture_id 규약: `haru:{short_sha}`
- 첫 run threshold 는 낮게 (0.85). 너무 엄격하면 improve 경로만 계속 탐.

### E 완료 기준 체크박스는 plan.md 에 이미 상세히 있음 — 그거 따라가면 됨.

## 보류 / 열린 것

- **대시보드 cache breakdown 차트** — v0.3 작업 (현재 tokens 탭은 input/output 만 보여줌, cache 필드는 DB 에 있지만 미표시).
- **product_runs 자동 수집** — v0.3. 현재 C hook 은 `.ax-generated` 매니페스트 기반이라 의존성 없음.
- **/ax-diff 수동 명령** — v0.3. 현재 C hook 하나로 충분.
- **ax-qa 포팅** — v0.3. v0.1 `labs/ax-qa` 는 동결, smoke test 용으로만 남음.
- **재현성 체크 / 북극성 기준선 숫자** — v0.3, 실전 데이터 2~3건 본 뒤.
- **대시보드 v2 재설계 여부** — v0.2 E/F 데이터 본 뒤 v0.3 에서 판단.

## 금지 사항

- **rubato 에 ax-* 산출물 적용 금지** — public 제품. v0.5+ 에서만. v0.2 는 haru 전용.
- **labs/ax-qa/ 건드리지 말 것** — v0.1 smoke test 로 동결. improve_target 추상화 회귀 테스트 기반. (ax-qa 포팅은 v0.3.)
- **product_runs 자동 수집 추가 금지** — 범위 밖. C hook 은 매니페스트 기반으로 이미 해결됨.
- **자연어 SKILL.md 를 새로 작성 금지** — E1 은 **team-product 포팅 (복사)**. 발명 X. 자연어 규칙의 재작성은 levelup loop 가 담당.
- **대시보드 v2 재설계 금지** — 범위 밖. Live 30초 poll 하나만 v0.2 G 에서.
- **`/ax-diff` 명령 구현 금지** — v0.3.
- **태스크 tool 도구 사용 금지** (세션 내 작업 추적에 쓰지 말 것) — 메모리에 저장된 가드라인.

## 이번 세션 Retro 한 줄

> 방향 전환(C')을 한 세션 내에 결정하고 그 패턴을 뒷받침하는 엔진 안전성(A) + 수집 인프라(B/C/D) 를 모두 끝낸 게 가장 큰 수확. E 가 시작할 때 환경은 "준비 완료" 상태. 다음 세션은 fixture 선정 → 포팅 → 첫 cycle 흐름을 의심 없이 타면 됨.

## 커맨드 치트시트

```bash
# 테스트 회귀
.venv/bin/python -m pytest tests/ -q

# ax-qa 회귀 run (v0.1 동일 조건)
.venv/bin/python src/loop.py ax-qa --user yoyo --fixture rubato:0065654 --max-iter 2 --threshold 0.95

# /ax-feedback 수동 호출
.venv/bin/python scripts/ax_feedback.py --priority high --stage ax-implement "..."

# post-commit hook 설치 (대상 프로젝트)
scripts/install_ax_diff_hook.sh ~/hq/projects/journal

# post-commit hook dry-run (manifest 매칭만 찍고 insert 안 함)
MOOMOO_AX_DRY_RUN=1 .venv/bin/python scripts/ax_post_commit.py /path/to/target

# DB 조회 (Supabase MCP)
# select count(*) from levelup_runs / interventions / feedback_backlog / product_runs;
```
