# Codex Worker Contract — v0.4 Track B

## 목적

`team-ax/ax-implement` 의 기존 루프:

`task 선택 → executor 구현 → reviewer 판정 → fix task 삽입`

이 구조는 유지하고, **Claude 는 conductor**, **Codex 는 executor / reviewer worker** 로만 쓴다.
핵심은 모델이 아니라 **결과 계약이 안정적이어야 한다**는 점이다.

## 역할 분리

- **Claude conductor**
  - plan.md 읽기
  - 다음 task 선택
  - worker 입력 파일 생성
  - worker 실행
  - worker 결과 판정
  - deterministic checks 실행 (`checks.json`)
  - `[x]` 체크 또는 fix task 삽입
- **Codex executor worker**
  - 선택된 task 구현
  - 구현 결과 파일 반환
  - 결과 파일 반환
- **Codex reviewer worker**
  - executor 결과 diff / 파일 검토
  - `APPROVE` 또는 `REQUEST_CHANGES`
  - blocking / non-blocking 이슈 반환

## 공통 산출물

worker 1회 실행마다 아래 파일을 남긴다.

- `events.jsonl`
- `stderr.log`
- `last-message.txt`
- `meta.json`
- `result.json`
- `model-selection.json` (skill wrapper 가 선택 근거를 남길 때)

conductor 가 task 단위 검증을 수행할 때는 worker 산출물과 별도로 아래 파일을 남긴다.

- `checks.json`

reviewer 는 가능하면 이 파일을 source of truth 로 사용하고, broad checks 재실행은 피한다.

판정 우선순위:

1. `result.json`
2. `meta.json`
3. `last-message.txt`
4. `events.jsonl`
5. exit code

즉 **exit code 는 최하위 보조 신호**다.

## Executor Result Schema

`result.json`

```json
{
  "role": "executor",
  "status": "ok",
  "summary": "Implemented T-001 and updated tests.",
  "task_id": "T-001",
  "changed_files": [
    "src/components/Button.tsx",
    "src/components/Button.test.tsx"
  ],
  "checks_run": [
    "npm run lint",
    "npm run test"
  ],
  "commit_sha": null,
  "notes": []
}
```

필드 규칙:

- `role`: 항상 `"executor"`
- `status`: `ok | failed | infra_error`
- `summary`: 1~3문장 요약
- `task_id`: Claude 가 넘긴 task id
- `changed_files`: 실제 수정 파일 상대경로
- `checks_run`: worker 가 실행한 검증 명령
- `commit_sha`: v0.4 에선 optional
- `notes`: 자유 메모, optional

status 의미:

- `ok`
  - 구현 완료
  - reviewer 로 넘어갈 수 있음
- `failed`
  - 구현은 했지만 task 요구를 만족 못했거나 checks red
  - Claude 가 fix task 또는 재시도 판단
- `infra_error`
  - sandbox, timeout, wrapper crash, malformed output
  - Claude 가 즉시 중단 또는 fallback

추가 규칙:

- executor 가 `changed_files[]` 를 남길 정도로 구현을 끝냈다면, self-check 환경 문제만으로 `infra_error` 를 쓰지 않는 것이 원칙이다
- 이 경우 worker 는 `status="ok"` + `notes[]` 로 환경 문제를 남기고, conductor checks 를 source of truth 로 사용한다

## Reviewer Result Schema

`result.json`

```json
{
  "role": "reviewer",
  "verdict": "REQUEST_CHANGES",
  "summary": "1 blocking issue found.",
  "task_id": "T-001",
  "blocking_issues": [
    {
      "file": "src/components/Button.tsx",
      "reason": "disabled prop does not prevent click handler"
    }
  ],
  "non_blocking_issues": [
    {
      "file": "src/components/Button.tsx",
      "reason": "token naming mismatch"
    }
  ]
}
```

필드 규칙:

- `role`: 항상 `"reviewer"`
- `verdict`: `APPROVE | REQUEST_CHANGES | ERROR`
- `summary`: 짧은 요약
- `task_id`: executor 와 같은 task id
- `blocking_issues[]`: fix task 생성 기준
- `non_blocking_issues[]`: 기록용, 즉시 차단 아님

verdict 의미:

- `APPROVE`
  - Claude 가 `[ ] → [x]`
- `REQUEST_CHANGES`
  - Claude 가 blocking issues 기준 fix task 삽입
- `ERROR`
  - reviewer 자체 실패
  - Claude 가 fallback 또는 오너 개입 판단

## Normalize 규칙

`result.json` 이 없거나 깨졌을 때만 보조 신호를 쓴다.

### Executor normalize

- `result.json.status=ok` → `ok`
- `result.json.status=failed` → `failed`
- `result.json.status=infra_error` → `infra_error`
- `meta.status=stopped` → `infra_error`
- `sandbox_block=true` → `infra_error`
- `meta` 없음 + partial logs 만 있음 → `infra_error`

### Reviewer normalize

- `result.json.verdict=APPROVE` → `APPROVE`
- `result.json.verdict=REQUEST_CHANGES` → `REQUEST_CHANGES`
- `result.json.verdict=ERROR` → `ERROR`
- `meta.status=stopped` → `ERROR`
- malformed / missing outputs → `ERROR`

## Claude conductor 판정 규칙

### Executor 후

- `ok` → reviewer 호출
- `failed` → fix task 생성 또는 같은 task 재시도
- `infra_error` → 즉시 중단, fallback 또는 오너 개입

recoverable executor infra_error:

- 예외적으로 executor 가 `infra_error` 를 반환했더라도 아래를 모두 만족하면 conductor 가 계속 진행할 수 있다.
  - `changed_files[]` 가 비어 있지 않음
  - `checks.json.status == "pass"`
- 이 경우 conductor 는 해당 run note 에 "recoverable executor infra_error" 를 남기고 reviewer 로 진행한다
- `changed_files[]` 가 비어 있거나 conductor checks 가 red/setup_failure 이면 즉시 중단한다

### Reviewer 후

- `APPROVE` → 해당 task `[x]`
- `REQUEST_CHANGES` → 원 task 아래 fix task 삽입
- `ERROR` → reviewer fallback 또는 오너 개입

fix task 패턴:

- selected task 가 `T-FIX-<orig>-<n>` 이고 reviewer 가 `APPROVE` 면
  - fix task `[x]`
  - 원 태스크 `<orig>` 도 즉시 `[x]`
  - reviewer-only 재검증 task 를 추가하지 않음

## 세션 규칙

- executor / reviewer 는 항상 **fresh session**
- 동일 task 라도 executor 와 reviewer 는 **별도 task file**
- 동일 task 라도 executor 와 reviewer 는 **별도 log dir**
- tmux 를 쓰더라도 판정은 항상 파일 기준

## 모델 라우팅 규칙

- 기본 fast model: `gpt-5.4-mini`
- 기본 strong model: `gpt-5.3-codex`
- 기본 final-review model: `gpt-5.4`
- 환경 변수 override 허용:
  - `AX_CODEX_FAST_MODEL`
  - `AX_CODEX_STRONG_MODEL`
  - `AX_CODEX_FINAL_REVIEW_MODEL`
  - `AX_CODEX_FAST_PROFILE`
  - `AX_CODEX_STRONG_PROFILE`
  - `AX_CODEX_FINAL_REVIEW_PROFILE`

선택 원칙:

- executor
  - 저위험 page/copy/test 성격 task → fast
  - 공용 component/config/schema/auth/package 수준 task → strong
  - risk 가 애매하면 strong
- reviewer
  - `stage-final-review` → 항상 final-review model
  - 공용 component/config/schema/auth/package 수준 task → strong
  - 나머지 task-level review → fast

선택 근거는 skill wrapper 가 `model-selection.json` 으로 남긴다.

## v0.4 범위 밖

- commit 자동화 고도화
- multi-worker 병렬 분할
- qa / design / deploy 까지 Codex 확대
- runtime-neutral harness 재작성

## 한 줄 원칙

> Claude 는 지휘하고, Codex 는 일하고, 판정은 파일 계약으로 한다.
