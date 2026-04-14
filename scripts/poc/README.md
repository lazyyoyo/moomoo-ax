# PoC Scripts

이 디렉토리는 `v0.3.0` 본선과 분리된 실험용 스크립트만 둔다.

원칙:

- `src/`, `plugin/`, `scripts/ax_product_run.py` 를 직접 호출하지 않는다.
- 본선 런타임의 source of truth 역할을 하지 않는다.
- 성공 여부와 무관하게 main flow 에 자동 편입되지 않는다.

현재 포함:

- `run_codex_worker.sh`
  - `codex exec --json` one-shot worker 래퍼
  - 입력: `--cd`, `--task-file`, `--log-dir`
  - 출력: `events.jsonl`, `stderr.log`, `last-message.txt`, `meta.json`
- `summarize_codex_worker.py`
  - `events.jsonl` + `last-message.txt` + `meta.json` 요약 helper
  - 출력: `status`, `thread_id`, `usage`, `sandbox_block`, event type 집계
- `start_codex_tmux_worker.sh`
  - detached tmux 세션에서 `run_codex_worker.sh` 를 실행하는 host wrapper
- `tmux_worker_status.sh`
  - session 존재 여부와 pane 상태 확인
- `tmux_worker_capture.sh`
  - 최근 pane 출력 캡처
- `tmux_worker_stop.sh`
  - detached tmux 세션 종료

주의:

- 이 환경 샌드박스에서는 tmux socket 생성이 차단되어 런타임 검증을 여기서 끝내지 못했다
- 실제 tmux 검증은 Claude 쪽 실행 세션에서 해야 한다
