# moomoo-ax

자기 하네스를 진화시켜 IT 제품 제작을 자동화하는 시스템.

## 한 줄 미션

> **오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인.**

배포 제품은 `team-ax` 이고, 이 저장소는 그 제품을 만드는 **levelup loop** 와 그 공장을 관찰하고 진화시키는 **meta loop** 까지 포함한 전체 시스템이다. 프로젝트 정의의 SSOT 는 [PROJECT_BRIEF.md](./PROJECT_BRIEF.md) 다.

## 현재 상태

- 현재 기준 방향은 **product → meta → levelup** 순서다.
- v0.3 범위는 **`ax-implement` 1개 stage 를 실제 product loop 로 완성**하는 데 집중한다.
- 기존 levelup harness (`src/loop.py`), 피드백/개입 수집 (`scripts/ax_feedback.py`, `scripts/ax_post_commit.py`), 대시보드 (`dashboard/`) 는 이미 존재한다.
- `README.md` 는 개요용이다. 실제 작업 시작 전에는 아래 문서를 이 순서로 보는 게 맞다.

## 먼저 읽을 문서

1. [PROJECT_BRIEF.md](./PROJECT_BRIEF.md) — 프로젝트 정의 SSOT
2. [CLAUDE.md](./CLAUDE.md) — 실행 규칙, 구조 요약, gotchas
3. [HANDOFF.md](./HANDOFF.md) — 현재 세션 기준 진행 상태와 다음 작업
4. [versions/v0.3/plan.md](./versions/v0.3/plan.md) — 현재 작업 계획

## 3 레이어

| 레이어 | 역할 | 현재 코드 기준 구현물 |
|---|---|---|
| `product loop` | 외부 프로젝트에서 실제 제품을 만드는 루프 | `plugin/` 의 `team-ax`, `scripts/ax_product_run.py` |
| `levelup loop` | `team-ax` 자체를 실험하고 개선하는 내부 공장 | `src/loop.py`, `src/judge.py`, `labs/` |
| `meta loop` | 관측, 판단, 피드백 수집, 버전 결정 | `dashboard/`, `scripts/ax_feedback.py`, `scripts/ax_post_commit.py`, `src/db.py` |

북극성 지표는 **오너 개입 횟수 감소**다.

## 레포 구조

```text
moomoo-ax/
├── PROJECT_BRIEF.md      # 프로젝트 정의 SSOT
├── CLAUDE.md             # 실행 규칙 / 구조 요약
├── HANDOFF.md            # 현재 진행 상태
├── README.md             # 이 문서
│
├── src/                  # levelup loop 엔진
│   ├── loop.py
│   ├── judge.py
│   ├── claude.py
│   └── db.py
│
├── labs/                 # stage별 실험장
│   └── ax-implement/
│
├── plugin/               # 배포 제품 team-ax (Claude Code plugin)
│   ├── .claude-plugin/
│   ├── agents/
│   └── skills/
│
├── scripts/              # 운영 스크립트
├── dashboard/            # meta loop UI (Next.js)
├── dogfooding/           # product loop 자기 적용 결과
├── versions/             # 버전별 계획 / 회고
└── notes/                # 설계 메모 / 조사 기록
```

## 주요 진입점

### 1. 테스트

```bash
.venv/bin/python -m pytest tests/ -q
```

현재 테스트 스위트는 `87 passed` 가 기준이다.

### 2. levelup loop 실행

`labs/{stage}/script.py` 를 rubric 기반으로 반복 개선한다.

```bash
.venv/bin/python src/loop.py ax-implement \
  --user yoyo \
  --fixture haru:7475bef \
  --input labs/ax-implement/input/haru-7475bef \
  --max-iter 3 \
  --threshold 0.95
```

### 3. product loop smoke 실행

현재 v0.3 에서는 `src/loop.py` 를 거치지 않는 별도 드라이버로 `team-ax` 를 worktree 에서 실행한다.

```bash
.venv/bin/python scripts/ax_product_run.py \
  --fixture labs/ax-implement/input/static-nextjs-min \
  --plugin-dir plugin
```

이 경로는 `team-ax/ax-implement` 1개 stage 를 product loop 관점에서 점검하는 용도다.

### 4. 피드백 기록

```bash
.venv/bin/python scripts/ax_feedback.py \
  --priority high \
  --stage ax-implement \
  "타입 오류가 반복 생성됨"
```

### 5. 대시보드 실행

```bash
cd dashboard
npm install
npm run dev
```

## 현재 코드베이스에서 중요한 점

- `PROJECT_BRIEF.md` 와 `dogfooding/` 는 다르다. 전자는 정의, 후자는 실험 결과다.
- `plugin/` 은 아직 **Claude Code 플러그인** 기준으로 구성되어 있다.
- `src/claude.py` 와 `scripts/ax_product_run.py` 가 현재 product/levelup 실행의 핵심 런타임 결합 지점이다.
- Codex 전환 검토 메모는 [notes/2026-04-13-codex-transition-plan.md](./notes/2026-04-13-codex-transition-plan.md)에 정리했다.

## 라이선스

MIT
