# 2026-04-13 — Codex tmux host layer PoC

상위 문서:

- `notes/2026-04-13-codex-transition-plan.md`
- `notes/2026-04-13-codex-worker-poc-scope.md`
- `notes/2026-04-13-codex-worker-smoke.md`

## 목적

`codex exec --json` one-shot worker 가 성립한 뒤, **tmux 를 세션 호스팅/관찰 레이어로 얹을 수 있는지**를 별도 PoC 로 확인한다.

이 단계의 목적은 orchestration 이 아니다.

- lead = 여전히 Claude
- worker = 여전히 Codex one-shot
- tmux = 세션 유지, 관찰, 종료, 캡처

즉 tmux 는 lifecycle host 이지 상태 기계가 아니다.

## 범위

### 이번 PoC 에서 하는 것

- `tmux new-session -d` 로 Codex worker 를 백그라운드 실행
- 세션 상태 조회 (`has-session`, `list-panes`)
- pane 캡처 (`capture-pane`)
- 세션 종료 (`kill-session`)
- 로그/결과 파일은 여전히 `run_codex_worker.sh` 가 생성

### 이번 PoC 에서 하지 않는 것

- tmux 안에서 multi-worker orchestration
- Claude 와 tmux 세션 간 실시간 메시지 프로토콜
- task queue / retry loop / auto-resume
- 본선 `src/loop.py`, `scripts/ax_product_run.py`, `plugin/` 편입

## 핵심 원칙

1. **source of truth 는 여전히 파일**
   - `events.jsonl`
   - `stderr.log`
   - `last-message.txt`
   - `meta.json`

2. **tmux pane 은 관찰용**
   - 빠른 상태 확인
   - hung 여부 확인
   - 최근 출력 확인
   - 최종 판정은 파일 기준

3. **socket / session / log dir 는 외부 작업공간에 둔다**
   - 권장: `/tmp/codex-poc/<ts>/tmux/`
   - repo 내부에 tmux 소켓 생성 금지

4. **worker 스크립트는 그대로 재사용**
   - `scripts/poc/run_codex_worker.sh`
   - tmux wrapper 는 그 위에 얇게 얹는 host layer

## 래퍼 인터페이스

### 1. start

`scripts/poc/start_codex_tmux_worker.sh`

필수 인자:

- `--socket <path>`
- `--session <name>`
- `--cd <dir>`
- `--task-file <file>`
- `--log-dir <dir>`

선택:

- `--sandbox`
- `--add-dir`
- `--last-message`

동작:

- `tmux -S <socket> new-session -d -s <session> -c <dir> ...`
- 내부 명령으로 `run_codex_worker.sh` 실행

### 2. status

`scripts/poc/tmux_worker_status.sh`

필수 인자:

- `--socket <path>`
- `--session <name>`

출력:

- session 존재 여부
- pane 수
- `pane_dead`
- `pane_exit_status`
- `pane_current_command`

### 3. capture

`scripts/poc/tmux_worker_capture.sh`

필수 인자:

- `--socket <path>`
- `--session <name>`

선택:

- `--lines <n>` 기본 200

출력:

- 최근 pane 출력 텍스트

### 4. stop

`scripts/poc/tmux_worker_stop.sh`

필수 인자:

- `--socket <path>`
- `--session <name>`

동작:

- `kill-session`
- best-effort 정리

## 세션 규약

- socket: `/tmp/codex-poc/<ts>/tmux/<session>.sock`
- session: `ax-codex-<stage>-<short_id>`
- log dir: `/tmp/codex-poc/<ts>/<case>/logs`

예:

```text
/tmp/codex-poc/20260413T070000Z/
├── case1/
│   ├── task.txt
│   ├── work/
│   └── logs/
└── tmux/
    └── ax-codex-smoke-case1.sock
```

## 성공 판정

아래가 모두 만족되면 tmux host layer PoC 는 성공으로 본다.

- [ ] detached session 이 생성된다
- [ ] `tmux_worker_status.sh` 가 session 존재와 pane 상태를 읽는다
- [ ] `tmux_worker_capture.sh` 가 최근 출력을 읽는다
- [ ] `run_codex_worker.sh` 산출물(`meta.json`, `last-message.txt`)이 정상 생성된다
- [ ] `tmux_worker_stop.sh` 로 세션 종료가 된다

## 알려진 제약

- 현재 Codex 작업 샌드박스에서는 **tmux socket 생성이 차단**되어 여기서 직접 런타임 검증 불가
- 따라서 실제 tmux 검증은 Claude 쪽 실제 실행 세션에서 수행해야 한다
- 이 문서와 `scripts/poc/` 래퍼는 **선행 scaffold** 로만 취급한다

## 다음 단계

1. Claude가 `/tmp/codex-poc/...` 에서 tmux host layer smoke 실행
2. 결과를 `notes/2026-04-13-codex-tmux-smoke.md` 에 기록
3. 성공 시에만 tmux 를 Codex worker host layer 후보로 유지
