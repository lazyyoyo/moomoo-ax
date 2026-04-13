# HANDOFF — v0.3 plan 전면 재편 중 (product → meta → levelup 순서로 전환)

**작성 시점**: 2026-04-13
**다음 작업**: team-product 의 product-implement 원문을 직접 읽고, 오너 기준으로 (자연어 유지 vs script/코드 분리) 을 분류한 뒤 `versions/v0.3/plan.md` 를 전면 재편한다.

## 한 줄 요약

Phase 0 (리서치) + Phase 1a (claude.py 옵션 확장) 은 커밋 완료. 이후 **v0.3 전체 방향이 바뀜** — product loop 먼저, meta loop 관찰, levelup 은 v0.4 이월. 새 세션에서 team-product 원문을 직접 읽고 plan 을 다시 쓴다.

## 반드시 먼저 읽을 문서 (순서대로)

1. **이 HANDOFF** — 현재 위치
2. **`PROJECT_BRIEF.md`** — 3 레이어 정의 (product/levelup/meta loop). 이 정의는 그대로 유지. 구축 순서만 바뀜.
3. **`CLAUDE.md`** — 6 stage 메뉴, Gotchas
4. **`notes/2026-04-11-v0.3-feasibility.md`** — Phase 0 판정 리포트. Path A (하이브리드) 채택 근거. 필수.
5. **`versions/v0.3/plan.md`** — **현재 구조는 낡음**. 재편 대상.
6. **`docs/claude-code-spec/`** — Claude Code CLI/skill/plugin/hook/agent 공식 규약. 영구 레퍼런스.
7. **`docs/references/mao/team-product-map.md`** / `team-design-map.md` — 요약본. **맥락 유실 위험. 참고만. 원문 직접 읽기 우선.**
8. (메모리) `feedback_progressive_codification.md` — 자연어 vs script 원칙

## 이번 세션에서 정해진 새 방향 (핵심)

### 1. 구축 순서 전환

원래 v0.1~v0.3 plan 은 levelup loop 를 먼저 만들었다. 그런데 **"뭘 개선할지" 가 사전에 안 나와서** v0.2 E 가 공허했다 (SKILL.md 를 추상적으로 압축만 한 결과).

새 순서 (PROJECT_BRIEF 의 레이어 정의는 그대로):

```
product loop 먼저 생성 (team-ax/ax-implement 를 실제 돌아가게)
    ↓
meta loop 조회 인프라 (개입 횟수 / 토큰 관찰)
    ↓
levelup loop 개시 (관찰 데이터로 개선 대상 명확해진 후)
```

### 2. v0.3 범위 축소

- **1 stage only**: ax-implement 1개만. 나머지 (ax-qa, ax-design 등) 는 v0.4~v0.5.
- **levelup loop smoke 는 v0.4 이월**. v0.3 는 product + meta 까지만.
- **비용/시간 판단 기준 제외**: "돌아가는가" 이진 기준. 최적화는 v0.5+.

### 3. Codification 기준 (이번 세션에서 교정된 핵심)

이전에 내(Claude) 가 착각한 타깃:
- ❌ R-LEN/R-DRY 같은 **검증 규칙** 을 AST 스크립트로 뺌 (v0.2 E 에서 식별됐던 것)

오너의 진짜 의도:
- ✅ **절차적, 결정론적 step** 을 script/코드로 뺌
- 예: "브랜치 생성", "디렉토리 초기화", "템플릿 복사", "테스트 실행", "린트", "commit", "PR 생성"

**기준**:

| 자연어로 유지 (LLM 강점) | script/코드로 분리 (결정론) |
|---|---|
| spec 어떻게 작성할지 판단 | git checkout -b feat/X |
| 에지 케이스 열거 | 템플릿 파일 생성 |
| 코드 품질 판단 | 테스트/린트 실행 |
| 요구사항 해석 | 디렉토리 구조 초기화 |

"LLM 이 **해석해야 하는** 부분은 자연어, **그냥 실행하면 되는** 부분은 script."

## 현 git 상태 (세션 종료 시점)

- 브랜치: `main` (origin 대비 10 커밋 ahead)
- 최근 커밋:
  ```
  (이 HANDOFF + 매핑 문서 커밋 예정)
  ae04626 v0.3 Phase 1a — claude.py 옵션 확장 + stream-json 파서
  34b89d1 v0.3 Phase 0 — 리서치 + 판정 + v0.3 plan
  81f39c1 v0.2 마감 — F/G 이월 + 구조 결함 2개 실증 + v0.3 리서치 스코프
  ```

## 코드/파일 현황

### 이미 커밋된 것

- **Phase 0 산출물**:
  - `docs/claude-code-spec/` — 10개 파일, 공식 규약
  - `notes/v0.3-experiments/exp-01~06.md` — 실험 6개 all green
  - `notes/2026-04-11-v0.3-feasibility.md` — Path A 판정
  - `versions/v0.3/plan.md` — **낡음. 재편 대상.**

- **Phase 1a 코드 변경**:
  - `src/claude.py` — `allowed_tools`/`permission_mode`/`plugin_dir`/`bare`/`setting_sources` 옵션 + `parse_stream_json()` + `tool_events` 반환
  - `src/loop.py` — program.md 의 `call_options` 를 env 로 script.py 에 전달
  - `labs/ax-implement/program.md` — frontmatter 에 call_options 추가
  - `labs/ax-implement/script.py` — env 수신
  - `tests/test_claude_call.py` + `test_loop_call_options.py` — 신규 35 케이스
  - 단위 테스트 87/87 통과

### 이번 세션에서 추가 (HANDOFF 와 같이 커밋)

- `docs/references/mao/team-product-map.md` (377줄) — team-product 요약
- `docs/references/mao/team-design-map.md` (153줄) — team-design 요약
- `notes/v0.3-experiments/phase1a-run.log` — Phase 1a 실 1회 실행 로그 (참고용)
- `labs/ax-implement/logs_v0.2-e/` + `best_v0.2-e/` — v0.2 E 결과 보존
- `plugin/skills/ax-implement/SKILL.md.v0.2-e-original` — 원본 백업
- `labs/ax-implement/logs/001.json` + `best/` — Phase 1a 1회 실행 결과 (참고용)

### Phase 1a 실 실행 결과 (1회)

- fixture: `haru-7475bef`
- iter 1 에 score 1.0 → threshold 도달 즉시 종료
- cost $0.92, duration 74.4s
- **단, tool_call_count 가 log_data 에 저장 안 됨 (버그)** → "tool loop 이 실제로 발화했는지" 는 이 log 만으론 모름
- v0.2 E 대비 비교는 의미 없다고 결론 (v0.2 E 자체가 tool 없는 실행이라 베이스라인 부적절)

## 다음 세션 시작 순서

### 1. (5분) 컨텍스트 재확보
- 이 HANDOFF 읽기
- `PROJECT_BRIEF.md` + `CLAUDE.md` + `notes/2026-04-11-v0.3-feasibility.md` 훑기
- `versions/v0.3/plan.md` 낡은 상태 인식

### 2. (30~60분) team-product/product-implement 직접 읽기
원문 경로: `~/hq/projects/my-agent-office/plugins/team-product/skills/product-implement/`
- `SKILL.md` (258줄) — 본체
- `references/preflight-checklist.md`
- `references/review-checklist.md`
- `references/security-rules.md`
- `references/backpressure-pattern.md`
- `templates/PLAN_TEMPLATE.md`

관련 agent 원문: `~/hq/projects/my-agent-office/plugins/team-product/agents/`
- product-implement 가 호출하는 agent 선별해서 원문 읽기 (map.md 에 호출 관계 있음, 참고용)

**읽으면서 섹션/지시마다**:
1. 진행 내용 (무엇을 하는가)
2. 자연어 유지 vs script/코드 분리 판단 (위 기준 적용)
3. 제외/보완할 부분 — **옵셔널**. 1,2 확정 후 levelup loop 에서 처리 가능.

### 3. v0.3 plan 전면 재편
단계 2 결과를 근거로 `versions/v0.3/plan.md` 재작성.

제안하는 새 Phase 구조 (지난 세션에서 합의한 뼈대):
```
Phase 0 (✅ 완료) 리서치
Phase 1a (✅ 완료) claude.py 옵션 확장 — meta loop 인프라로 재배치

Phase A: product loop — ax-implement 완성판
  - team-product/product-implement 구조를 team-ax/ax-implement 로 이관
  - 자연어 유지할 것 / script 로 뺄 것 을 명시적으로 구분해서 이관
  - Claude 공식 skill 구조 (SKILL.md + scripts/ + references/ + templates/) 준수
  - 검증: `claude --plugin-dir plugin -p "/team-ax:ax-implement ..."` end-to-end

Phase B: meta loop — 조회 인프라
  - product_runs 자동 수집 hook
  - 기존 interventions 와 결합, stage 별 집계
  - 대시보드 확장 (기존 재사용)

Phase C: 마감 retro + v0.4 로 levelup smoke 이월
```

## 금지 사항

- **태스크 tool 사용 금지** (메모리 가드라인)
- **rubato / haru / rofan-world 등 외부 프로젝트 파일 직접 수정 금지** — 허브 CLAUDE.md 규칙
- **커밋/주석/문서 한글**, 변수/함수명 영문 (글로벌 CLAUDE.md)
- **키/토큰 하드코딩 금지** (환경 변수만)
- **labs/ax-qa 건드리지 말 것** — v0.1 동결 유지
- **rnd/ (meta loop 스크래퍼/게이터/evolver) 건드리지 말 것** — v1.x
- **세션 종료 제안은 토큰 기반으로만** (메모리 가드라인)

## 새 세션에서 절대 하지 말 것

- **team-product-map.md 만 보고 plan 재편하지 말 것** — 요약본이라 맥락 유실 있음. 반드시 원문 직접 읽기.
- **v0.2 E 결과와 비교하는 벤치마크 짜지 말 것** — v0.2 E 자체가 tool 없는 실행이라 베이스라인 부적절.
- **R-LEN/R-DRY 같은 검증 규칙 AST 추출 경로로 가지 말 것** — 오너가 원한 codification 과 다른 방향.
- **levelup loop 구현 재개하지 말 것** — v0.3 에선 product + meta 까지만, levelup smoke 는 v0.4.

## 커밋 치트시트

```bash
# 테스트 회귀
.venv/bin/python -m pytest tests/ -q   # 87 passed 기대

# labs/ax-implement 실 실행 (Phase 1a 시점 레퍼런스, 지금은 재실행 의미 제한)
.venv/bin/python src/loop.py ax-implement --user yoyo \
  --fixture haru:7475bef \
  --input labs/ax-implement/input/haru-7475bef \
  --max-iter 3 --threshold 0.95

# post-commit hook dry-run
MOOMOO_AX_DRY_RUN=1 .venv/bin/python scripts/ax_post_commit.py /path/to/target

# /ax-feedback
.venv/bin/python scripts/ax_feedback.py --priority high --stage v0.3-plan "..."
```

## 이번 세션 한 줄 수확

> v0.3 plan 을 **product → meta → levelup 순서로 뒤집는 결정**. 그리고 codification 의 진짜 타깃을 "검증 규칙 AST 추출" 이 아니라 "절차적 step 을 script 로 뺌" 으로 재정의. 이 두 결정이 다음 세션의 나침반.
