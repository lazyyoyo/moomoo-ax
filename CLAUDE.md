# moomoo-ax

team-ax 엔진 — auto-research 패턴 기반 자율 제품 개발 파이프라인. team-product를 대체.

## 핵심 개념

- **오너는 CPS만 던진다** — 페르소나, 평가, 구현, 재작업 전부 시스템이 자율 실행
- **코드가 강제한다** — Python/Shell 오케스트레이터가 루프/평가/판정을 결정적으로 제어
- **2-Level 루프** — 루프 1: 시스템 자체 개선 (스프린트 단위, 수동) / 루프 2: 산출물 품질 개선 (기능 단위, 자동)

## 아키텍처

```
moomoo-ax/
├── .claude-plugin/        # 플러그인 정의 + marketplace
├── agents/                # 워커 역할 정의 (designer.md, coder.md, judge.md)
├── skills/ax-loop/        # 스킬 진입점 + 오케스트레이터 스크립트
│   └── scripts/           # orchestrator.py, gate_*.sh/.py, worker.py
├── harness/               # 공통 평가 인프라
│   ├── rubrics/           #   고정 루브릭 (base.yml)
│   ├── schemas/           #   워커 산출물 JSON 스키마
│   ├── templates/         #   CPS/PRD 템플릿 + 검증 체크리스트
│   └── linters/           #   커스텀 ESLint 룰
├── hooks/                 # ax-loop 전용 hooks
├── docs/specs/            # 스펙 (SSOT)
├── dashboard/             # 레벨 1 지표 시각화
└── notes/                 # 설계 논의 기록
```

프로젝트별 평가 환경은 대상 프로젝트 루트의 `.harness/`에 배치. 실행 시 공통(harness/) + 프로젝트별(.harness/) merge.

## 스펙 (SSOT)

| 파일 | 내용 |
|------|------|
| `docs/specs/architecture.md` | 시스템 아키텍처, 2-Level 루프, Phase 0→3, 코드/AI 영역 분리 |
| `docs/specs/skills.md` | CLI 커맨드, composable stages, 체크포인트, 구현 로드맵 |
| `docs/specs/gates.md` | 게이트 4계층 (정적→시각→구조→Judge), 루브릭, keep/discard/crash |

## Phase 흐름

```
Phase 0: Define  — 러프 입력 → CPS 구조화
Phase 1: Plan    — CPS → PRD + 페르소나 + 루브릭
Phase 2: Build   — ax-loop (워커 → 게이트 → keep/discard → 반복)
Phase 3: Ship    — 문서 갱신 + PR + 배포
```

## CLI 커맨드

```
/ax define   — 러프 입력 → CPS 구조화
/ax plan     — CPS → PRD + 페르소나 + 루브릭
/ax design   — 디자인 exploration + 시각 게이트
/ax run      — ax-loop 실행 (워커 → 게이트 → 반복)
/ax fix      — 실패 게이트 기준 재작업
/ax gate     — 게이트만 단독 실행
/ax ship     — 문서 갱신 + PR + 배포
/ax status   — 현재 루프 상태 조회
```

## 게이트 순서 (비용순)

① 정적 (lint/typecheck/build) → ② 시각 (스크린샷 diff) → ③ 구조 (ARIA) → ④ Judge (LLM 체크리스트)

①②③ 이진 판정, ④만 합성 점수. 앞 게이트 통과해야 다음 실행.

## 구현 로드맵

| 버전 | 스코프 | 게이트 | 모델 |
|------|--------|--------|------|
| **MVP (v0.1)** | `run` (Phase 2만) + `status` | ① 정적만 | Claude 단일 |
| v0.2 | + `fix` + `gate` + `ship` | ① + ④ Judge | Claude 단일 |
| v0.3 | + `design` + exploration rail | ① + ② + ④ | Claude + Gemini |
| v0.4 | + `define` + `plan` + 동적 루브릭 | 전체 | 전체 멀티모델 |

## 멀티모델 워커

| 모델 | 역할 | 호출 |
|------|------|------|
| Claude | 설계, 판정, 재작업 프롬프트 | `claude -p "..." --output-format json` |
| Codex | 코드 생성, 패치 | `codex exec --output-schema schema.json` |
| Gemini | UI/비전, 스크린샷 평가 | `gemini -p "..." --output-format json` |

## Gotchas

- 게이트 정의는 루프 2(ax-loop) 안에서 변경 불가 — 변경은 루프 1(스프린트 단위)에서만
- 기존 team-product/team-design hooks는 프로젝트 터미널에서 이미 활성 — team-ax가 중복 정의하지 않음
- 정적 게이트가 기존 lint/format hooks를 포함하므로 ax-loop 안에서는 게이트가 hooks 역할 대체
- Normal Form 검증 (하네스 멱등성 테스트)은 하네스 설정 변경 후에만 실행, 매 빌드마다 X
