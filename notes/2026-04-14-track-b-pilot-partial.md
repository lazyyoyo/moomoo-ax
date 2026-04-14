# Track B Pilot Partial — 69ddd1eb0aa4

## 요약

`Track B` 첫 fixture pilot 은 **구조 검증은 PASS**, **green completion 은 미달** 이다.

- `Claude conductor + Codex executor/reviewer` 루프는 실제로 동작했다
- 원 계획 3개 태스크(`T-001~T-003`)와 fix 1개(`T-FIX-T-001-1`)는 모두 APPROVE 까지 도달했다
- 그러나 `stage-final-review` 가 추가 blocking issue 3건을 발견해 `T-004~T-007` 태스크가 재귀적으로 생성됐다
- run 은 **약 43분 시점에 수동 중단**했다
- 결론: **구조는 됐지만 latency / scope expansion 때문에 v0.4 Track B success 로 닫을 수는 없다**

## 실행 식별

- `run_id`: `69ddd1eb0aa4`
- `product_run_id`: `2263a242-4f45-48b6-9222-b0df4b52aac2`
- elapsed: 약 43분
- preserved `run_dir`:
  - `/var/folders/r8/9dwjk1j54qj02rpmls2bvgmh0000gn/T/ax-run-69ddd1eb0aa4`

## 완료된 원 태스크

### `T-001`

- executor: `ok`
- reviewer: `REQUEST_CHANGES`
- blocking:
  - unknown variant runtime fallback 부재
  - lint/typecheck 증빙 부재

### `T-FIX-T-001-1`

- executor: `ok`
- reviewer: `APPROVE`

### `T-001-retry`

- reviewer-only 재검증
- reviewer: `APPROVE`
- 관찰:
  - fix approve 후 원 태스크를 바로 닫지 않고 reviewer 재호출이 발생했다
  - 이 호출은 latency 관점에서 중복이다

### `T-002`

- executor: `ok`
- reviewer: `APPROVE`
- 관찰:
  - executor 가 구현 외에 dependency 상태 확인과 `npm install` 시도까지 수행하며 시간이 크게 늘어졌다

### `T-003`

- executor: `ok`
- reviewer: `APPROVE`

## stage-final-review 결과

verdict: `REQUEST_CHANGES`

blocking issues 3건:

1. 런타임 디자인 토큰 주입 부재
2. clean-state typecheck 재현성 부재 (`.next/types` 의존)
3. invalid variant fallback 회귀 테스트 부재

non-blocking 1건:

- 홈 페이지를 불필요하게 client component 로 승격

## 추가 생성 태스크

stage-final-review 이후 plan 에 아래 태스크가 추가됐다.

- `T-004` 디자인 토큰 런타임 주입
- `T-005` clean-state typecheck 재현성 확보
- `T-006` invalid variant fallback 회귀 테스트
- `T-007` 홈 페이지 server component 복원 (non-blocking)

관찰:

- `T-004~T-006` executor 는 `ok` 까지 생성됨
- `T-007` executor `ok` 직후 reviewer 진입 단계에서 run 을 kill 했다
- 즉 이번 pilot 은 "원 3-task fixture" 검증을 넘어서 **remediation loop** 로 확장됐다

## 산출물 경로

- executor / reviewer 결과:
  - `run_dir/.harness/codex/<task-id>/{executor,reviewer}/logs/result.json`
- stage-final-review 결과:
  - `run_dir/.harness/codex/stage-final-review/reviewer/logs/result.json`
- 갱신된 plan:
  - `run_dir/versions/v0.3-fixture/plan.md`

## product_runs 관찰

kill 이 driver `finally` 전에 들어가서 `product_runs` row 는 `running` 으로 남았다.

- `status=running`
- `finished_at=null`
- `duration_sec=null`
- `cost_usd=0`
- `num_turns=null`
- `session_id=null`

의미:

- 현재 driver 는 SIGTERM 시 finish update 를 보장하지 못한다
- orphan `running` row 를 `cancelled` 또는 `failed` 로 정리하는 recovery 경로가 필요하다

## 결론

이번 pilot 은 아래를 입증했다.

1. Claude conductor 가 Codex executor / reviewer worker 를 실제로 호출할 수 있다
2. `REQUEST_CHANGES → fix task 삽입 → 재검토` 루프가 유지된다
3. 다만 current wiring 으로는 latency 와 stage-final recursive expansion 때문에 운영 경로로는 쓸 수 없다

## 다음

- rerun 금지
- 먼저 latency reduction pass 수행
- 목표:
  - fixture 전체 wall-clock 을 15분 이내로 절감
  - fix approve 후 중복 reviewer 제거
  - checks / dependency recovery 를 Codex worker 바깥으로 이동

