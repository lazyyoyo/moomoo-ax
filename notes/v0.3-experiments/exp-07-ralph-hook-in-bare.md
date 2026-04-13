# exp-07 — Ralph Stop hook in `claude -p` child session

- 날짜: 2026-04-13
- 축: Phase A 의 Ralph 루프 설계 선결 조건
- 배경: v0.3 plan 재편. product loop 내부에서 Ralph Stop hook 으로 plan.md 체크박스 소비 루프를 자체 구동하려면, `claude -p --plugin-dir` 자식 세션에서 plugin 의 Stop hook 이 발화해야 함.
- claude CLI: v2.1.104

## 목표

두 질문:

1. `claude -p --plugin-dir <dir>` 자식 세션에서 plugin 이 제공하는 **Stop hook 이 발화하는가**?
2. `--bare` 플래그와의 조합은?

## 설계

### canary plugin

```
sandbox/exp07-plugin/
├── .claude-plugin/plugin.json    # name: exp07
├── hooks/
│   ├── hooks.json                # Stop hook 등록
│   └── stop-hook.sh              # 카운터 파일 + 1번째 호출 block, 2번째부터 allow
└── skills/
    └── try-exit/SKILL.md         # "Output EXP07_HELLO and nothing else"
```

`stop-hook.sh` 로직:
- `/tmp/exp07-hook-count.txt` 증가
- `/tmp/exp07-hook-log.txt` 에 HOOK_INPUT 기록
- count=1: `{"decision":"block","reason":"Now output exactly: EXP07_AFTER_HOOK"}` 반환 → Claude 에게 재프롬프트
- count≥2: exit 0 (exit 허용)

기대 시그널:
- Stop hook 동작 → 카운터=2, 최종 assistant output 이 `EXP07_AFTER_HOOK`, num_turns ≥ 2
- 동작 안 함 → 카운터 파일 없음, num_turns=1, 응답은 `EXP07_HELLO` 만

## 테스트 & 결과

### Test A — `--bare + --plugin-dir`

```bash
claude --plugin-dir $SANDBOX/exp07-plugin \
  -p "/exp07:try-exit" \
  --permission-mode acceptEdits \
  --output-format stream-json --verbose \
  --include-hook-events \
  --bare \
  --setting-sources project,local
```

결과:
- exit=1, `is_error: true`, `num_turns: 1`
- `result`: **`"Not logged in · Please run /login"`**
- `error`: `"authentication_failed"`
- 카운터/로그 파일 **생성 안 됨** (hook 발화 전에 auth 실패로 종료)

**관찰**: `--bare` 가 keychain/OAuth credential 까지 끊음. Phase 0 feasibility 에서 "재현성 확보용 --bare" 로 제안했던 게 **실제로는 사용 불가**. 문서의 `--bare` 권장 조항을 수정해야 함.

### Test B — `--plugin-dir` 만 (`--bare` 제외)

```bash
claude --plugin-dir $SANDBOX/exp07-plugin \
  -p "/exp07:try-exit" \
  --permission-mode acceptEdits \
  --output-format stream-json --verbose \
  --include-hook-events \
  --setting-sources project,local
```

결과:
- exit=0, `is_error: false`, `num_turns: 2`, `cost: $0.209`
- `result`: `"EXP07_AFTER_HOOK"` (두 번째 턴의 응답)
- stream-json assistant 메시지 순서: `EXP07_HELLO` → `EXP07_AFTER_HOOK`
- 카운터 파일: **`2`** (Stop hook 두 번 호출)
- hook 로그:
  ```
  === Stop hook fired #1 ... ===
  last_assistant_message: EXP07_HELLO
  stop_hook_active: false

  === Stop hook fired #2 ... ===
  last_assistant_message: EXP07_AFTER_HOOK
  stop_hook_active: true
  ```

**관찰**:
- ✅ plugin Stop hook 이 `claude -p` headless 자식 세션에서 **완전 정상 발화**
- ✅ `{"decision":"block","reason":"..."}` 출력 → reason 이 다음 prompt 로 재주입되어 LLM 이 그에 맞게 응답
- ✅ Claude 가 재주입된 prompt 에 순응 (`EXP07_AFTER_HOOK` 출력)
- ✅ `stop_hook_active` 필드로 재귀 루프 진입 여부 감지 가능 (Ralph 의 session isolation 로직과 호환)

## 핵심 결론

1. **Phase A.4 의 Ralph Stop hook 설계는 실현 가능**. 자식 `-p` 세션에서 Stop hook 이 발화하며 block+reason 재주입이 동작한다. v0.3 plan R3 (가장 높은 리스크) **해소**.
2. **`--bare` 는 사용 금지**. auth credential 까지 끊어서 `-p` 자식 세션이 `"Not logged in"` 로 즉시 종료. Phase 0 feasibility 에서 재현성 근거로 제안했던 `--bare` 는 무효. `--setting-sources project,local` 만으로 재현성 확보해야 함.
3. `--include-hook-events` 플래그는 stream-json 에 hook 실행 이벤트를 추가로 포함하므로 감사 데이터에 유용. Phase A 의 tool_events 파서에 hook_events 도 추가 파싱 필요.

## plan 업데이트 지시사항

다음 항목을 `versions/v0.3/plan.md` 에 반영:

- **R2/R3 해소** — Stop hook 동작 확인. Phase A.4.3 완료로 체크.
- **`--bare` 제거** — Phase A.5.3 실행 커맨드 예시에서 `--bare` 삭제. Phase 1a 기록에도 `--bare=False` 가 실전 기본값이라 명시.
- **Phase 1a claude.py** — `bare` 옵션 자체는 유지 (수동 실험용), 다만 call 기본값은 `bare=False` 유지.
- **리스크 R3 → 해소 완료로 마감, R2 → `--bare` 제거로 해소**.

## 재현

```bash
rm -f /tmp/exp07-hook-log.txt /tmp/exp07-hook-count.txt
SANDBOX=/Users/sunha/hq/projects/moomoo-ax/notes/v0.3-experiments/sandbox
cd $SANDBOX/exp07-workdir && claude \
  --plugin-dir $SANDBOX/exp07-plugin \
  -p "/exp07:try-exit" \
  --permission-mode acceptEdits \
  --output-format stream-json --verbose \
  --include-hook-events \
  --setting-sources "project,local"
cat /tmp/exp07-hook-count.txt  # 기대: 2
```

## 이번 실험 한 줄 수확

> Stop hook 은 `-p` 에서도 돈다 — 그러나 `--bare` 를 걸면 로그인부터 끊긴다. 재현성은 `--setting-sources project,local` 로만 확보.
