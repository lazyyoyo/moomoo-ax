---
last-updated: 2026-04-09
---

# Gates

team-ax 게이트 시스템. 비용순 계층 구조로 배치, 저비용 게이트부터 순차 실행.

## 설계 원칙

1. **저비용 먼저** — 비싼 판단은 마지막에. 값싼 신호로 먼저 걸러낸다
2. **①②③은 이진, ④만 점수** — 정적/시각/구조 게이트는 통과/실패, Judge만 합성 점수 산출
3. **게이트 = prepare.py** — auto-research에서 prepare.py가 수정 불가인 것처럼, 게이트 정의는 루프 안에서 변하지 않는다. 변경은 meta-loop(버전 단위)에서만
4. **실패 시 재작업 자동화** — 어떤 항목이 왜 실패했는지를 재작업 프롬프트로 변환

## 게이트 계층

### ① 정적 게이트 (gate_static.sh)

**유형**: 코드 (결정적)
**판정**: 통과/실패 (이진)
**비용**: 최저 (로컬 실행, 수초)

실행 항목:
- ESLint (공통 룰 + 프로젝트 커스텀 룰)
- TypeScript 타입체크 (`tsc --noEmit`)
- Prettier 포맷 검증
- 커스텀 린트 룰 (파일명 컨벤션, import 순서, 디자인 토큰 직접값 금지 등)
- 빌드 성공 여부 (`npm run build`)

실패 시: 에러 메시지를 재작업 프롬프트에 포함 → 워커가 자동 수정 → 재실행

```bash
# gate_static.sh 실행 흐름
eslint --format json src/ > /tmp/lint-result.json
tsc --noEmit 2> /tmp/type-result.txt
npm run build 2> /tmp/build-result.txt

# 결과: exit 0 (통과) 또는 exit 1 (실패 + 에러 JSON)
```

### ② 시각 게이트 (gate_visual.py)

**유형**: 코드 (결정적)
**판정**: 통과/실패 (임계값 기반 이진)
**비용**: 중 (Playwright 브라우저 실행)
**전제**: ① 통과 후에만 실행

실행 항목:
- Playwright 스크린샷 촬영 (주요 화면/컴포넌트)
- baseline 이미지와 픽셀 diff 비교
- diff 비율이 임계값 초과 시 실패

```python
# gate_visual.py 핵심 로직
for route in target_routes:
    screenshot = capture(route)
    baseline = load_baseline(route)
    diff_ratio = pixel_diff(screenshot, baseline)
    if diff_ratio > THRESHOLD:  # 예: 0.1%
        fail(route, diff_ratio, screenshot)
```

baseline 관리:
- 최초 실행 시 자동 생성 → `.harness/baselines/`에 저장
- 의도적 UI 변경 시 baseline 갱신 (오케스트레이터가 keep 판정 후 자동)
- 경로별 스크린샷: `baselines/{route-slug}.png`

### ③ 구조 게이트 (ARIA 스냅샷)

**유형**: 코드 (결정적)
**판정**: 통과/실패 (이진)
**비용**: 중 (Playwright + ARIA 트리 추출)
**전제**: ② 통과 후에만 실행

실행 항목:
- Playwright로 접근성 트리(ARIA) 스냅샷 추출 (YAML)
- baseline ARIA 스냅샷과 구조 비교
- 역할(role), 라벨(label), 계층 변경 감지

시각 게이트와의 차이: 시각 = 픽셀 레벨, 구조 = 시맨틱 레벨. 시각적으로 동일해도 구조가 달라지면 접근성 회귀.

### ④ Judge 게이트 (gate_judge.py)

**유형**: AI + 코드
**판정**: 합성 점수 (0~1)
**비용**: 최고 (LLM 호출)
**전제**: ①②③ 전부 통과 후에만 실행

실행 항목:
- 체크리스트 로드 (고정 루브릭 + 동적 루브릭)
- 각 항목에 대해 LLM Judge가 Yes/No 판정
- 합성 점수 = Yes 비율 (0~1)

```python
# gate_judge.py 핵심 로직
rubric = merge(base_rubric, dynamic_rubric)  # 고정 + 동적
results = []
for item in rubric.items:
    verdict = llm_judge(item, context)  # Yes/No + 근거
    results.append(verdict)

score = sum(r.yes for r in results) / len(results)
# critical 항목이 하나라도 No이면 점수와 무관하게 실패
if any(r.no and r.critical for r in results):
    return FAIL
```

## 루브릭 구조

### 고정 루브릭 (harness/rubrics/base.yml)

모든 프로젝트, 모든 기능에 항상 적용. 변경은 meta-loop(버전 단위)에서만.

카테고리:
- **레이아웃**: spacing 스케일 준수, 반응형 브레이크포인트
- **타이포**: 계층 유지, 폰트 크기/무게 토큰 사용
- **색상**: 대비 비율, 디자인 토큰 준수, 다크/라이트 모드
- **컴포넌트**: shadcn/ui 우선 사용, 일관된 패턴
- **접근성**: ARIA 역할/라벨, 키보드 네비게이션, 포커스 관리
- **상태 처리**: loading/empty/error 상태 존재 여부
- **인터랙션**: 호버/포커스/액티브 피드백, 트랜지션

### 동적 루브릭 (Phase 1에서 자동 생성)

기능 컨텍스트(CPS + 페르소나)에서 LLM이 생성. Yes/No로 답할 수 있는 형태 필수.

생성 입력: 페르소나 JSON + critical journeys + 화면 목록
생성 제약: 각 항목은 `{ question: string, critical: boolean }` 형태

예시 (독서 기록 기능):
```yaml
- question: "2탭 이내에 독서 기록 입력 화면에 도달할 수 있는가?"
  critical: true
- question: "저장 실패 시 입력 데이터가 보존되는가?"
  critical: true
- question: "오프라인 상태에서 적절한 피드백이 표시되는가?"
  critical: false
- question: "최근 기록이 시간순으로 정렬되어 보이는가?"
  critical: false
```

## keep / discard / crash 판정

auto-research 원본의 판정 로직을 그대로 적용.

| 판정 | 조건 | 동작 |
|------|------|------|
| **keep** | ④ 점수 > 이전 best 점수 | git commit, 브랜치 전진, best 갱신 |
| **discard** | ④ 점수 ≤ 이전 best 점수 | git reset, 이전 best로 복원 |
| **crash** | ①②③ 실패 또는 빌드 에러 | git reset, 에러 로그 기록, 다음 반복 |

## 종료 조건

1. **성공**: 전 게이트 통과 + Judge 점수 ≥ 임계값 (예: 0.85)
2. **예산 초과**: 반복 횟수 상한 도달 또는 토큰 예산 초과 → best scoring 결과 남기고 종료
3. **연속 crash**: N회 연속 crash 시 구조적 문제로 판단 → 오너에게 에스컬레이션

## 로그 형식

`.harness/logs/iteration_{N}.json`:

```json
{
  "iteration": 3,
  "timestamp": "2026-04-09T14:30:00Z",
  "worker": "codex",
  "git_ref": "abc1234",
  "gates": {
    "static": { "pass": true, "duration_ms": 3200 },
    "visual": { "pass": true, "diff_max": 0.02, "duration_ms": 8500 },
    "structural": { "pass": true, "duration_ms": 6100 },
    "judge": { "pass": true, "score": 0.87, "items": 12, "yes": 10, "no": 2, "critical_fail": 0 }
  },
  "verdict": "keep",
  "tokens": { "claude": 1200, "codex": 3400, "gemini": 0 },
  "rework_prompt": null
}
```

## 페르소나 JSON 계약

Phase 1에서 CPS 컨텍스트로부터 자동 도출. 사전 정의 X.

```json
{
  "feature": "<feature-name>",
  "personas": [
    {
      "id": "p1",
      "name": "<이름>",
      "goals": ["<목표1>", "<목표2>"],
      "constraints": ["<제약1>", "<제약2>"],
      "success_signals": ["<성공 신호1>", "<성공 신호2>"]
    }
  ],
  "critical_journeys": [
    {
      "id": "j1",
      "persona_id": "p1",
      "steps": ["<step1>", "<step2>", "..."],
      "edge_cases": ["<edge1>", "<edge2>"]
    }
  ]
}
```

## 게이트 진화 로드맵

eval 자체가 진화하는 것이 시스템의 핵심.

| 단계 | 게이트 구성 | 트리거 |
|------|-----------|--------|
| MVP | ① 정적 게이트만 | 첫 구현 |
| v0.2 | ① + ④ Judge (고정 루브릭만) | 정적 게이트 안정화 후 |
| v0.3 | ① + ② 시각 + ④ | Playwright 인프라 구축 후 |
| v0.4 | ① + ② + ③ 구조 + ④ | ARIA 스냅샷 baseline 축적 후 |
| v0.5 | 전체 + 동적 루브릭 | 페르소나 자동 도출 검증 후 |
