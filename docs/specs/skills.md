---
last-updated: 2026-04-09
---

# Skills

team-ax 플러그인의 스킬 정의. Composable Stages 패턴으로 전체 루프 또는 개별 단계를 독립 실행.

## Composable Stages 원칙

1. **각 단계 독립 실행** — 전체 루프 외에 define/plan/design/gate/fix/ship/status를 개별 실행 가능
2. **체크포인트 기반 재진입** — 어떤 단계에서 재진입하든 마지막 체크포인트에서 시작
3. **게이트 불변** — 어떤 단계에서 재진입하든 게이트(prepare.py 역할)는 동일하게 적용
4. **바뀌는 건 train.py 쪽뿐** — 디자인/구현 코드만 수정, 평가 기준은 불변

## CLI 진입점

오케스트레이터는 Python CLI. 프로젝트 루트에서 실행.

```bash
python orchestrator.py <command> [options]
```

| 커맨드 | 설명 | Phase |
|--------|------|-------|
| `run` | 전체 루프 (기본) | 0 → 1 → 2 → 3 |
| `define "<러프 입력>"` | Phase 0만 실행 (JTBD/SLC → CPS 생성) | 0 |
| `plan` | Phase 1만 재실행 (CPS 유지, PRD/페르소나/루브릭 재생성) | 1 |
| `design` | 디자인만 재실행 | 2 |
| `design --from-checkpoint` | 마지막 best에서 이어서 디자인 | 2 |
| `gate` | 현재 상태에 게이트만 재적용 | 2 |
| `fix "<피드백>"` | 특정 이슈 타겟 수정 | 2 |
| `ship` | Phase 3만 실행 (문서 갱신 + PR + 배포 준비) | 3 |
| `status` | 체크포인트 + 점수 현황 | — |

## 스킬 노출

프로젝트 터미널에서 slash command로 접근.

```
/ax run          → 전체 루프 (Phase 0→3)
/ax define "..." → CPS 생성
/ax plan         → Phase 1만
/ax design       → 디자인 단계만
/ax fix "..."    → 타겟 수정
/ax gate         → 현재 상태 재평가
/ax ship         → 문서 갱신 + PR + 배포 준비
/ax status       → 체크포인트 + 점수 현황
```

### /ax run

전체 루프. Phase 0(Define) → Phase 1(Plan) → Phase 2(Build) → Phase 3(Ship) 순차 실행.

- **input**: 오너의 러프한 입력 (구두, 메모, 한마디) 또는 기존 체크포인트
- **output**: 게이트 통과한 최종 산출물 + SSOT 문서 갱신 + 실험 로그
- **동작**:
  1. Phase 0: 러프 입력 → JTBD/SLC → CPS → specs/backlog 갱신
  2. Phase 1: CPS → PRD → 페르소나 → 루브릭
  3. Phase 2: ax-loop (워커 → 게이트 → keep/discard → 반복)
  4. Phase 3: changelog + decisions + specs 최신화 + PR 생성
  5. 종료 시 status 출력
- **체크포인트 재진입**: 기존 체크포인트가 있으면 해당 Phase부터 시작 (이전 Phase 스킵)

### /ax define

Phase 0. 오너의 러프한 입력을 구조화된 CPS로 변환.

- **input**: 자연어 문자열 (한마디, 메모, 러프 아이디어)
- **output**: CPS 문서 + specs 업데이트 + backlog 정제 + `define_latest.json`
- **동작**:
  1. 기존 프로젝트 컨텍스트 로드 (specs, ROADMAP, 최근 리포트)
  2. JTBD/SLC 초안 도출
  3. CPS 구조화 (Context-Problem-Solution)
  4. CPS에서 specs 자동 업데이트 + BACKLOG.md 정제
- **용도**: "이런 기능 만들고 싶어" → 구조화된 CPS로 변환
- **오너 터치포인트**: CPS 초안 확인 (선택적). "이거 맞아?" 수준.

### /ax plan

Phase 1만 재실행. CPS는 유지하고 PRD/페르소나/루브릭을 재생성.

- **input**: 기존 CPS (`.harness/checkpoints/`에서 로드)
- **output**: `plan_latest.json` 갱신
- **용도**: "PRD가 잘못됐어" → CPS 유지하면서 하위 산출물만 재생성

### /ax design

디자인 단계만 재실행. exploration rail에서 새 UI 후보 생성.

- **input**: `plan_latest.json` (페르소나 + 루브릭)
- **output**: 디자인 산출물 + `design_best.json` 갱신
- **옵션**:
  - `--from-checkpoint`: 마지막 best 디자인에서 이어서 exploitation
  - (기본): 새로운 exploration (3~5 후보 생성)
- **용도**: "디자인 마음에 안들어" → 새 후보 생성

### /ax gate

현재 코드 상태에 게이트만 재적용. 코드 수정 없음.

- **input**: 현재 워킹 디렉토리 상태
- **output**: 게이트 결과 리포트 (통과/실패 항목 + 점수)
- **용도**: 수동 수정 후 "지금 상태가 괜찮은지" 확인

### /ax fix

자연어 피드백으로 타겟 수정.

- **input**: 자연어 피드백 문자열
- **output**: 수정된 코드 + 게이트 재평가
- **동작**:
  1. 피드백 분석 → 영향 범위 파악
  2. 해당 파일만 워커에게 수정 지시
  3. 게이트 재적용
  4. keep/discard 판정
- **용도**: "이 기능 이렇게 돌면 안돼" → 특정 이슈만 수정

### /ax ship

Phase 3. 산출물 기반으로 SSOT 문서 자동 갱신 + PR 생성.

- **input**: Phase 2 완료 상태 (build_best checkpoint)
- **output**: SSOT 문서 갱신 + PR 생성 + 배포 준비
- **동작**:
  1. git diff 분석 → CHANGELOG.md 항목 자동 생성
  2. keep/discard 로그에서 주요 결정 추출 → decisions.md 갱신
  3. 구현 결과를 docs/specs/*.md에 반영
  4. ROADMAP.md 완료 항목 체크 + BACKLOG.md ready→done 전환
  5. PR 생성 (제목 + 본문 자동)
  6. (설정에 따라) 배포 트리거
- **용도**: ax-loop 완료 후 "마무리 작업" 전체 자동화
- **오너 터치포인트**: PR 확인 + 배포 승인 (자동 배포 설정 시 생략 가능)

### /ax status

현재 체크포인트와 점수 현황 출력.

- **output**:
  - Phase 0 상태 (CPS 존재 여부, specs 갱신 시각)
  - Phase 1 상태 (plan 존재 여부, 페르소나 수, 루브릭 항목 수)
  - Phase 2 상태 (최근 N개 iteration의 verdict + score, best scoring git ref)
  - Phase 3 상태 (문서 갱신 여부, PR 상태)
  - 토큰 사용량 누적 (모델별)

## 시나리오 매핑

| 오너 피드백 | 커맨드 | 동작 |
|------------|--------|------|
| "이런 기능 만들고 싶어" | `/ax define "..."` | 러프 입력 → CPS 구조화 → specs/backlog 갱신 |
| "디자인 마음에 안들어" | `/ax design` | CPS/PRD 유지, exploration rail에서 새 후보 |
| "이 기능 이렇게 돌면 안돼" | `/ax fix "..."` | 영향 범위 분석 → 해당 파일만 수정 → 게이트 |
| "PRD가 잘못됐어" | `/ax plan` | CPS 유지, PRD/페르소나/루브릭 재생성 |
| "전체 다시" | `/ax run` | 전체 루프 (Phase 0→3) |
| "지금 상태 어때?" | `/ax status` | 전 Phase 체크포인트 + 점수 |
| "수동으로 좀 고쳤는데 괜찮아?" | `/ax gate` | 현재 상태 게이트 재적용 |
| "다 됐어, 마무리해" | `/ax ship` | 문서 갱신 + PR + 배포 준비 |

## 체크포인트 시스템

매 단계 완료 시 `.harness/checkpoints/`에 상태 스냅샷 저장.

### 스냅샷 내용

```json
{
  "stage": "design",
  "timestamp": "2026-04-09T14:30:00Z",
  "git_ref": "abc1234",
  "score": 0.87,
  "gate_results": {
    "static": true,
    "visual": true,
    "structural": true,
    "judge": { "score": 0.87, "critical_fail": 0 }
  },
  "iteration": 3,
  "tokens_used": { "claude": 5200, "codex": 8400, "gemini": 2100 }
}
```

### 파일 구조

```
.harness/checkpoints/
├── define_latest.json     ← Phase 0 결과 (CPS + JTBD + SLC)
├── plan_latest.json       ← Phase 1 결과 (PRD + 페르소나 + 루브릭)
├── design_best.json       ← 최고 점수 디자인
├── build_best.json        ← 최고 점수 빌드
├── ship_latest.json       ← Phase 3 결과 (갱신된 문서 목록 + PR URL)
└── history/               ← 전체 이력
    ├── design_001.json
    ├── design_002.json
    └── ...
```

## Exploration / Exploitation Rails

디자인 단계에서 2단계 접근.

### Exploration Rail

- 3~5개 UI 후보를 다양한 레이아웃으로 생성
- 각 후보를 게이트 평가
- best scoring 후보를 선택

### Exploitation Rail

- best 후보를 기반으로 디테일 최적화 루프
- Judge 체크리스트의 실패 항목 중심으로 반복 개선
- `--from-checkpoint` 옵션으로 진입

## 스크립트 목록

| 파일 | 역할 | 의존성 |
|------|------|--------|
| `orchestrator.py` | 루프 제어, CLI 파싱, 체크포인트, 판정 | Python 3.10+ |
| `gate_static.sh` | lint/typecheck/build 게이트 | ESLint, TypeScript, Node.js |
| `gate_visual.py` | Playwright 스크린샷 diff | Playwright, Pillow |
| `gate_judge.py` | 체크리스트 합성 점수 | LLM CLI (Claude) |
| `worker.py` | 멀티모델 워커 호출 래퍼 | Claude CLI, Codex CLI, Gemini CLI |

## 구현 로드맵

| 버전 | 스코프 | 게이트 | 모델 |
|------|--------|--------|------|
| MVP (v0.1) | `run` (Phase 2만) + `status` | ① 정적만 | Claude 단일 |
| v0.2 | + `fix` + `gate` + `ship` | ① + ④ Judge (고정 루브릭) | Claude 단일 |
| v0.3 | + `design` + exploration rail | ① + ② 시각 + ④ | Claude + Gemini |
| v0.4 | + `define` + `plan` + 동적 루브릭 | ① + ② + ③ + ④ | Claude + Codex + Gemini |
| v0.5 | 전체 composable stages (Phase 0→3) | 전체 + 동적 루브릭 | 전체 멀티모델 |
