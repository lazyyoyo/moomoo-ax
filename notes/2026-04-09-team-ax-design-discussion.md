# team-ax 설계 논의 정리

**날짜**: 2026-04-09
**참여**: yoyo (오너), Claude (오케스트레이터)

---

## 배경과 동기

남편이 MAO 플러그인의 다음 단계로 '하네스 엔지니어링'을 제안. 핵심 페인포인트는 디자인 완성도가 낮아서 오너가 수동 리뷰에 시간을 과도하게 쓰는 것. Claude Max $220 × 2계정으로도 토큰 부족.

참고 자료:
- 빌더조쉬 유튜브 (하네스 엔지니어링): https://www.youtube.com/watch?v=A8PMyC7W_vg
- auto-research 햄버거 최적화: https://www.youtube.com/watch?v=5-ekc3eXNvs
- Karpathy autoresearch 레포: https://github.com/karpathy/autoresearch
- 딥리서치 1: notes/2026-04-08-deep-research-report.md
- 딥리서치 2: notes/2026-04-08-ai-design-deep-research-report.md
- 영상 메모: ~/hq/vault/하네스 깎기 영상.md

---

## 핵심 개념 정의

### 하네스 엔지니어링
어떤 AI 모델을 쓰든 멱등한(일관된) 결과물을 강제하는 기법. 핵심은 프롬프트가 아니라 **런타임(코드)**으로 강제하는 것.

### auto-research 패턴 (Karpathy)
- prepare.py (수정 불가): 평가 함수 + 고정 상수 = 하네스
- train.py (유일한 수정 대상): 뭐든 바꿔도 됨
- program.md: 에이전트 행동 규칙, 사람이 시간 두고 개선
- 루프: 수정 → 실행(5분) → 평가 → keep/discard → 로그 → ∞ 반복
- NEVER STOP: 사람이 자고 있어도 계속 돌려라

### Normal Form
막연한 요구사항 → N개 AI가 독립적으로 기획/구현 → ESLint harness 적용 후 구조적으로 동일한 형태에 수렴하는지 검증. 하네스의 검증 방법.

---

## 설계 철학

**"오너는 CPS(무엇을 만들지)만 던진다. 나머지는 전부 시스템이 한다."**

- 페르소나 도출 → CPS 컨텍스트에서 자동 생성 (사전 정의 X)
- 평가 기준 생성 → 페르소나 × 기능에서 자동 생성 (사전 정의 X)
- 구현 → 멀티모델 워커 (Claude/Codex/Gemini)
- 평가 → 자동 루프 (게이트 계층)
- 재작업 → 자동 (실패 항목 → 재작업 프롬프트 자동 생성)
- 오너 개입 = 최종 결과물 확인만
- 결과가 쓰레기면 → 프로세스(eval 로직/페르소나 생성)를 개선 (시스템 레벨)

---

## 기존 플러그인과의 차이

### 이미 있는 하네스 (team-product/team-design)
- Hooks (exit code 2 강제 차단): DB 파괴 방지, .env 차단, force push 차단 등
- 자동 포맷/린트 (PostToolUse)
- Backpressure: lint → typecheck → unit → build 통과 전 다음 태스크 불가
- 리뷰 게이트: APPROVE/REQUEST_CHANGES 이진 판정
- 디자인 루프: 최대 2회 반복, 초과 시 오너에게 전달
- 에이전트별 하드 제약: TDD 필수, 텍스트 하드코딩 금지 등

### 새 시스템(team-ax)이 다른 점

|             | 기존                 | team-ax                     |
| ----------- | ------------------ | --------------------------- |
| 피드백 루프      | 오너가 유일한 피드백 루프     | 자동 eval 루프, 오너 개입 없음        |
| 평가 기준       | 사전 정의된 체크리스트       | CPS에서 자동 생성 (동적)            |
| 페르소나        | 없음                 | 기능 컨텍스트에서 자동 도출             |
| 실패 시        | max 2~3회 후 오너에게 전달 | 자동 재작업 프롬프트 → 루프 계속         |
| 모델          | Claude 단일          | Claude + Codex + Gemini     |
| 실행          | 자연어 스킬 (해석에 의존)    | Python/Shell 코드 (결정적)       |
| Input       | 구두 합의 → 바로 스펙      | rough log → CPS → PRD 파이프라인 |
| Lint        | 기본 ESLint/Prettier | 프로젝트 고유 커스텀 룰               |
| Normal Form | 없음                 | 멱등성 검증 프레임워크                |

요약: **기존 = 나쁜 결과를 막는다 (방어적 하네스) / team-ax = 좋은 결과가 나올 때까지 자율적으로 돌린다 (공격적 하네스)**

---

## 2-Level 평가 프레임워크

### 레벨 1: AX 시스템 자체 평가 — "이 시스템이 팀을 돕고 있는가?"
자동 측정 가능한 지표만:
- 토큰 소비량 (모델별: Claude/Codex/Gemini)
- 오너 개입 횟수 ("다시 해" / 되돌리기 횟수)
- eval 루프 내 자동 재작업 횟수
- 첫 결과 수용율 (오너 수정 요청 없이 수용된 비율)

### 레벨 2: 제품 결과물 평가 — "이 결과물이 좋은가?"
처음부터 완벽한 eval 불필요. 측정 가능한 것부터 시작, eval 자체를 진화.
- 1단계: 린트 통과율, 빌드 성공, 스크린샷 diff, 상태 처리 존재 여부
- 2단계: 페르소나 체크리스트, 레퍼런스 비교, 브랜드 토큰 준수율 (결과 보며 추가)

### 2-Level의 auto-research 매핑

**루프 1 (AX 시스템 진화 — 수동, 스프린트 단위)**
- program.md = 스킬/에이전트 정의 (오너가 시간 두고 개선)
- train.py = 프롬프트, hooks, eval 설정 (스프린트마다 조정)
- prepare.py = 레벨 1 지표 (토큰량, 개입 횟수, 수용율)
- results.tsv = 스프린트 리포트

**루프 2 (제품 결과물 개선 — 자동, 기능 단위)**
- program.md = CPS 스펙 (오너가 던지는 유일한 입력)
- train.py = 디자인 코드/구현 코드 (단계별 수정 범위 고정)
- prepare.py = 게이트 시스템 (린트 + Playwright + 체크리스트)
- results.tsv = .harness/logs/ (keep/discard/crash)

연결: 루프 2 실행 → 레벨 1 지표 수집 → 루프 1에서 시스템 개선 → 다음 루프 2가 더 효율적

---

## 루프 2 내부 구조: Phase 1 + Phase 2

### Phase 1: Input → Plan
- 구두 논의 / 메모 / 요구사항
- CPS 작성 (Context - Problem - Solution)
- PRD 작성 (요구사항, 스코프, 완료기준)
- 페르소나 자동 도출 + 동적 평가기준 생성
- 여기까지는 AI 협업이되 오너 확인 가능

### Phase 2: Build (ax-loop)
- orchestrator.py가 돌린다 (오너 개입 없음)
- 워커(Claude/Codex/Gemini)가 작업
- 게이트(린트/스크린샷/체크리스트) 통과 검증
- keep / discard / crash 판정
- 로그 기록
- ∞ 반복 (예산 내)

---

## 코드 vs AI 영역 분리 (핵심 설계)

스킬(자연어)로 정의하면 AI가 해석에 의존 → 100% 실행 안 됨.
오케스트레이터를 Python/Shell로 짜면 루프/평가/판정이 결정적.

| 영역 | 실행 방식 | 예시 |
|------|----------|------|
| 코드 (결정적) | Python/Shell, 스킵 불가 | 루프 제어, eval 실행, keep/discard, git reset, 토큰 카운팅, 로깅 |
| AI (창의적) | headless CLI 호출 | CPS에서 페르소나 도출, 디자인 코드 작성, 리뷰, 재작업 방향 결정 |

---

## 게이트 계층 (비용순)

| # | 게이트 | 유형 | 판정 |
|---|--------|------|------|
| ① | 정적 규칙 (lint, typecheck, format) | 코드 | 통과/실패 (이진) |
| ② | 시각 회귀 (Playwright 스크린샷 diff) | 코드 | 통과/실패 (임계값) |
| ③ | 구조 회귀 (ARIA 스냅샷 비교) | 코드 | 통과/실패 (이진) |
| ④ | Judge 체크리스트 (페르소나 × 기능 Yes/No) | AI+코드 | 합성 점수 |

①②③은 이진, ④만 점수. keep/discard는 ④ 점수가 이전 best 초과 시 keep.

---

## 멀티모델 워커

| 모델 | 역할 | 호출 방식 |
|------|------|----------|
| Claude | 설계, 판정, 재작업 프롬프트 생성 | claude -p → JSON |
| Codex | 코드 생성, 패치 (--output-schema 강제) | codex exec → JSON |
| Gemini | UI/비전, 스크린샷 평가, 긴 컨텍스트 | gemini -p → JSON |

---

## 프로젝트 구조 결정

### MAO 안에 team-ax 플러그인으로
- 기존 team-product/team-design은 건드리지 않고 새 플러그인 추가
- rubato 등 각 프로젝트 터미널에서 team-ax 호출 가능 (기존 플러그인 배포 구조 활용)
- 스킬 안에 Python 스크립트 포함 가능

### 디렉토리 구조

```
my-agent-office/plugins/team-ax/     ← 엔진 (공통)
├── .claude-plugin/plugin.json
├── skills/
│   └── ax-loop/
│       ├── SKILL.md                   ← 스킬 진입점
│       └── scripts/
│           ├── orchestrator.py        ← 루프 제어 (keep/discard/로깅)
│           ├── gate_static.sh         ← 린트/타입체크 게이트
│           ├── gate_visual.py         ← Playwright 스크린샷 diff
│           ├── gate_judge.py          ← 체크리스트 합성 점수
│           └── worker.py              ← 멀티모델 워커 호출 래퍼
├── harness/
│   ├── rubrics/base.yml               ← 고정 루브릭 (공통)
│   ├── schemas/                       ← JSON 스키마 (워커 산출물 형상)
│   └── linters/                       ← 커스텀 ESLint 룰 (공통)
├── hooks/hooks.json
├── agents/                            ← 필요 시 에이전트 정의
└── program.md                         ← 시스템 행동 규칙

rubato/.harness/                       ← 프로젝트별 평가 환경
├── rubrics/                           ← rubato 도메인 루브릭
├── linters/                           ← rubato 커스텀 ESLint 룰
├── baselines/                         ← Playwright 스크린샷 기준
└── logs/                              ← 이 프로젝트의 실험 로그
```

오케스트레이터 실행 시 공통(team-ax/harness/) + 프로젝트별(.harness/)을 merge.

---

## Composable Stages (단계별 독립 실행)

전체 ax-loop를 모놀리스로 돌리는 것이 아니라, 각 단계를 독립 실행 가능하게 구성.
오너가 특정 단계만 재실행하거나, 타겟 수정을 지시할 수 있음.

### CLI 진입점

```
python orchestrator.py run              # 전체 루프 (기본)
python orchestrator.py plan             # Phase 1만 재실행 (CPS 유지, PRD/페르소나/루브릭 재생성)
python orchestrator.py design           # 디자인만 재실행
python orchestrator.py design --from-checkpoint  # 마지막 best에서 이어서
python orchestrator.py gate             # 현재 상태에 게이트만 재적용
python orchestrator.py fix "자연어 피드백"  # 특정 이슈 타겟 수정
python orchestrator.py status           # 체크포인트 + 점수 현황
```

### 체크포인트 시스템

매 단계 완료 시 `.harness/checkpoints/`에 상태 스냅샷 저장:
- git ref (커밋 해시)
- 게이트 결과 (통과/실패 항목)
- 점수 (Judge 체크리스트 합성 점수)

```
.harness/
├── checkpoints/
│   ├── plan_latest.json       # Phase 1 결과 스냅샷
│   ├── design_best.json       # 최고 점수 디자인 (git ref + score)
│   ├── build_best.json        # 최고 점수 빌드 (git ref + score)
│   └── history/               # 전체 이력
```

### 시나리오

| 오너 피드백 | 실행 | 동작 |
|------------|------|------|
| "디자인 마음에 안들어" | `design` | CPS/PRD 유지, exploration rail에서 새 후보 생성 → 게이트 → keep/discard |
| "이 기능 이렇게 돌면 안돼" | `fix "..."` | 영향 범위 분석 → 해당 파일만 수정 → 게이트 재평가 |
| "PRD가 잘못됐어" | `plan` | CPS 유지, PRD/페르소나/루브릭 재생성 → Phase 2로 전진 |
| "전체 다시" | `run` | 전체 루프 |

### auto-research 정합성

어떤 단계에서 재진입하든 **게이트(prepare.py 역할)는 동일**하게 적용.
바뀌는 건 train.py(디자인/구현 코드) 쪽뿐. 평가 기준 불변 원칙 유지.

### 스킬 노출 (예정)

```
/ax run          → 전체 루프 (Phase 0→3)
/ax define "..." → CPS 생성 (Phase 0)
/ax plan         → Phase 1만
/ax design       → 디자인 단계만
/ax fix "..."    → 타겟 수정
/ax gate         → 현재 상태 재평가
/ax ship         → 문서 갱신 + PR + 배포 준비
/ax status       → 체크포인트 + 점수 현황
```

---

## 전체 사이클 결정 (2026-04-09 추가)

team-ax는 team-product를 수정하지 않고 점진적으로 대체한다. define→ship 전체 사이클을 자체 포함.

**배경**: team-product의 구조적 문제 — 디자인 무한반복 → 컨텍스트 상실 → 후속 단계(implement→qa→deploy) 전부 붕괴 → 문서 최신화 안 됨.

**Phase 구조**:
- Phase 0 (Define): 러프 입력 → JTBD/SLC → CPS → specs/backlog 갱신
- Phase 1 (Plan): CPS → PRD → 페르소나 → 루브릭 → plan 자동 생성
- Phase 2 (Build): ax-loop (design→implement→qa 자동 반복)
- Phase 3 (Ship): changelog + decisions + specs 자동 최신화 + PR

**핵심 차이**: team-product에서 수동이었던 define/design/qa/ship 모두 자동화 대상. 오너는 Phase 0에서 러프 입력 + 최종 확인만.

상세는 `plugins/team-ax/docs/specs/` 참조.

---

## 다음 스텝

1. ~~team-ax 스펙 초안 작성 (docs/specs/)~~ ✅
2. orchestrator.py MVP (단일 모델 + 정적 게이트만) → **Claude Code에서 진행**
3. rubato에 .harness/ 초기 셋업
4. 멀티모델 워커 추가
5. Judge 게이트 + 페르소나 자동 도출 추가
6. Phase 0 (define) + Phase 3 (ship) 구현
