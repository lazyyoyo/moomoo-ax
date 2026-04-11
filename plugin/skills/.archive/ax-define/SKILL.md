---
name: ax-define
description: This skill should be used when the user asks to "define a project", "create a PRD", "start a new product", "run define pipeline", "/ax define", "seed to PRD", or mentions the define stage of IT product creation — the skill runs a 5-stage pipeline (Seed → JTBD → Problem Framing → Scope → PRD) with a PO gate after Problem Framing.
version: 0.1.0
---

# ax-define

IT 제품 제작의 define 단계를 자동화하는 파이프라인. 러프 아이디어 → PRD까지 5단계로 생성.

## 파이프라인

```
러프 아이디어
  → Stage 1: Seed Capture       → seed.md
  → Stage 2: JTBD Discovery     → jtbd.md
  → Stage 3: Problem Framing    → problem-frame.md
  ── PO 게이트 (솔루션 선택 확정) ──
  → Stage 4: Scope Definition   → scope.md
  → Stage 5: PRD Generation     → prd.md
```

Stage 1~3 자동 → PO 확인 → Stage 4~5 자동.

## 각 단계의 산출물

| Stage | 입력 | 출력 | 목적 |
|-------|------|------|------|
| seed-gen | 러프 아이디어 | seed.md | 한줄 아이디어, 사용자, 동기, 도메인, 제약 |
| jtbd-gen | seed.md | jtbd.md | Core Job Statement, Job Map, Competing Solutions, Underserved Needs |
| problem-frame | seed + jtbd | problem-frame.md | HMW, Solution Candidates (Impact×Feasibility), Selected Direction |
| scope-gen | problem-frame.md | scope.md | SLC 체크, v1 스코프, Out of Scope, 핵심 플로우 |
| prd-gen | seed + jtbd + problem-frame + scope | prd.md | Overview, Background, Goals, User Stories, Functional Requirements, Technical Constraints, UI/UX Direction, Out of Scope, Open Questions |

## 사용법

### 전체 파이프라인

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-define/runner.py \
  --idea "독서 기록 앱인데 귀찮지 않았으면 좋겠어" \
  --output-dir ./strategy
```

산출물이 `./strategy/` 아래에 seed.md → prd.md 순으로 생성된다.
Stage 3 후 PO 게이트에서 `problem-frame.md`를 확인하고 `y/n`으로 계속/중단을 결정.

### 게이트 없이 전체 자동

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-define/runner.py \
  --idea "..." \
  --output-dir ./strategy \
  --no-gate
```

### 특정 stage만 실행

```bash
# seed만
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-define/runner.py \
  --stage seed-gen \
  --input idea.md \
  --output strategy/seed.md

# jtbd만 (seed.md를 input으로)
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-define/runner.py \
  --stage jtbd-gen \
  --input strategy/seed.md \
  --output strategy/jtbd.md
```

## 전제 조건

- `claude` CLI 설치 및 인증
- Python 3.10+
- 네트워크 (Claude API 호출)

## 구조

```
skills/ax-define/
├── SKILL.md              ← 이 파일
├── runner.py             ← 파이프라인 실행기
├── _lib/
│   └── claude.py         ← Claude CLI 공통 래퍼
└── stages/
    ├── seed-gen/script.py
    ├── jtbd-gen/script.py
    ├── problem-frame/script.py
    ├── scope-gen/script.py
    └── prd-gen/script.py
```

각 stage의 script.py는:
- stdin으로 입력 받음
- stdout으로 산출물 출력
- stderr로 토큰 메타 (JSON) 출력

## 개선 사이클

이 스킬의 각 script.py는 `moomoo-ax/labs/`에서 auto-research 루프로 개선된 결과물입니다. 품질 문제가 발견되면:

1. `labs/{stage}/`에서 루프 재실행 → script.py 개선
2. `labs/{stage}/best/script.py` → `plugin/skills/ax-define/stages/{stage}/script.py`로 복사
3. `labs/.archive/v{version}/`에 승격 당시 스냅샷 보관

plugin 자체는 순정으로 유지되며, 실험/개선은 moomoo-ax 본체에서만 수행.
