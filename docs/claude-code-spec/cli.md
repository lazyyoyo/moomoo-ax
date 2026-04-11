# Claude Code CLI 레퍼런스

> v0.3 Phase 0 리서치 산출물.
> 출처: `claude --help` (v2.1.101, 2026-04-11 캡처) + claude-code-guide 보완.

## 버전

- 캡처 시점: **2.1.101**
- 캡처 일: 2026-04-11
- 명령: `claude --help`

## 기본 문법

```
claude [options] [command] [prompt]
```

- 기본: 인터랙티브 세션
- `-p`/`--print`: 비인터랙티브 (파이프용). workspace trust dialog 스킵 → 신뢰 디렉토리만 사용.

## 핵심 옵션 (levelup loop 관점)

### Tool / Permission

| 플래그 | 의미 | 사용 메모 |
|---|---|---|
| `--allowedTools`, `--allowed-tools <tools...>` | 허용 도구 (공백/쉼표 구분). 예: `"Bash(git:*) Edit"` | rule 문법. `permissions.allow` 에 merge |
| `--disallowedTools`, `--disallowed-tools <tools...>` | 차단 도구 | deny rule |
| `--tools <tools...>` | **사용 가능 도구 세트**. `""` 전부 비활성, `default` 전부, 특정 목록 (`Bash,Edit,Read`) | allowedTools 와 다른 레이어 |
| `--permission-mode <mode>` | `acceptEdits|auto|bypassPermissions|default|dontAsk|plan` | `-p` 에서 `default` 는 사실상 tool 거부 |
| `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` | 모든 prompt 스킵 (protected 제외) | sandbox 전용 |

### Session / Resume

| 플래그 | 의미 |
|---|---|
| `-p`, `--print` | 응답 출력 후 종료 |
| `-c`, `--continue` | 현 디렉토리 최근 대화 이어쓰기 |
| `-r`, `--resume [value]` | session id 로 재개 (또는 picker) |
| `--session-id <uuid>` | 특정 session id 사용 (반드시 valid UUID) |
| `--fork-session` | resume 시 새 session id 생성 |
| `--no-session-persistence` | 디스크 저장 안 함 (`-p` 전용) |
| `--from-pr [value]` | PR 에 연결된 session 재개 |

### Output / Input

| 플래그 | 의미 |
|---|---|
| `--output-format <format>` | `text` (기본) / `json` / `stream-json` (`-p` 전용) |
| `--input-format <format>` | `text` (기본) / `stream-json` (realtime 입력) |
| `--include-hook-events` | stream-json 에 hook 이벤트 포함 |
| `--include-partial-messages` | partial chunk 포함 |
| `--replay-user-messages` | 입력을 출력으로 재반환 |
| `--json-schema <schema>` | 구조화 출력 검증 JSON Schema |

### Model / Budget

| 플래그 | 의미 |
|---|---|
| `--model <model>` | `sonnet`, `opus`, 또는 full name |
| `--fallback-model <model>` | overloaded 시 fallback (`-p` 전용) |
| `--effort <level>` | `low` / `medium` / `high` / `max` |
| `--max-budget-usd <amount>` | 최대 지출 (`-p` 전용) |
| `--betas <betas...>` | beta header (API key 유저 only) |

### Plugin / MCP / Agent

| 플래그 | 의미 |
|---|---|
| `--plugin-dir <path>` | 로컬 플러그인 세션 전용 로드 (반복 가능) |
| `--mcp-config <configs...>` | MCP 서버 설정 로드 |
| `--strict-mcp-config` | `--mcp-config` 만 사용, 다른 MCP 무시 |
| `--agent <agent>` | 세션 agent 지정 |
| `--agents <json>` | 인라인 custom agent 정의. 예: `'{"reviewer": {"description": "...", "prompt": "..."}}' ` |

### System Prompt / Context

| 플래그 | 의미 |
|---|---|
| `--system-prompt <prompt>` | 시스템 프롬프트 전체 교체 |
| `--append-system-prompt <prompt>` | 기본 시스템 프롬프트에 append |
| `--add-dir <directories...>` | 추가 디렉토리 도구 접근 허용 |
| `--exclude-dynamic-system-prompt-sections` | per-machine 섹션을 첫 user message 로 이동 (prompt cache reuse 향상) |
| `--setting-sources <sources>` | `user,project,local` 중 선택 로드 |
| `--settings <file-or-json>` | 추가 settings |
| `--file <specs...>` | 시작 시 파일 다운로드 (`file_id:relative_path`) |

### Bare / Worktree / IDE

| 플래그 | 의미 |
|---|---|
| `--bare` | 최소 모드: hooks/LSP/plugin sync/attribution/auto-memory/prefetch/keychain/CLAUDE.md auto-discovery 스킵. `CLAUDE_CODE_SIMPLE=1`. 3P provider 는 자체 credential. Skills 는 `/skill-name` 으로 resolve. Context 는 명시 주입 필요 |
| `-w`, `--worktree [name]` | 새 git worktree 생성 |
| `--tmux` | tmux session (worktree 필요) |
| `--ide` | IDE 자동 연결 |
| `--chrome` / `--no-chrome` | Chrome 통합 |

### Debug / Misc

| 플래그 | 의미 |
|---|---|
| `-d`, `--debug [filter]` | 디버그 모드. 카테고리 필터 가능 (`api,hooks` / `!1p,!file`) |
| `--debug-file <path>` | 디버그 로그 파일 경로 |
| `--verbose` | verbose 설정 override |
| `-v`, `--version` | 버전 |
| `-n`, `--name <name>` | session display name |
| `--remote-control-session-name-prefix <prefix>` | remote control session name prefix |
| `--disable-slash-commands` | 모든 skill 비활성 |
| `--brief` | SendUserMessage tool 활성 (agent → user) |

## Subcommands

| 명령 | 용도 |
|---|---|
| `agents [options]` | 구성된 agent 리스트 |
| `auth` | 인증 관리 |
| `auto-mode` | auto mode classifier 설정 조회 |
| `doctor` | auto-updater 상태 진단 |
| `install [options] [target]` | native build 설치 (stable/latest/version) |
| `mcp` | MCP 서버 설정/관리 |
| `plugin` / `plugins` | 플러그인 관리 |
| `setup-token` | long-lived auth token 설정 |
| `update` / `upgrade` | 업데이트 |

## v0.3 리서치 관점 — 축 1 세부 질문 초기 판정

> `notes/2026-04-11-v0.3-research-scope.md` 축 1 의 세부 질문들에 대한 `--help` 기반 1차 답변. 실험 필요 항목은 ⚠️ 표시.

| 질문 | 초기 판정 | 근거 / 실험 계획 |
|---|---|---|
| `claude -p` + `--allowedTools Read,Write,Bash,Agent` 동작? | ✅ 플래그 존재. ⚠️ 실제 tool call 여부는 실험 | `exp-01-echo`, `exp-02-stateful` |
| `--permission-mode {auto, acceptEdits, plan, bypassPermissions}` 동작? | ✅ 존재. `-p` 에서 `default` 는 사실상 거부 | permissions.md 정리됨 |
| 스킬 강제 load (`--skill team-ax:ax-implement` 같은)? | ❌ **`--skill` 플래그 없음** | 대신: `--plugin-dir plugin` + `$ARGUMENTS` 스킬 호출 프롬프트, 또는 `--agent` / `--agents` JSON |
| plugin 활성/비활성 플래그? | 간접: `--plugin-dir` 로 로컬 로드, `plugin enable/disable` subcommand | `exp-04-skill-load` |
| `--output-format json` 에 tool call / cost / token 포함? | ⚠️ 실험 필요 | `exp-01-echo` 출력 분석 |
| `--resume {session_id}` 세션 이어붙이기? | ✅ 존재 (`-r`) | loop 에 유용한가는 별도 판단 |
| Claude Code 안에서 또 `claude` subprocess 호출 (재귀)? | ⚠️ `--session-id` 충돌 + permission 상속 미확인 | `exp-03-recursion` |
| stdin 대량 입력 제한? | ⚠️ 실험 필요 | `exp-01-echo` (수십 KB fixture) |
| stdout JSON max size? | ⚠️ 실험 필요 | `exp-05-cost-tracking` |
| `--bare` 모드에서 plugin 가능? | ✅ Skills 는 `/skill-name` 으로 resolve 가능. `--plugin-dir` 허용됨 | 재현성 위해 loop 에서 고려 |

## 핵심 관찰 5개

1. **`--skill` 플래그가 없다**. 스킬 강제 로드는 `--plugin-dir` + 프롬프트 내 `/plugin-name:skill-name` 호출로 해야 함. 또는 `--agent` / `--agents` 로 subagent 를 ad-hoc 정의.
2. **`--agents` JSON 플래그가 있다**. Python 하네스가 각 iteration 을 즉석에서 subagent 로 정의해서 `claude -p` 로 실행 가능. **Path A 의 핵심 빌딩 블록**.
3. **`--bare` 모드** 는 hooks/auto-memory/plugin sync 를 스킵 → 재현성/cache-reuse 향상. levelup loop 의 기본 후보.
4. **`--exclude-dynamic-system-prompt-sections`** 는 prompt cache 재활용을 늘림 → 반복 호출이 많은 loop 에서 비용 절감 수단.
5. **`--max-budget-usd`** + **`--fallback-model`** + **`--output-format json`** 조합이면 Python 하네스가 비용/리스크를 런타임에 제어 가능.

## 미해결 질문 (실험으로 회답)

1. `claude -p --allowedTools` 로 실제 tool call 이 돌고 JSON output 에 나오는가? → `exp-01-echo`
2. `claude -p` 가 파일 쓰기까지 수행 가능한가 (`--permission-mode acceptEdits` 필요?) → `exp-02-stateful`
3. Claude Code 세션 안에서 `claude` 를 subprocess 로 또 호출 가능한가? → `exp-03-recursion`
4. `--plugin-dir plugin` 으로 team-ax 를 로드한 상태에서 `/team-ax:ax-implement` 호출 가능한가? → `exp-04-skill-load`
5. `--output-format json` 출력의 tool call / usage / cost 필드 스키마는? → `exp-05-cost-tracking`
6. 부모 세션의 MCP 서버를 자식 `claude -p` 가 사용할 수 있는가? → `exp-06-mcp`

## 전체 `--help` 풀 출력 (캐시)

`notes/v0.3-experiments/claude-help-2.1.101.txt` 로 별도 보관 예정.
