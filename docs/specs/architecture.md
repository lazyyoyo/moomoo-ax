---
last-updated: 2026-04-09
---

# Architecture

team-ax 플러그인의 시스템 아키텍처. Karpathy auto-research 패턴을 제품 개발 파이프라인에 적용한 구조.

## 설계 원칙

1. **오너는 CPS만 던진다** — 페르소나, 평가기준, 구현, 평가, 재작업 전부 시스템이 자율 실행
2. **코드가 강제한다** — 프롬프트가 아니라 Python/Shell 오케스트레이터가 루프/평가/판정을 결정적으로 제어
3. **결과가 나쁘면 프로세스를 고친다** — 개별 산출물 수동 수정이 아니라 eval 로직/페르소나 생성 자체를 개선
4. **eval이 진화한다** — 처음부터 완벽한 평가 불필요. 측정 가능한 것부터 시작, eval 함수 자체를 반복 개선
5. **하네스 = 런타임 강제** — 어떤 모델을 쓰든 멱등한 결과를 보장하는 외부 구조 (린트, 게이트, 스키마)

## auto-research 매핑

### 원본 구조 (Karpathy)

| 요소 | 역할 | 수정 가능 |
|------|------|----------|
| program.md | 에이전트 행동 규칙 | 사람이 시간 두고 개선 |
| train.py | 유일한 수정 대상 (아키텍처, 하이퍼파라미터) | AI가 매 반복 수정 |
| prepare.py | 평가 함수 + 고정 상수 (하네스) | 수정 불가 |
| results.tsv | 실험 로그 | 자동 기록 |

루프: 수정 → git commit → 실행(5분) → 평가 → keep/discard/crash → ∞ 반복 (NEVER STOP)

### AX 시스템 2-Level 매핑

#### meta-loop: AX 시스템 진화 (스프린트 단위)

시스템 자체가 팀을 돕고 있는지 평가. 스프린트 단위로 지표 수집 → 진단 → 변경 → 검증.
상세는 `meta-loop.md` 참조.

| auto-research 요소 | meta-loop 매핑 | 설명 |
|-------------------|---------------|------|
| program.md | program.md, agents/*.md | 오너가 시간 두고 개선 |
| train.py | agents/, harness/, hooks/, gate 설정 | 스프린트마다 조정 |
| prepare.py | 레벨 1 지표 (scripts/metrics.py) | 토큰량, 개입횟수, 수용율, 재작업횟수, 게이트 통과율 |
| results.tsv | 스프린트 리포트 (meta/reports/sprint-N.md) | 변경 사항 + 지표 + keep/revert |

#### ax-loop: 제품 결과물 개선 (자동, 기능 단위)

개별 기능의 산출물 품질을 자동으로 개선. 오케스트레이터가 자율 루프.

| auto-research 요소 | AX 매핑 | 설명 |
|-------------------|---------|------|
| program.md | CPS 스펙 | 오너가 던지는 유일한 입력 |
| train.py | 디자인/구현 코드 | 단계별 수정 범위 고정 |
| prepare.py | 게이트 시스템 | 린트 + 스크린샷 + 체크리스트 (gates.md 참조) |
| results.tsv | .harness/logs/ | keep/discard/crash 이력 |

연결: ax-loop 실행 → 레벨 1 지표 수집 → meta-loop에서 시스템 개선 → 다음 ax-loop가 더 효율적

## 루프 2 내부 구조: Phase 0 → 1 → 2 → 3 (전체 제품 사이클)

team-ax는 define부터 ship까지 전체 사이클을 포함한다. team-product를 대체하는 구조.

### 기존 team-product의 구조적 문제

디자인 단계에서 품질이 낮아 무한 반복 → 컨텍스트 상실 → 후속 단계(implement→qa→deploy) 전부 붕괴 → 문서 최신화 포기. 오너가 수동 개입해야 하는 지점이 너무 많고, 각 단계 사이에 상태가 사라짐.

### Phase 0: Define — "무엇을 만들지"

오너의 러프한 입력을 구조화된 CPS로 변환.

| 항목 | team-product (기존) | team-ax (자동화) |
|------|-------------------|----------------|
| JTBD/SLC 분석 | 오너가 수동 정의 | AI가 기존 데이터(specs, 리포트, 유저 피드백)에서 초안 도출 |
| CPS 작성 | 없음 (구두 합의 → 바로 스펙) | rough input → CPS 자동 구조화 |
| Spec 업데이트 | analyst 에이전트 + 오너 리뷰 | CPS에서 자동 파생, 오너 확인만 |
| Backlog 정제 | /backlog refine (수동 트리거) | CPS 기반 자동 정제 (inbox→ready) |

**오너 터치포인트**: 방향 제시 (러프해도 됨). CPS 초안 확인 (선택적).
**자동 문서 갱신**: `docs/specs/*.md`, `BACKLOG.md`
**체크포인트**: `.harness/checkpoints/define_latest.json`

### Phase 1: Plan — "어떻게 만들지"

CPS를 실행 가능한 계획 + 평가 기준으로 변환.

| 항목 | team-product (기존) | team-ax (자동화) |
|------|-------------------|----------------|
| PRD 작성 | 오너가 수동 | CPS에서 자동 파생 |
| plan.md 작성 | 오너+AI 협업 (수동) | CPS + specs에서 자동 생성 |
| qa-plan.md 작성 | 오너+AI 협업 (수동) | 게이트 정의에서 자동 파생 (별도 문서 불필요 — 루브릭 = QA 계획) |
| 페르소나 정의 | 없음 | CPS 컨텍스트에서 JSON 계약으로 자동 도출 |
| 평가기준 정의 | 사전 정의 체크리스트 | 고정 루브릭(base.yml) + 페르소나×기능별 동적 루브릭 자동 생성 |
| design system 참조 | CLAUDE.md에 텍스트 규칙 | hooks 자동 주입 + ESLint 커스텀 룰로 강제 |

**오너 터치포인트**: PRD/페르소나 확인 (선택적). 대부분 자동.
**자동 문서 갱신**: `ROADMAP.md`, `decisions.md`
**체크포인트**: `.harness/checkpoints/plan_latest.json` (PRD + 페르소나 + 루브릭)

### Phase 2: Build (ax-loop) — "만든다"

오케스트레이터가 자율 반복. 디자인→구현→QA를 하나의 루프로 통합.

| 항목 | team-product (기존) | team-ax (자동화) |
|------|-------------------|----------------|
| 디자인 | 목업→오너 피드백→수정 (수동 루프, max 2회) | exploration rail (3~5 후보) → 게이트 eval → exploitation (자동) |
| design.md 생성 | product-designer 에이전트 (수동 트리거) | 디자인 산출물에서 자동 생성 |
| 디자인 시스템 준수 | 프롬프트 약속 (깨짐) | ESLint 커스텀 룰 + 스크린샷 baseline + 디자인 토큰 강제 |
| 구현 | executor↔reviewer 루프 (수동 트리거) | 워커 자동 호출 + 정적 게이트 자동 검증 |
| QA | qa-plan.md 기반 수동 | 게이트 4계층 자동 (정적→시각→구조→Judge) |
| 디자인 실패 시 | max 2회 후 오너에게 전달 | 자동 재작업 프롬프트 → 루프 계속 (예산 내) |

**ax-loop 내부 흐름**:
```
워커 작업 (design/code) → 게이트 순차 평가 → keep/discard/crash → 로그 → 반복
```

1. **워커 호출** — 멀티모델 워커가 디자인/구현 수행
2. **게이트 순차 적용** — 비용순: 정적 → 시각 → 구조 → Judge (gates.md 참조)
3. **판정** — keep(점수 개선) / discard(점수 동일/하락) / crash(빌드 실패)
4. **재작업** — fail 항목에서 자동 재작업 프롬프트 생성 → 다음 반복
5. **종료 조건** — 전 게이트 통과 + Judge 점수 임계값 초과, 또는 예산 초과 시 best scoring 결과 남기고 종료

**오너 터치포인트**: 없음. 최종 결과만 확인.
**체크포인트**: `.harness/checkpoints/design_best.json`, `build_best.json`

### Phase 3: Ship — "내보내고 기록한다"

산출물 기반으로 SSOT 문서 자동 갱신 + 배포.

| 항목 | team-product (기존) | team-ax (자동화) |
|------|-------------------|----------------|
| changelog | 오너가 수동 작성 | git diff + CPS 요약에서 자동 생성 |
| decisions.md | 오너가 수동 기록 | keep/discard 로그에서 주요 결정 자동 추출 |
| specs 최신화 | 구현 후 수동 반영 (자주 누락) | 구현 결과를 specs에 자동 반영 |
| ROADMAP 갱신 | 수동 | 완료 항목 자동 체크 + 다음 항목 하이라이트 |
| PR 생성 | /sprint done (수동 트리거) | ax-loop 완료 후 자동 |
| 배포 | /product-deploy (수동) | 게이트 전체 통과 시 자동 (설정에 따라) |

**오너 터치포인트**: 최종 결과 확인 + 배포 승인 (선택적 — 자동 배포 설정 가능).
**자동 문서 갱신**: `CHANGELOG.md`, `decisions.md`, `docs/specs/*.md`, `ROADMAP.md`, `BACKLOG.md`

### Phase 간 컨텍스트 보존

기존 team-product의 핵심 문제: 디자인 반복 중 컨텍스트 상실 → 후속 단계 붕괴.

team-ax 해결: **체크포인트 시스템**으로 각 Phase 상태를 `.harness/checkpoints/`에 보존.

```
.harness/checkpoints/
├── define_latest.json    ← Phase 0 (CPS + JTBD + SLC)
├── plan_latest.json      ← Phase 1 (PRD + 페르소나 + 루브릭)
├── design_best.json      ← Phase 2 디자인 best (git ref + score)
├── build_best.json       ← Phase 2 빌드 best (git ref + score)
└── history/              ← 전체 이력
```

디자인에서 100회 반복해도 Phase 0의 CPS, Phase 1의 PRD/페르소나는 체크포인트에 살아있음. 컨텍스트 상실 불가.

### 오너 시간 비교 (기능 1개 기준)

| 단계 | team-product (수동) | team-ax (자동) |
|------|-------------------|---------------|
| Define | ~30분 (JTBD/SLC 정의) | ~5분 (러프 입력만) |
| Plan | ~20분 (plan.md 작성) | ~2분 (확인만, 선택적) |
| Design | ~2시간+ (반복 리뷰) | 0 (자동 루프) |
| Implement | ~30분 (감독) | 0 (자동 루프) |
| QA | ~30분 (qa-plan 실행) | 0 (게이트 자동) |
| Ship | ~20분 (문서 갱신) | 0 (자동 갱신) |
| **합계** | **~4시간+** | **~7분** |

## 코드 vs AI 영역 분리

핵심: 스킬(자연어)은 AI 해석에 의존 → 100% 실행 보장 안 됨. 오케스트레이터를 Python/Shell로 짜면 결정적.

### 코드 영역 (결정적, 스킵 불가)

Python/Shell 스크립트. 루프 제어, eval 실행, keep/discard 판정, git 조작, 토큰 카운팅, 로깅.

- `orchestrator.py` — 루프 제어, 체크포인트 관리
- `gate_static.sh` — lint/typecheck/format 게이트
- `gate_visual.py` — Playwright 스크린샷 diff
- `gate_judge.py` — 체크리스트 합성 점수
- `worker.py` — 멀티모델 워커 호출 래퍼

### AI 영역 (창의적, 비결정적)

headless CLI 호출. 결과물은 JSON 스키마로 형상 강제.

- CPS에서 페르소나 도출
- 동적 루브릭 생성
- 디자인/구현 코드 작성
- Judge 체크리스트 평가
- 재작업 방향 결정

## 멀티모델 워커

| 모델 | 역할 | 호출 패턴 |
|------|------|----------|
| Claude | 설계, 판정, 재작업 프롬프트 생성 | `claude -p "..." --output-format json` |
| Codex | 코드 생성, 패치 | `codex exec --output-schema schema.json` |
| Gemini | UI/비전, 스크린샷 평가, 긴 컨텍스트 | `gemini -p "..." --output-format json` |

워커 호출은 `worker.py`가 래핑. 산출물은 `harness/schemas/`의 JSON 스키마로 형상 검증.

모델 선택 로직:
- Phase 1 (Plan): Claude (설계/구조화에 강점)
- Phase 2 Design: Gemini (비전/UI) → Claude (판정)
- Phase 2 Code: Codex (코드 생성) → Claude (리뷰)
- Gate Judge: Claude (체크리스트 평가)

## 디렉토리 구조

### 엔진 (team-ax 플러그인 — 공통)

```
plugins/team-ax/
├── .claude-plugin/plugin.json
├── skills/
│   └── ax-loop/
│       ├── SKILL.md                    ← 스킬 진입점
│       └── scripts/
│           ├── orchestrator.py         ← 루프 제어, 체크포인트
│           ├── gate_static.sh          ← lint/typecheck 게이트
│           ├── gate_visual.py          ← Playwright 스크린샷 diff
│           ├── gate_judge.py           ← 체크리스트 합성 점수
│           └── worker.py              ← 멀티모델 워커 래퍼
├── harness/
│   ├── rubrics/base.yml               ← 고정 루브릭 (공통)
│   ├── schemas/                       ← JSON 스키마 (워커 산출물 형상)
│   └── linters/                       ← 커스텀 ESLint 룰 (공통)
├── hooks/hooks.json
├── agents/
├── docs/
│   └── specs/                         ← 이 문서들
└── program.md                         ← 시스템 행동 규칙
```

### 프로젝트별 평가 환경 (.harness/)

각 프로젝트(rubato 등) 루트에 배치. 오케스트레이터 실행 시 공통 + 프로젝트별을 merge.

```
{project}/.harness/
├── rubrics/                           ← 도메인 루브릭
├── linters/                           ← 커스텀 ESLint 룰
├── baselines/                         ← Playwright 스크린샷 기준
├── checkpoints/                       ← 상태 스냅샷
│   ├── plan_latest.json              ← Phase 1 결과
│   ├── design_best.json              ← 최고 점수 디자인 (git ref + score)
│   ├── build_best.json               ← 최고 점수 빌드 (git ref + score)
│   └── history/                       ← 전체 이력
└── logs/                              ← 실험 로그 (iteration_N.json)
```

### Merge 규칙

| 리소스 | 공통 (team-ax) | 프로젝트별 (.harness/) | merge 전략 |
|--------|--------------|---------------------|-----------|
| rubrics | base.yml (항상 적용) | 도메인 루브릭 | concat (공통 + 프로젝트) |
| linters | 공통 ESLint 룰 | 프로젝트 커스텀 룰 | extends (프로젝트가 공통 확장) |
| schemas | 워커 산출물 스키마 | — | 공통만 사용 |
| baselines | — | 프로젝트별 스크린샷 | 프로젝트만 사용 |

## 레벨 1 지표 (시스템 자체 평가)

meta-loop의 eval 함수. 상세 지표 목록, 수집 방법, 스프린트 리포트 구조는 `meta-loop.md` 참조.

핵심 지표 요약: 토큰 소비량, 오너 개입 횟수, 첫 결과 수용율, 평균 반복 횟수, 게이트 통과율, Judge 점수 추이.

## Normal Form (멱등성 검증)

하네스의 품질을 검증하는 프레임워크. "하네스가 충분히 강한가?"를 테스트.

**정의**: 동일 CPS 스펙을 N개 독립 AI(또는 같은 AI의 N번 실행)에게 제공 → ESLint harness 적용 후 구조적으로 동일한 형태에 수렴하는지 검증.

**의미**: 수렴하면 하네스가 충분히 강하다 (어떤 모델을 쓰든 멱등). 수렴하지 않으면 하네스에 빈틈이 있다 → 린트 룰/게이트 추가 필요.

**실행 시점**: 루프 1(스프린트 단위)에서 하네스 점검 시. 매 기능 빌드마다 돌리는 것이 아니라, 하네스 설정을 변경한 뒤 검증 용도.

**구현 (향후)**:
1. 동일 CPS로 N번 독립 실행 (서로 다른 세션, 또는 서로 다른 모델)
2. 정적 게이트(①) 적용 후 산출물 구조 비교 (파일 트리, 컴포넌트 구조, import 그래프)
3. 수렴도 측정 → 낮으면 린트 룰 추가 대상 식별

## 기존 hooks 상속

team-ax는 team-product/team-design의 기존 hooks를 상속·확장.

**기존 hooks (team-product)**:
- DB 파괴 방지 (exit code 2)
- .env 파일 접근 차단
- force push 차단
- 자동 포맷/린트 (PostToolUse)
- 컨텍스트 재주입 (컴팩션 이후)

**team-ax 확장**:
- 기존 hooks는 프로젝트 터미널에서 이미 활성화 → team-ax가 중복 정의하지 않음
- team-ax는 ax-loop 실행 중에 추가로 필요한 hooks만 `hooks/hooks.json`에 정의
- 정적 게이트(gate_static.sh)가 기존 lint/format hooks를 포함하므로, ax-loop 안에서는 게이트가 hooks 역할을 대체

## 기존 플러그인과의 관계

| | team-product/team-design | team-ax |
|---|---|---|
| 역할 | 스프린트 기반 개발 파이프라인 | 자율 하네스 엔지니어링 |
| 피드백 루프 | 오너 = 유일한 피드백 루프 | 자동 eval 루프 |
| 실행 | 자연어 스킬 (해석 의존) | Python/Shell (결정적) |
| 공존 | 유지 (기존 워크플로우) | 점진 도입 후 대체 가능 |

team-ax는 기존 team-product/team-design을 건드리지 않고 독립 추가. 기존 hooks/린트 인프라는 team-ax가 확장해서 재활용.
