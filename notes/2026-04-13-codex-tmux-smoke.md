# 2026-04-13 — Codex tmux host layer smoke 결과

상위 문서:

- `notes/2026-04-13-codex-tmux-host-poc.md`
- `notes/2026-04-13-codex-worker-poc-scope.md`
- `notes/2026-04-13-codex-worker-smoke.md`

## 목적

`codex exec --json` one-shot worker 위에 tmux 를 세션 호스팅/관찰 레이어로 얹었을 때,

- detached lifecycle
- 상태 조회
- 강제 stop
- 파일 기반 post-mortem

이 성립하는지 본다.

## 실행 결과 요약

작업 공간:

- root: `/tmp/codex-poc/20260413T131709Z/`
- socket: `/tmp/codex-poc/20260413T131709Z/tmux/ax-codex-smoke.sock`

케이스:

| 케이스 | session | 결과 |
|---|---|---|
| case1 짧은 hello | `ax-codex-smoke-case1` | 자연 종료 성공 |
| case2 의도적 중단 | `ax-codex-smoke-case2` | `stop` 으로 강제 종료 성공 |

## 관찰

### 1. detached host 자체는 동작

- `tmux new-session -d` 로 worker session 생성 가능
- 시작 직후 `session_exists=true` 확인 가능
- 강제 stop 후 `session_exists=false` 즉시 확인 가능

즉 **host lifecycle 자체는 성립**한다.

### 2. `status` 의 pane 필드는 실효성이 낮음

관찰된 한계:

- `pane_dead`
- `pane_exit_status`

는 현재 wrapper 설계에선 거의 의미가 없다.

이유:

- 자연 종료 시 세션이 바로 teardown 되어 조회 시점엔 이미 `session_exists=false`
- 강제 stop 도 동일

따라서 현재 유효한 status 신호는 사실상:

- `session_exists=true/false`

하나뿐이다.

### 3. `capture` 는 현재 설계에선 빈 출력

원인:

- `run_codex_worker.sh` 가 stdout/stderr 를 로그 파일로 직접 리다이렉트한다
- pane 에는 실시간 출력이 거의 남지 않는다

결론:

> tmux capture 는 운영상 핵심 채널이 아니고, 실제 관찰은 `events.jsonl` tail 이 더 유효하다.

### 4. clean exit 와 stopped exit 의 파일 차이

#### clean exit

- `meta.json`
- `events.jsonl`
- `last-message.txt`
- `stderr.log`

모두 생성됨.

#### stopped exit

기존 관찰:

- `events.jsonl` 일부만 남음
- `meta.json` / `last-message.txt` 부재 가능
- summarize helper 가 `meta.json` 부재로 죽음

후속 보정:

- `tmux_worker_stop.sh --log-dir ...` 가 `meta.json` 부재 시
  - `status="stopped"`
  - `partial=true`
  - `stopped_at_utc`
  - `socket`
  - `session`
  를 기록하도록 보강
- `summarize_codex_worker.py` 는 `meta.json` 부재 시
  - `status="incomplete"`
  - `partial=true`
  로 graceful degrade 하도록 보강

## 결론

tmux host layer PoC 는 **조건부 성공**으로 본다.

성공:

- detached start / stop lifecycle 은 성립
- file-based post-mortem 모델과 결합 가능

한계:

- `status` 의 pane exit 필드는 현 설계상 약함
- `capture` 는 실용성이 낮음

따라서 현재 결론은:

> tmux 는 "관찰의 중심" 이 아니라 "세션 수명 관리용 host" 로 쓰는 것이 맞다.

lead 가 의존해야 하는 주요 채널은 여전히 파일이다.

- `events.jsonl`
- `meta.json`
- `last-message.txt`

## 다음 단계 제안

1. `tmux_worker_status.sh` 의 pane 필드를 단순화할지 결정
2. `capture` 를 유지하되 "debug only" 로 격하
3. 본선 편입 전, reviewer 후보 one-shot worker 에 한정한 시뮬레이션 PoC 검토
