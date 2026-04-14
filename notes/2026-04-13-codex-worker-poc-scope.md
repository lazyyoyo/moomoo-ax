# 2026-04-13 — Codex worker PoC 운영 규약

## 이 문서의 위치

- 상위: `notes/2026-04-13-codex-transition-plan.md` (전환 전략 전반)
- 이 문서: **v0.3.0 close-out 이후 별도 실험 트랙**. 본선 편입 결정 이전의 PoC 범위만 고정한다.
- 본선 스펙 아님. v0.4 편입 여부는 PoC 결과를 본 뒤 별도 `/plugin-define` / spec 단계에서 판정한다.

## 트랙 지위

- v0.3.0 (tag `v0.3.0`, commit `2fb4f8a`) 는 baseline. **건드리지 않는다**.
- v0.4 본선 착수 전 또는 병렬로 수행 가능한 **비침투 실험**.
- `BACKLOG.md` inbox 의 "Codex 런타임 편입 가능성" 항목을 감사하는 트랙.

## 역할 경계 (lead / worker)

`notes/2026-04-13-codex-transition-plan.md` §"oh-my-claudecode team 시사점" 결론을 따른다.

| 주체 | 역할 | 금지 |
|---|---|---|
| **Claude (lead)** | plan.md 갱신, 태스크 분해/할당, fix task 삽입, verify gate, retry/abort 판정, 머지 | worker 가 만든 output 을 무검증 반영 |
| **Codex (worker)** | 단일 태스크 one-shot 실행. 지정된 worktree 내에서만 파일 변경. 결과는 stdout/파일로 반환 | plan.md 갱신, 다음 태스크 선택, 다른 worker 호출, team communication API 접근 |
| **tmux (v2 이후)** | 세션 호스팅, 관찰 레이어 | lifecycle 결정권 없음 |

핵심: **worker 는 상태 관리 주체 아님.** 세션 컨텍스트가 아니라 파일로 handoff.

## PoC 범위 (이번 트랙 한정)

### 포함

- `codex exec --json` 단독 smoke (tmux 없음)
- `--cd`, `--sandbox workspace-write`, `--add-dir` 동작 확인
- 종료코드, event 스키마, 로그 파일 크기/형식 관찰
- `scripts/poc/run_codex_worker.sh` 초안 (본선 미호출)
- 본 문서 및 smoke 결과 메모

### PoC wrapper 인터페이스

`scripts/poc/run_codex_worker.sh` 는 아래 인터페이스만 보장한다.

- `--cd <dir>`
- `--task-file <file>`
- `--log-dir <dir>`
- 선택: `--sandbox`, `--add-dir`, `--last-message`

wrapper 는 항상 아래 플래그를 강제한다.

- `codex exec --json`
- `--skip-git-repo-check`
- `--ephemeral`

wrapper 산출물:

- `events.jsonl`
- `stderr.log`
- `last-message.txt`
- `meta.json`

### 제외 (이번 트랙에서 하지 않음)

- `src/runtime/` 디렉토리 신설
- `src/claude.py` 이관 / `src/loop.py` backend 옵션 추가
- `scripts/ax_product_run.py` 수정
- `plugin/skills/ax-implement/SKILL.md` 수정
- `stages/` source of truth 분리
- tmux 세션 호스팅 / 멀티 worker
- Supabase 로깅 결합
- 대시보드 반영

위 항목은 PoC 결과가 긍정적일 때 v0.4 spec 단계에서 개별 평가한다.

## 본선 비접촉 원칙

아래 경로는 **읽기만 가능, 쓰기 금지**:

- `src/` 전체
- `plugin/` 전체
- `scripts/ax_product_run.py`, `scripts/ax_feedback.py`, `scripts/ax_post_commit.py`
- `labs/ax-implement/input/static-nextjs-min/` (fixture 원본)
- `versions/v0.3/`
- `dashboard/`

PoC 가 쓸 수 있는 경로:

- `notes/` (이 문서 계열)
- `scripts/poc/` (신설, 본선 미참조)
- `/tmp/codex-poc/` (repo 바깥, smoke 작업 공간)

## 실행 격리 규칙

1. smoke 는 `/tmp/codex-poc/<timestamp>/` 에서 실행. moomoo-ax repo worktree 밖.
2. Codex worker 의 `--cd` 는 위 임시 디렉토리로만 지정.
3. `--add-dir` 은 원칙적으로 비우고, 필요한 경우에만 해당 임시 경로로 제한.
4. moomoo-ax 의 어떤 파일도 worker 가 수정할 수 없게 한다 (sandbox 로 차단 + `--cd` 위치로 이중 차단).
5. smoke 결과물은 `notes/` 에 요약만 남기고, 원본 로그는 `/tmp/codex-poc/<timestamp>/` 에 둔다 (필요 시 일부만 `notes/2026-04-13-codex-worker-smoke.md` 에 인용).

## handoff 파일 규약 (v2 이후 필요 시)

PoC 단계에서는 쓰지 않지만, 본선 편입 시 적용할 위치를 미리 못박는다.

```
.harness/handoffs/<run_id>/<stage>-<phase>.md
```

필드 (oh-my-claudecode team 패턴):

- Decided
- Rejected
- Risks
- Files (touched)
- Remaining

lead 만 쓰기. worker 는 출력만 파일/stdout 으로 남기고 handoff 파일은 lead 가 정리 후 기록.

## 타임아웃 / 중단 기준 (PoC 단계)

- 단일 `codex exec` 호출 타임아웃 목표: **300 초 (5분)**.
- **wrapper 가 타임아웃을 강제하지 않는다.** macOS 기본 환경에 `timeout` 이 없으므로, PoC 단계에서는 호출측 책임으로 둔다.
- stdout 무활동 60 초 초과 시 중단 고려 (PoC 단계는 수동 관찰).
- 종료코드 비 0 시 재시도 없음. 결과를 그대로 기록.
- fix loop / retry 는 PoC 범위 아님 (lead 가 책임지는 본선 규약).

## 로그 저장 방식 (PoC)

- raw event: `/tmp/codex-poc/<ts>/events.jsonl`
- stderr: `/tmp/codex-poc/<ts>/stderr.log`
- 마지막 응답: `/tmp/codex-poc/<ts>/last-message.txt`
- 메타: `/tmp/codex-poc/<ts>/meta.json` (exit_code, duration_sec, command line, codex version)
- 공통 schema 정규화는 이번 PoC 에서 **하지 않는다**. 본선 편입 시 `normalize.py` 로 분리.

## tmux 세션 네이밍 (v2 이후 예약)

이번 PoC 에서는 **tmux 미사용**. 본선 편입 시 적용할 규약만 예약.

- 세션명: `ax-codex-<stage>-<short_run_id>` (예: `ax-codex-implement-1e9ae5a4`)
- 윈도우: `lead` / `worker-0` / `monitor`
- 세션 종료 권한: lead 만 보유. worker kill 시 lead 에게 알림.

## 성공 판정 (PoC)

아래를 모두 관찰할 수 있으면 PoC "성공" 으로 본다.

- [x] `codex exec --json --cd /tmp/codex-poc/<ts>` 가 exit 0 으로 종료한다.
- [x] `--json` 출력이 line-delimited JSON 이고, `type` 필드로 이벤트 구분이 가능하다.
- [x] 최종 assistant 응답을 `-o last-message.txt` 로 직접 수신할 수 있다.
- [x] `--sandbox workspace-write` 가 `--cd` 밖 쓰기를 실제로 차단한다 (확인 태스크 1개 포함).
- [x] worker 가 moomoo-ax repo 의 어떤 파일도 수정하지 않았다 (`git status` clean 으로 확인).

**중요 관찰**:

- sandbox 차단 케이스도 **exit 0** 으로 종료할 수 있다. 즉 성공/차단 판정은 종료코드만으로는 불충분하다.
- 차단 여부는 `last-message.txt` 와 `events.jsonl` 안의 agent message 를 함께 읽어야 한다.
- `thread.started.thread_id` 를 세션 식별자로 사용할 수 있다.
- `turn.completed.usage` 에서 `input_tokens`, `cached_input_tokens`, `output_tokens` 를 읽을 수 있다. 본선 편입 시 cost/usage 정규화에 재사용 가능하다.
- 관찰된 event type (smoke 기준): `thread.started`, `turn.started`, `item.started`, `item.completed`, `turn.completed`.

실패 시: 원인 (CLI 옵션 미지원 / 스키마 차이 / sandbox 우회 / 인증 이슈) 을 `notes/` 에 기록하고, wrapper 는 유지하되 본선 편입 작업은 보류한다.

## 다음 단계

1. (이 문서 확정 후) `/tmp/codex-poc/` 에서 smoke 1회 실행.
2. smoke 결과 요약을 `notes/2026-04-13-codex-worker-smoke.md` 에 기록.
3. wrapper 인터페이스와 로그 형식 보정:
   - bash 3.2 빈 배열 + `set -u` 가드 유지
   - timeout 은 호출측 책임으로 명시
   - sandbox 차단 판정은 `last-message.txt` / event 파싱 필수
4. PoC 종료 후 `BACKLOG.md` inbox 의 Codex 항목을 업데이트하고, v0.4 spec 단계에서 편입 여부 판정.
