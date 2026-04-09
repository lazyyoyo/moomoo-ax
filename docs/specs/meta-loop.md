---
last-updated: 2026-04-09
---

# Meta-Loop

AX 시스템 자체를 개선하는 루프. ax-loop가 제품 산출물을 개선한다면, meta-loop는 ax-loop 자체를 개선한다.

## auto-research 매핑

| auto-research 요소 | meta-loop 매핑 | 위치 | 수정 주체 |
|-------------------|---------------|------|----------|
| program.md | 시스템 행동 규칙 | `program.md` | 오너 (시간 두고 개선) |
| train.py | 프롬프트, hooks, eval 설정 | `agents/*.md`, `harness/`, `hooks/` | 스프린트마다 조정 |
| prepare.py | 레벨 1 지표 (eval 함수) | `scripts/metrics.py` | 지표 추가 시만 변경 |
| results.tsv | 스프린트 리포트 | `meta/reports/sprint-N.md` | 자동 생성 |

## 레벨 1 지표 (prepare.py 역할)

ax-loop 실행 결과에서 자동 수집. 시스템이 팀을 돕고 있는지 측정.

| 지표 | 수집 소스 | 목표 |
|------|----------|------|
| 토큰 소비량 (모델별) | .harness/logs/ iteration JSON의 tokens 필드 | ↓ 또는 동일 토큰 대비 품질 ↑ |
| 오너 개입 횟수 | `/ax fix`, `/ax design` 등 수동 커맨드 실행 카운트 | ↓ |
| 자동 재작업 횟수 | .harness/logs/ 의 discard/crash 카운트 | 추이 트래킹 |
| 첫 결과 수용율 | ax-loop 완료 후 오너 수정 요청 없이 ship된 비율 | ↑ |
| 게이트 통과율 (단계별) | 정적/시각/구조/Judge 각각의 첫 시도 통과율 | ↑ |
| 평균 반복 횟수 | ax-loop 종료까지 iteration 수 | ↓ |
| Judge 점수 추이 | best scoring의 점수 이력 | ↑ |

### 지표 수집 자동화

```python
# scripts/metrics.py — .harness/logs/에서 지표 집계
def collect_sprint_metrics(logs_dir, sprint_range):
    """
    스프린트 기간 내 모든 iteration 로그에서 레벨 1 지표 집계.
    출력: sprint-N.md 리포트 + metrics.json (대시보드용)
    """
```

## 조정 대상 (train.py 역할)

meta-loop에서 변경할 수 있는 것들. 각 변경은 before/after 지표로 평가.

### agents/*.md — 워커 프롬프트

| 파일 | 역할 | 조정 시점 |
|------|------|----------|
| designer.md | 디자인 워커 | 디자인 품질 낮을 때 (Judge 점수 ↓, 시각 게이트 실패 ↑) |
| coder.md | 구현 워커 | 정적 게이트 실패 ↑, 재작업 ↑ |
| judge.md | Judge 평가 | 오너 판단과 Judge 판단 불일치 시 |
| planner.md | Phase 0-1 계획 | CPS/PRD 품질 이슈 시 |

조정 방법: 역할 설명 강화, 금지사항 추가, 예시 추가, 컨텍스트 주입 범위 변경.

### harness/ — 평가 인프라

| 리소스 | 조정 시점 |
|--------|----------|
| rubrics/base.yml | 체크리스트 항목 추가/삭제/수정. Judge 판단과 오너 기대 괴리 시 |
| templates/cps.md, prd.md | Phase 0-1 산출물 품질 이슈 시 |
| schemas/*.json | 워커 산출물 형상 부족 시 |
| linters/ | 반복적으로 같은 코드 패턴 실패 시 → 린트 룰 추가 |

### 게이트 설정

| 설정 | 조정 시점 |
|------|----------|
| 스크린샷 diff 임계값 | 시각 게이트가 너무 관대/엄격할 때 |
| Judge 점수 임계값 | 통과 기준이 너무 낮아서 쓰레기가 통과하거나, 너무 높아서 진행 불가 |
| 최대 반복 횟수 | 토큰 예산 대비 반복이 과다/부족할 때 |
| 연속 crash 에스컬레이션 N값 | 구조적 문제 감지 민감도 조정 |

### hooks/

| 조정 시점 |
|----------|
| ax-loop 실행 중 반복되는 환경 문제 (파일 보호, 컨텍스트 주입 등) |

## 스프린트 리포트 (results.tsv 역할)

매 스프린트(또는 N회 ax-loop 실행) 후 자동 생성.

### 리포트 위치

```
moomoo-ax/
├── meta/
│   ├── reports/
│   │   ├── sprint-1.md
│   │   ├── sprint-2.md
│   │   └── ...
│   └── metrics.json    ← 대시보드용 누적 데이터
```

### 리포트 구조

```markdown
# Meta-Loop Sprint N Report

## 기간
- 시작: YYYY-MM-DD
- 종료: YYYY-MM-DD
- ax-loop 실행 횟수: N

## 레벨 1 지표 요약

| 지표 | 이전 스프린트 | 이번 스프린트 | 변화 |
|------|-------------|-------------|------|
| 토큰 소비량 (Claude) | 45,000 | 38,000 | ↓ 15% |
| 토큰 소비량 (Codex) | 12,000 | 14,000 | ↑ 17% |
| 오너 개입 횟수 | 5 | 2 | ↓ 60% |
| 첫 결과 수용율 | 40% | 70% | ↑ 30p |
| 평균 반복 횟수 | 8.2 | 5.1 | ↓ 38% |
| Judge 평균 점수 | 0.72 | 0.81 | ↑ 0.09 |

## 이번 스프린트 변경 사항

| 변경 | 파일 | 이유 |
|------|------|------|
| designer.md에 spacing 규칙 예시 추가 | agents/designer.md | 시각 게이트 실패 40% → spacing 관련 |
| base.yml에 "로딩 스켈레톤 존재" 항목 추가 | harness/rubrics/base.yml | 상태 처리 누락이 오너 개입 원인 |
| 스크린샷 diff 임계값 0.1% → 0.05% | gate_visual.py | 미세한 UI 차이 통과하고 있었음 |

## 판정

| 변경 | 지표 영향 | 판정 |
|------|----------|------|
| designer.md spacing 예시 | 시각 게이트 통과율 60%→85% | ✅ keep |
| base.yml 스켈레톤 항목 | 오너 개입 5→2 | ✅ keep |
| diff 임계값 강화 | 반복 횟수 5.1→7.3 | ⚠️ 모니터링 (반복 늘었지만 품질 ↑) |

## 다음 스프린트 계획

- [ ] coder.md에 import 순서 규칙 강화 (정적 게이트 실패 원인 분석)
- [ ] Judge 점수 임계값 0.85 → 0.80 실험 (반복 횟수 감소 효과 확인)
```

## meta-loop 실행 프로세스

### 트리거

- **정기**: 스프린트 종료 시 (2주 또는 ax-loop N회 실행 후)
- **비정기**: 오너가 반복적으로 같은 이유로 개입할 때 ("또 spacing이야")

### 프로세스

```
① 지표 수집
   scripts/metrics.py → .harness/logs/ 분석 → 스프린트 리포트 초안

② 진단
   - 어떤 지표가 악화/정체?
   - 오너 개입 패턴 분석 (같은 이유 반복?)
   - 게이트별 실패 원인 분류

③ 가설
   - "designer.md에 spacing 예시가 없어서 시각 게이트 실패가 높다"
   - "Judge 임계값이 너무 높아서 불필요한 반복이 발생한다"

④ 변경
   - 조정 대상 파일 수정 (agents/, harness/, gate 설정 등)
   - 변경 사항을 리포트에 기록

⑤ 검증 (다음 스프린트)
   - 동일 조건에서 ax-loop 실행
   - before/after 지표 비교
   - keep / revert 판정

⑥ 기록
   - 리포트 확정 (meta/reports/sprint-N.md)
   - metrics.json 업데이트 (대시보드용)
```

### keep / revert 판정

| 조건 | 판정 |
|------|------|
| 레벨 1 지표 개선 (1개 이상 ↑, 나머지 유지) | keep |
| 레벨 1 지표 악화 (핵심 지표 ↓) | revert |
| 트레이드오프 (일부 ↑ 일부 ↓) | 오너 판단 → 리포트에 근거 기록 |

revert 시: git revert로 변경 전 상태 복원 + 리포트에 revert 사유 기록.

## 관측성 (Observability)

### 문제: 로그가 흩어진다

ax-loop는 각 프로젝트에서 실행된다. 로그도 프로젝트별로 쌓인다:
- `rubato/.harness/logs/` — rubato에서 돌린 ax-loop 로그
- `rofan-world/.harness/logs/` — rofan-world에서 돌린 ax-loop 로그

하지만 meta-loop 개선은 moomoo-ax에서 한다. 이 로그를 취합해야 "어떤 프로젝트에서 어떤 Phase가 문제인지" 진단할 수 있다.

### 로그 취합 구조

```
각 프로젝트 (.harness/logs/)
    ↓ scripts/metrics.py --collect
moomoo-ax/meta/collected/
    ├── rubato/              ← rubato 로그 사본/참조
    ├── rofan-world/         ← rofan-world 로그 사본/참조
    └── ...
    ↓ scripts/metrics.py --aggregate
moomoo-ax/meta/metrics.json  ← 통합 지표 (대시보드용)
```

수집 방식: metrics.py가 각 프로젝트의 `.harness/logs/`를 읽어서 `meta/collected/`에 정규화된 형태로 저장. 원본 로그는 프로젝트에 그대로 유지.

### 멀티유저

두 명(yoyo + 남편)이 각각 ax-loop를 실행할 수 있다. 로그에 유저 식별 필요.

iteration 로그에 추가 필드:
```json
{
  "iteration": 3,
  "user": "yoyo",
  "project": "rubato",
  "timestamp": "2026-04-09T14:30:00Z",
  ...
}
```

리포트에서 유저별 분리 가능:
- 전체 지표 (합산)
- 유저별 지표 (누가 어떤 프로젝트에서 개입이 많은지)
- 프로젝트별 지표 (어떤 프로젝트가 ax-loop가 잘 안 도는지)

### Phase별 진단

"ax-loop가 안 돌아"보다 "Phase N이 병목"을 알아야 개선 가능.

각 Phase는 독립적으로 측정된다:

| Phase | 성공 지표 | 실패 신호 |
|-------|----------|----------|
| Phase 0 (Define) | CPS 검증 체크리스트 통과율 | CPS 불완전 → Phase 1 PRD 품질 ↓ |
| Phase 1 (Plan) | PRD/페르소나/루브릭 검증 통과율 | 루브릭이 부실 → Phase 2 Judge 무의미 |
| Phase 2 Design | 시각 게이트 첫 시도 통과율, Judge 점수 | 디자인 반복 과다 (>N회), 시각 게이트 반복 실패 |
| Phase 2 Code | 정적 게이트 첫 시도 통과율, 빌드 성공률 | lint 반복 실패, 타입에러 반복 |
| Phase 2 Judge | Judge 점수 수렴 속도 | 점수 정체 (개선 안 됨), critical 항목 반복 실패 |
| Phase 3 (Ship) | 문서 갱신 완료율, PR 생성 성공 | 문서 누락, PR 충돌 |

### 진단 흐름

```
문제: "rubato에서 오너 개입이 많다"

① 프로젝트별 분리 → rubato 로그만 추출
② Phase별 분리 → Phase 2 Design에서 반복이 15회 (평균 5회)
③ 게이트별 분리 → 시각 게이트 실패율 70%
④ 실패 원인 분류 → spacing 관련 60%, 색상 관련 40%
⑤ 조정 대상 특정 → designer.md에 spacing 규칙 보강 or rubato/.harness/linters에 spacing 린트 추가
```

### 리포트 뷰

meta-loop 스프린트 리포트에 다음 뷰를 포함:

**1) 전체 요약** — 전 프로젝트/전 유저 합산 레벨 1 지표

**2) 프로젝트별 브레이크다운**
```
| 프로젝트 | ax-loop 실행 | 평균 반복 | 수용율 | 토큰 |
|----------|-------------|----------|--------|------|
| rubato   | 12          | 5.3      | 75%    | 180k |
| rofan    | 4           | 3.1      | 100%   | 45k  |
```

**3) Phase별 병목 분석**
```
| Phase | 첫 시도 통과율 | 평균 재시도 | 주요 실패 원인 |
|-------|-------------|-----------|--------------|
| Define | 90% | 1.1 | CPS Context 누락 |
| Design | 40% | 4.2 | spacing 위반, 상태처리 누락 |
| Code | 85% | 1.3 | 타입에러 |
| Judge | 60% | 2.1 | 접근성 항목 |
```

**4) 유저별 패턴**
```
| 유저 | 개입 횟수 | 주요 개입 이유 | 주로 사용 프로젝트 |
|------|----------|-------------|-----------------|
| yoyo | 3 | "디자인 다시" | rubato |
| 남편 | 1 | "타입에러" | rofan-world |
```

**5) 변경 이력 + 효과**
- 이전 스프린트 변경 → 이번 스프린트 결과 비교

### 공통 하네스 vs 프로젝트 하네스

진단 결과 조정이 필요할 때, **어디를 고칠 것인가**:

| 문제 범위 | 조정 위치 | 예시 |
|----------|----------|------|
| 전 프로젝트 공통 | moomoo-ax/harness/, agents/ | Judge 체크리스트에 "로딩 상태" 항목 추가 |
| 특정 프로젝트만 | {project}/.harness/ | rubato 전용 spacing 린트 룰 추가 |
| 특정 유저 패턴 | agents/*.md 또는 program.md | 특정 워커 프롬프트 보강 |

## Normal Form과의 관계

meta-loop에서 하네스(linters, rubrics, gate 설정)를 변경한 후, 하네스가 충분히 강한지 검증하려면 Normal Form 테스트 실행.

- 동일 CPS로 N번 독립 실행 → 산출물 구조 수렴도 측정
- 수렴도 낮아졌으면 → 하네스 약화. 린트 룰 추가 필요.
- 수렴도 유지/향상이면 → 변경 안전.

## 디렉토리 구조

```
moomoo-ax/
├── meta/
│   ├── reports/           ← 스프린트 리포트
│   │   ├── sprint-1.md
│   │   └── ...
│   ├── collected/         ← 프로젝트별 수집 로그
│   │   ├── rubato/
│   │   ├── rofan-world/
│   │   └── ...
│   └── metrics.json       ← 통합 지표 (대시보드용)
├── scripts/
│   └── metrics.py         ← 지표 수집 + 취합 + 리포트 생성
├── dashboard/             ← 레벨 1 지표 시각화 (metrics.json 읽음)
└── program.md             ← 시스템 행동 규칙 (오너가 개선)
```

## 구현 로드맵

| 버전 | 스코프 |
|------|--------|
| MVP | 수동 리뷰 + 수동 리포트 작성 (Cowork에서) |
| v0.2 | metrics.py 자동 지표 수집 + 리포트 초안 생성 |
| v0.3 | dashboard 시각화 (지표 추이 차트) |
| v0.4 | 자동 진단 (반복 실패 패턴 탐지 → 변경 제안) |
