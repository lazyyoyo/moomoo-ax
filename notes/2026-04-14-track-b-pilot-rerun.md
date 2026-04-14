# Track B Pilot Rerun — 6593deebdf82

## 결과

두 번째 `Track B` fixture pilot 은 **green** 이다.

- `run_id`: `6593deebdf82`
- `product_run_id`: `9716ab8a-cae4-4433-a101-dd9d674a1343`
- elapsed: `1248.4s` (`20m 48s`)
- cost: `$4.46`

첫 pilot 대비 개선:

- reviewer-only retry 없음
- worker 환경 복구 누수 없음
- stage-final recursive task expansion 없음
- `product_runs` row 정상 종료

즉 **구조적으로는 v0.4 Track B fixture green** 이 달성되었다.

## task별 소요

- `T-001`
  - executor 약 `2:47`
  - checks 약 `0:19`
  - reviewer 약 `1:45`
- `T-002`
  - executor 약 `2:30`
  - checks 약 `0:24`
  - reviewer 약 `1:00`
- `T-003`
  - executor 약 `1:58`
  - checks 약 `0:30`
  - reviewer 약 `1:30`
- `stage-final-review`
  - reviewer 약 `3:15`

합산 기준으로는 약 16분, 나머지 4~5분은 preflight / test phase / dev server 쪽에서 소비됐다.

## 기대 회귀 항목

### 1. reviewer-only retry

재발 없음.

- reviewer 호출은 `T-001`, `T-002`, `T-003`, `stage-final-review` 총 4회
- `T-001-retry` 같은 reviewer-only 재검증 없음

### 2. worker 환경 복구 누수

재발 없음.

- `npm install` 계열은 conductor preflight 에서만 수행
- worker 가 lockfile/설치 복구로 새지 않았다

### 3. stage-final recursive loop

재발 없음.

- `stage-final-review` verdict 는 `APPROVE`
- `T-004~T-007` 같은 추가 task 생성 없음

## checks.json

task별 `checks.json` 생성 확인:

- `T-001`: `lint`, `typecheck`
- `T-002`: `lint`, `typecheck`, `test`
- `T-003`: `lint`, `typecheck`, `build`

즉 conductor 가 변경 범위에 맞춰 deterministic checks 를 선택했다.

## product_runs

`product_runs` row 는 정상 종료됐다.

- `status=done`
- `duration_sec=1248.4`
- `cost_usd=4.46`
- `num_turns=112`
- `session_id` 기록됨

## 잔존 이슈

### 1. hard target 미달

- 목표: fixture 15분 이내
- 실측: 20분 48초

주요 잉여:

- stage-final-review 약 3분 15초
- test phase (`run_checks.sh` + dev_server) 약 3분
- preflight 중 Codex CLI 확인 및 dependency 보정 약 1~2분

### 2. recoverable executor infra_error

`T-002` executor 는 아래 이유로 `status="infra_error"` 를 반환했다.

- targeted self-check 시 `@testing-library/dom` 누락

그러나:

- `changed_files[]` 는 존재했고
- conductor `checks.json` 은 `pass`
- reviewer 도 `APPROVE`

따라서 이번 rerun 에서는 이 케이스를 **recoverable executor infra_error** 로 본다.
향후 계약은:

- hard infra_error: 즉시 중단
- changed_files + conductor checks pass: reviewer 로 계속 진행 가능

## 결론

- `B.4.1 fixture green`: 달성
- `B.4.2 failure branch 실증`: 첫 pilot (`69ddd1eb0aa4`) 로 이미 확보
- `B.5 latency reduction pass`: 부분 성공
  - 구조 회귀 제거는 성공
  - 15분 hard target 은 아직 미달

다음 단계는 `Track C` 직행이 아니라, **latency round 2** 여부를 먼저 판단하는 것이다.
