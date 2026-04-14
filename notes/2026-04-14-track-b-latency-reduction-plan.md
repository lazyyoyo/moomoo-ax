# Track B Latency Reduction Plan

## 문제 정의

오너가 Codex 편입을 원하는 핵심 이유는 **속도 개선** 이다.

그러나 첫 `Track B` pilot (`69ddd1eb0aa4`) 은:

- 구조는 동작했지만
- 원 3-task fixture 에서 stage-final remediation 까지 확장되며
- 총 약 43분이 소요됐다

이 상태로는 dogfooding 이나 실전 편입이 불가하다.

## 목표

### 관찰 지표

- `static-nextjs-min` fixture 전체 elapsed
- cost / turns
- fix 발생률

### soft target

- 원 계획 3 task 기준 worker 호출 수를 **6회 전후**로 제한
  - 이상적 baseline: executor 3 + reviewer 3
- fix 가 생겨도 추가 호출 수를 최소화
- stage-final-review 가 원 계획을 크게 벗어나는 recursive remediation loop 로 확장되지 않게 제어

## 주요 원인

### 1. reviewer 호출 중복

- `T-FIX-T-001-1` reviewer approve 후 `T-001-retry` reviewer-only 재호출이 발생했다
- 동일 logical issue 에 대해 reviewer 를 2회 이상 태우는 구조는 latency 낭비

### 2. checks 를 worker 가 직접 탐색

- `T-002` executor 는 구현보다 dependency 상태 확인과 `npm install` 시도에 시간을 크게 썼다
- lint/typecheck/test/build 같은 결정론적 검증은 Codex worker 가 아니라 conductor/스크립트가 더 빠르다

### 3. dependency / 환경 복구가 task 안으로 섞임

- worker 가 package 설치/복구까지 맡으면서 구현 경로가 늘어졌다
- 이는 preflight 나 별도 infra step 에서 한 번만 처리해야 한다

### 4. stage-final-review 가 remediation generator 로 작동

- 원 3-task fixture 검증이 `T-004~T-007` 까지 확장되면서 총 wall-clock 이 급증했다
- stage-final-review 는 필요하지만, v0.4 pilot 에서는 범위 제한이 필요하다

## 우선순위

## P0 — rerun 전 필수

### P0.1 fix approve 시 원 태스크 즉시 닫기

- `T-FIX-*` reviewer 가 `APPROVE` 면
  - fix task `[x]`
  - 원 태스크도 바로 `[x]`
- `T-001-retry` 같은 reviewer-only 재호출 금지

기대 효과:

- fix당 reviewer 1회 제거

### P0.2 checks 를 conductor 로 이동

- executor 는 구현과 self-check 메모만 담당
- conductor 가 deterministic script 로:
  - `npm run lint`
  - `npm run typecheck`
  - `npm test`
  - `npm run build`
- reviewer 는 check 결과 파일만 읽는다

기대 효과:

- worker 탐색 시간 감소
- validation 재현성 증가

### P0.3 dependency / 환경 복구를 preflight 로 격리

- `npm install` / missing dependency recovery 는 task loop 밖에서 한 번만 허용
- worker prompt 에는:
  - 설치보다 구현 우선
  - dependency missing 은 infra note 로 남기고 conductor 로 반환

기대 효과:

- executor 가 구현 범위를 벗어나 환경 복구에 시간을 쓰는 문제 감소

### P0.4 task prompt 더 좁히기

- relevant file 수 축소
- executor 는 target file + 직접 필요한 spec만
- reviewer 는 changed_files + check result + 핵심 spec만
- broad repo search 유도 문구 제거

기대 효과:

- cold-start 후 탐색 시간 감소

### P0.5 stage-final-review 범위 제한

- v0.4 pilot 에서는:
  - 원 task acceptance criteria 에 직결되는 이슈만 blocking
  - architecture / polish / optimization 류는 non-blocking 또는 backlog
- stage-final-review 가 `T-004~T-007` 같은 확장 루프를 만들지 않게 가드

기대 효과:

- fixture pilot 을 “원 계획 검증” 범위 안에 묶음

## P1 — P0 후에도 느릴 때

### P1.1 reviewer 빈도 조정

- 모든 task 뒤 reviewer 를 유지할지
- 일부 task 는 stage-final-review 로 흡수할지 비교

### P1.2 risk-based 모델 라우팅

- 저위험 task 는 `gpt-5.4-mini`
- 고위험 구현/리뷰는 `gpt-5.3-codex`
- `stage-final-review` 는 `gpt-5.4`
- 선택 근거를 worker log 에 남겨 rerun 결과와 같이 비교

기대 효과:

- 안전도를 크게 잃지 않고 task-level wall-clock 감소

## v0.4 반영 원칙

- `B.4.1` 은 현재 **partial evidence** 로만 기록
- rerun 은 `P0` 반영 후 1회만 수행
- `Track C dogfooding` 은 구조적 green 과 안전 가드가 준비되면 시작 가능
- latency 는 계속 기록하되, v0.4 에서는 hard gate 가 아니라 최적화 backlog 로 관리

## 성공 판정

다음 rerun 에서 아래를 만족하면 latency pass 로 본다.

1. 중복 reviewer 호출 없음
2. worker 가 `npm install` 같은 환경 복구로 새지 않음
3. stage-final-review 가 recursive fix loop 를 만들지 않음
4. `product_runs` row 가 정상 종료 상태로 마감됨
5. elapsed / cost / turns 가 run note 와 `product_runs` 에 기록됨
