# Track B Model-Routing Rerun — e0f0a5be8b5a

## 결과

세 번째 `Track B` fixture rerun 은 **구조적으로는 성공** 했지만, **latency 는 더 악화** 됐다.

- `run_id`: `e0f0a5be8b5a`
- `product_run_id`: `286e55d4-fb99-494c-813a-c15ddb934326`
- elapsed: `1343.6s` (`22m 24s`)
- cost: `$4.26`
- turns: `115`

`model-selection.json` 은 task 별로 모두 생성됐다. 저위험 task 는 `gpt-5.4-mini`, 공용 component/config 성격 task 는 `gpt-5.3-codex`, `stage-final-review` 는 `gpt-5.4` 로 라우팅되는 것이 확인됐다.

## 라우팅 확인

- `T-001` executor / reviewer
  - `tier=strong`
  - `model=gpt-5.3-codex`
  - 근거: component keyword + `src/components/`
- `T-FIX-T-001-1` executor / reviewer
  - `tier=strong`
  - `model=gpt-5.3-codex`
  - 근거: `src/components/`
- `T-002` executor / reviewer
  - `tier=strong`
  - `model=gpt-5.3-codex`
  - 근거: low-risk summary 였지만 scope 가 `src/components/` 이라 high-risk 승격
- `T-003` executor / reviewer
  - `tier=fast`
  - `model=gpt-5.4-mini`
  - 근거: page keyword + all scope low-risk
- `stage-final-review`
  - `tier=final-review`
  - `model=gpt-5.4`
  - 근거: final review 고정 규칙

## task별 소요

- `T-001`
  - executor `106.1s`
  - reviewer `93.4s`
  - verdict `REQUEST_CHANGES` (blocking 4)
- `T-FIX-T-001-1`
  - executor `46.4s`
  - reviewer `52.9s`
  - verdict `APPROVE`
- `T-002`
  - executor `92.6s`
  - reviewer `64.0s`
  - verdict `APPROVE`
- `T-003`
  - executor `28.9s`
  - reviewer `30.2s`
  - verdict `APPROVE`
- `stage-final-review`
  - reviewer `224.4s`
  - verdict `REQUEST_CHANGES`

Codex worker 호출 합은 약 12분 19초였다. 나머지 약 10분은 conductor 전환, deterministic checks, preflight/test phase 에서 소모됐다.

## 구조 회귀 체크

- fix task 는 `T-FIX-T-001-1` 1개만 발생
- reviewer-only retry 없음
- `stage-final-review` 가 `REQUEST_CHANGES` 를 반환했지만 recursive task 확장은 없었음
- `product_runs` row 는 `done` 으로 정상 종료

즉 `B.5` 에서 제거하려던 구조 회귀는 재발하지 않았다.

## 새로 드러난 blocking 이슈

`stage-final-review` 는 아래 2건을 blocking 으로 보고했다.

- 디자인 토큰이 runtime 에서 실제로 정의되지 않음
- `tsconfig` 가 vitest globals 를 누수시켜 clean typecheck 안전성이 약함

v0.4 fixture pilot 규칙상 이 결과는 **non-recursive audit evidence** 로만 남기고 자동 fix task 는 만들지 않았다.

## 해석

- **좋아진 것**
  - model routing 자체는 의도대로 동작
  - 저위험 page task (`T-003`) 는 실제로 매우 짧아졌다
  - recursive loop / retry 회귀는 계속 억제됨
- **안 좋아진 것**
  - 전체 elapsed 는 `20m 48s` → `22m 24s` 로 더 나빠졌다
  - `T-001` fix cycle 1회와 `stage-final-review` 224초가 전체 시간을 다시 끌어올렸다
  - 속도 개선만으로는 v0.4 목표를 닫기 어렵다는 점이 더 분명해졌다

## 결론

- `Track B` 의 **구조적 green** 은 유지된다
- **model routing = 동작은 하나, latency 해결책으로는 충분하지 않다**
- 다음 단계는 `Track C dogfooding` 으로 진행하되, latency 는 known issue 로 backlog 에서 계속 추적한다
