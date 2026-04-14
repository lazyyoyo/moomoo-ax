# 2026-04-13 — Codex worker smoke 결과

상위 문서:

- `notes/2026-04-13-codex-worker-poc-scope.md`
- `notes/2026-04-13-codex-transition-plan.md`

## 목적

`v0.3.0` baseline 을 건드리지 않는 조건에서, `codex exec --json` 이 one-shot worker 로 충분히 제어 가능한지 확인한다.

실행은 `/tmp/codex-poc/<timestamp>/` 에서만 수행했고, `moomoo-ax` repo 내부 파일은 수정하지 않았다.

## 실행 케이스

| 케이스 | sandbox | 기대 | 결과 | exit code | duration |
|---|---|---|---|---:|---:|
| case1 hello.txt 생성 | `workspace-write` | 파일 생성 | pass | 0 | 15.5s |
| case2 repo 밖 escape 시도 | `workspace-write` | 차단 | pass | 0 | 16.5s |
| case3 seed.txt 관찰 | `read-only` | 읽기만 | pass | 0 | 16.7s |

## 핵심 결과

### 1. `codex exec --json` 출력 형식

- line-delimited JSON 확인
- case1 기준 7줄, invalid 0줄
- 모든 라인 최상위 `type` 필드 존재
- 관찰된 event type:
  - `thread.started`
  - `turn.started`
  - `item.started`
  - `item.completed`
  - `turn.completed`

### 2. 세션 / usage 식별자

- `thread.started.thread_id` 를 세션 식별자로 사용할 수 있음
- `turn.completed.usage` 에서 아래 필드를 읽을 수 있음
  - `input_tokens`
  - `cached_input_tokens`
  - `output_tokens`

즉, 본선 편입 시 usage/cost normalize 계층을 만들 여지가 있다.

### 3. 최종 응답 추출

- `codex exec -o <file>` 로 `last-message.txt` 를 직접 저장 가능
- worker 최종 응답은 event 파서 없이도 안정적으로 확보 가능
- PoC wrapper 는 이 경로를 기본 산출물로 유지하는 게 맞다

### 4. sandbox 차단 판정

- `workspace-write` 는 `--cd` 밖 쓰기를 실제로 차단했다
- `moomoo-ax/CODEX_SMOKE_ESCAPE.md` 는 생성되지 않음
- 다만 **차단 케이스도 exit code 0**

이건 중요하다.

> sandbox 차단 여부는 종료코드가 아니라 `last-message.txt` 와 `events.jsonl` 의 agent message 를 읽어 판정해야 한다.

### 5. repo 청결성

- `moomoo-ax` HEAD 는 `2fb4f8a` 유지
- repo `git status --porcelain` pre/post diff 없음
- worker 가 repo 파일을 수정하지 않았음

## wrapper 관련 후속 반영

### 반영 완료

- macOS bash 3.2 + `set -u` 에서 빈 배열 `ADD_DIRS` 접근 시 unbound variable 이슈
- `[[ ${#ADD_DIRS[@]} -gt 0 ]]` 가드로 보정

### 문서 반영 필요

- timeout 300초는 wrapper 강제가 아니라 호출측 책임으로 둔다
- sandbox 차단 판정은 exit code 가 아니라 `last-message.txt` / event 파싱 기준으로 둔다

## 판정

PoC 는 성공으로 본다.

성공 근거:

- `codex exec --json` 을 one-shot worker 로 사용할 수 있음
- 최종 응답을 별도 파일로 안정적으로 받을 수 있음
- sandbox 가 `--cd` 밖 쓰기를 실제로 차단함
- repo 비접촉 원칙을 유지할 수 있음
- 이벤트 스키마가 충분히 단순해서 후속 normalize 계층 설계가 가능함

## 아직 하지 않은 것

- tmux 세션 호스팅
- multi-worker
- runtime adapter (`src/runtime/`)
- 본선 `src/loop.py`, `scripts/ax_product_run.py`, `plugin/` 편입
- Supabase / dashboard 연동

이 항목들은 다음 단계 spec 에서 따로 판단한다.

## 후속 반영

반영 완료:

1. `BACKLOG.md` inbox 의 Codex 항목을 이 smoke 결과 기준으로 갱신
2. `scripts/poc/summarize_codex_worker.py` 추가
   - `events.jsonl` + `last-message.txt` + `meta.json` 을 읽어
   - `status`, `thread_id`, `usage`, `sandbox_block`, event type 집계를 추출

다음 제안:

1. 실제 smoke 로그 경로에 helper 를 적용해 요약 JSON 형식을 고정
2. 그 다음에야 tmux host layer PoC 를 별도 단계로 시작
