# Codex Worker Runtime

v0.4 Track B 에서 사용하는 정식 Codex worker runtime 자산.

현재 포함:

- `run_worker.sh`
  - one-shot Codex worker 실행
  - `events.jsonl`, `stderr.log`, `last-message.txt`, `meta.json`, `result.json` 생성
  - `--model`, `--profile` 로 worker 모델 선택 가능
- `src/codex_worker.py`
  - worker 로그를 executor / reviewer 계약으로 normalize

원칙:

- Claude 는 conductor
- Codex 는 executor / reviewer worker
- 판정은 exit code 단독이 아니라 `result.json` 우선
- skill wrapper 는 risk-based 모델 라우팅을 수행할 수 있음
- tmux 는 선택적 host/debug 레이어

PoC 자산은 여전히 `scripts/poc/` 아래 보존한다.
본 디렉토리는 본선 편입 대상으로 관리한다.
