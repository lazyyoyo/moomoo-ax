# exp-05 — `--output-format stream-json` 구조 + 자식 세션 환경 상속

- 날짜: 2026-04-11
- 축: 3 (+ exp-06 선행 답 포함)
- claude CLI: v2.1.101

## 목표

`--output-format json` 은 최종 result 한 줄만 준다. `stream-json` 은 per-turn / per-tool / per-event 를 주는가? levelup loop 의 tool call 감사 / 디버깅 / 토큰 회계 에 쓸 수 있는가?

**부가 목표** (원래 exp-06 였음): 부모 Claude Code 세션의 MCP / 플러그인 / 에이전트 / 스킬이 자식 `claude -p` 에 상속되는가?

## 설계

exp-01 Test 2 (Read tool) 와 동일한 프롬프트를 `--output-format stream-json --verbose` 로 재실행:

```bash
claude -p "Use the Read tool to read .../sandbox/fixture.txt and output line 2 exactly" \
  --allowedTools Read \
  --permission-mode acceptEdits \
  --output-format stream-json \
  --verbose
```

## 결과

stdout 에 6개 event (NDJSON):

| # | type | subtype | 의미 |
|---|---|---|---|
| 1 | `system` | `hook_started` | SessionStart:startup hook 발동 |
| 2 | `system` | `hook_response` | hook 응답 (outcome:success, exit_code:0) |
| 3 | `system` | `init` | **세션 초기화 메타 (mega event)** |
| 4 | `assistant` | — | LLM 의 첫 메시지 (tool_use: Read) |
| 5 | `user` | — | tool_result: 파일 내용 |
| 6 | `assistant` | — | LLM 의 두번째 메시지 (text reply) |
| 7 | `rate_limit_event` | — | rate limit 상태 (five_hour 윈도우) |
| 8 | `result` | `success` | 최종 결과 (기존 json 포맷과 동일) |

## 🔥 #3 init event 내용 — 결정적 발견

자식 세션의 `init` event 가 노출하는 필드:

```json
{
  "type":"system","subtype":"init",
  "cwd":"/Users/sunha/hq/projects/moomoo-ax",
  "session_id":"d9e2a3a2-...",
  "tools":[ /* 110+ 개 */ ],
  "mcp_servers":[
    {"name":"plugin:playwright:playwright","status":"connected"},
    {"name":"supabase","status":"connected"},
    {"name":"claude.ai Financial Datasets","status":"connected"},
    {"name":"claude.ai Gmail","status":"connected"},
    {"name":"claude.ai Google Calendar","status":"connected"},
    {"name":"claude.ai Excalidraw","status":"connected"}
  ],
  "model":"claude-opus-4-6[1m]",
  "permissionMode":"acceptEdits",
  "slash_commands":[ /* 70+ 개 */ ],
  "apiKeySource":"none",
  "claude_code_version":"2.1.101",
  "output_style":"default",
  "agents":[ /* 모든 subagent */ ],
  "skills":[ /* 모든 스킬 */ ],
  "plugins":[
    {"name":"codex","path":".../codex/1.0.1",...},
    {"name":"obsidian",...},
    {"name":"frontend-design",...},
    {"name":"team-scout",...},
    {"name":"team-design",...},
    {"name":"team-marketing",...},
    {"name":"team-newrich",...},
    {"name":"team-plugin",...},
    {"name":"statusline",...},
    {"name":"kesekit-ko",...},
    {"name":"playwright",...},
    {"name":"claude-code-setup",...},
    {"name":"moomoo-ax",...}
  ],
  "uuid":"...","fast_mode_state":"off"
}
```

### 결정적 발견

1. **자식 세션에 부모의 MCP 서버 6개 전부 `connected` 상태로 로드됨**:
   - **Playwright MCP** ← v0.2 F 에서 "ax-qa 가 못 쓰는 결정적 한계" 로 지목
   - Supabase MCP ← levelup 로그/feedback 주입 채널
   - Gmail / Calendar / Financial / Excalidraw
2. **13개 플러그인 모두 자동 로드** — moomoo-ax 플러그인 (`moomoo-ax@moomoo-ax/0.1.0`) 포함
3. 70+ 슬래시 명령 + 모든 subagent + 모든 skill 자동 노출
4. `apiKeySource: "none"` — OAuth/keychain 사용 중
5. `claude_code_version: "2.1.101"`, `model: "claude-opus-4-6[1m]"`, `permissionMode: "acceptEdits"`

### 상속 메커니즘 해석

**엄밀히는 "상속" 이 아니다**. 자식 `claude -p` 가 자기 설정 source (user `~/.claude/settings.json` + project `.claude/settings.json` + managed) 를 재로드해서 같은 플러그인/MCP 가 결과적으로 활성화된 것이다.

즉:
- 부모 프로세스의 MCP 소켓이나 플러그인 인스턴스가 자식에 넘어가진 않는다
- 자식이 스스로 `~/.claude/plugins/cache/` 를 읽고 MCP 서버를 새로 spawn
- 부모와 자식의 MCP 서버는 **별도 프로세스** — 독립적
- `--bare` 나 `--setting-sources` 로 이 로드를 차단 가능

levelup loop 관점에서 중요한 건: **차단하지 않으면 기본값으로 부모 환경이 복제된다**.

## #4-6 per-tool 메시지 구조

### #4 — tool_use

```json
{
  "type":"assistant",
  "message":{
    "model":"claude-opus-4-6",
    "content":[{
      "type":"tool_use",
      "id":"toolu_01NNTFzKSTBiriwgDTvMXKLm",
      "name":"Read",
      "input":{"file_path":"/Users/sunha/hq/projects/moomoo-ax/notes/v0.3-experiments/sandbox/fixture.txt"},
      "caller":{"type":"direct"}
    }],
    "usage":{"input_tokens":6,"cache_creation_input_tokens":36893,...},
  },
  "session_id":"...","uuid":"..."
}
```

필드: `tool_use.id`, `tool_use.name`, `tool_use.input`, `tool_use.caller.type` (direct/skill/agent 추정), `usage` per-message.

### #5 — tool_result

```json
{
  "type":"user",
  "message":{
    "content":[{
      "tool_use_id":"toolu_01NNTFzKSTBiriwgDTvMXKLm",
      "type":"tool_result",
      "content":"1\thello from fixture\n2\tline 2: moomoo-ax v0.3 exp-01\n..."
    }]
  },
  "tool_use_result":{
    "type":"text",
    "file":{"filePath":"...","content":"...","numLines":4,"startLine":1,"totalLines":4}
  }
}
```

tool_result 가 두 군데 등장:
- `message.content[0].content` — text (줄번호 포함)
- `tool_use_result.file.content` — 원본 파일 내용 + 메타

Read tool 이 file metadata 까지 주는 구조는 levelup loop 의 diff 계산에 직접 재활용 가능.

### #6 — 최종 text reply

```json
{
  "type":"assistant",
  "message":{
    "content":[{"type":"text","text":"line 2: moomoo-ax v0.3 exp-01"}],
    "usage":{"input_tokens":1,"cache_creation_input_tokens":177,"cache_read_input_tokens":36893,...}
  }
}
```

## 핵심 발견

### 1. stream-json 은 per-tool audit 을 완전히 제공한다

- 각 tool_use 가 별도 event (`type: assistant`, `content[0].type: tool_use`)
- 각 tool_result 가 별도 event (`type: user`, `content[0].type: tool_result`)
- tool_use 와 tool_result 는 `tool_use_id` 로 pair
- per-message `usage` (cache_read/creation, input/output)

**이게 levelup loop 의 토큰 회계/감사 기반**. v0.1/v0.2 의 `src/claude.py` 는 최종 `total_cost_usd` 만 수집했지만, stream-json 이면 per-tool 로 비용을 쪼갤 수 있다.

### 2. SessionStart hook 이 `-p` 모드에서도 돈다

`#1-2` 에서 `SessionStart:startup` hook 이 fire → outcome: success. 즉 **`-p` 모드에서도 user settings 의 hook 이 실행된다**. 이건 levelup loop 관점에서 양날의 검:
- 장점: Python 하네스가 hook 을 통해 자식 세션에 환경 주입 가능
- 단점: 무관한 hook 이 자식 세션에 영향 → 재현성 깨짐. **`--bare` 로 차단 필요**.

### 3. rate_limit_event 가 별도 이벤트로 노출

`five_hour` 윈도우. `status: "allowed"`, `overageStatus: "allowed"`, `overageResetsAt` 포함. levelup loop 이 rate limit 근접 시 자동 백오프 가능.

### 4. 자식 세션은 부모 환경을 기본 복제한다 (exp-06 선행 답)

**v0.2 F 의 가정은 대부분 틀렸다**:

| v0.2 F 의 주장 | 실제 |
|---|---|
| `claude -p` 는 MCP 접근 불가 | ❌ 6개 MCP 서버 connected 상태로 로드됨 |
| Playwright MCP 는 ax-qa 에서 사용 불가 | ❌ 자식 세션에 Playwright MCP 연결됨 |
| skill/agent 접근 불가 | ❌ 70+ slash command, 모든 agent 로드됨 |
| plugin 접근 불가 | ❌ 13개 플러그인 자동 활성 |

남은 질문: 자식 세션에서 Playwright tool 이 **실제로 호출 가능한지** (connected ≠ callable). → exp-06 에서 1-shot 으로 검증.

## 판정

**exp-05: ✅ 완전 성공**

**추가 판정 (exp-06 선행)**: 자식 세션 MCP 상속 = **사실상 확인됨** (connected 상태). 실 호출 테스트만 남음.

## 함의 (v0.3 재설계)

1. **levelup loop 은 `stream-json` 을 디폴트로 써야 한다**. json 은 감사 정보 부족.
2. **`--bare` 플래그로 재현성 확보**: 자식 세션이 부모 환경 전체를 복제하면 재현성 깨짐. `--bare` + `--plugin-dir plugin` + `--setting-sources user` 같이 명시 로드가 정석.
3. **토큰 회계 재설계**: `src/db.py` 에 per-tool_use 로 cost 를 저장해야 rubric 평가에서 "어떤 tool 이 얼마나 썼는지" 를 분석 가능. 지금은 총합만.
4. **ax-qa 재설계 불필요**: Playwright MCP 가 자식 세션에서 이미 connected. `--plugin-dir plugin` + SKILL.md 본문에서 `mcp__plugin_playwright_playwright__*` tool 을 allowedTools 로 명시하면 실 호출 가능할 것 (exp-06 확인).

## 결과 파일

- `sandbox/exp05-stream.ndjson` — 전체 stream 출력 (~7 events)
