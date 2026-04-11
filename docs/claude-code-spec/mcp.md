# Claude Code MCP 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사.

## `.mcp.json` 형식

```json
{
  "mcpServers": {
    "server-name": {
      "command": "path/to/binary",
      "args": ["arg1", "arg2"],
      "env": { "VAR": "value" },
      "cwd": "/working/directory",
      "timeout": 30000,
      "autoStart": true,
      "transport": "stdio",
      "initializationOptions": {}
    }
  }
}
```

### 필드

- `command` (required): MCP 서버 바이너리
- `args` (optional): array
- `env` (optional): object
- `cwd` (optional): working directory
- `timeout` (optional): ms
- `autoStart` (optional): 세션 시작 시 자동 시작
- `transport` (optional): `stdio` (기본) 또는 `socket`
- `initializationOptions` (optional): 서버 초기화

### CLI Flag

- `--mcp-config <path>`: 커스텀 .mcp.json 지정
- `--strict-mcp-config`: failed server 가 session 차단

## Plugin 내장 MCP Server

### plugin.json inline

```json
{
  "name": "my-plugin",
  "mcpServers": {
    "database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": { "DB_PATH": "${CLAUDE_PLUGIN_DATA}" }
    }
  }
}
```

### plugin `.mcp.json`

```json
{
  "database": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
  }
}
```

### Path Variables

- `${CLAUDE_PLUGIN_ROOT}`: 플러그인 설치 절대경로 (변함)
- `${CLAUDE_PLUGIN_DATA}`: persistent data (안 변함)
- `${CLAUDE_PLUGIN_OPTION_*}`: userConfig 값

### Managed MCP

```json
{
  "mcpServers": {
    "allowed-server": { "command": "/usr/bin/server" }
  },
  "allowManagedMcpServersOnly": true,
  "deniedMcpServers": ["forbidden-server"]
}
```

- `allowManagedMcpServersOnly: true` → managed allowed 만 허용
- `deniedMcpServers`: 차단 명시

## Tool/Resource/Prompt 노출

### Tool

- MCP 서버 도구 → Claude Code 도구 목록에 자동 추가
- 네이밍: `mcp__<server-name>__<tool-name>`
- 예: `mcp__github__search_repositories`
- Permission rule: `mcp__github__.*`
- 일반 도구와 동일하게 permission 적용

### Resource

- `/mcp` 명령어로 browseable
- 자동 호출 대상 아님

### Prompt

- system prompts → session context 에 자동 inject
- Claude 동작을 MCP 레벨에서 조정

## Subprocess 상속 (⚠️ 확인 필요)

**공식 문서에 명시 없음**. 다음은 추론 기반:

- `subprocess.run(["claude", "-p", prompt])` 는 새 독립 session 시작
- Parent session 의 MCP 서버는 자동 상속되지 않음 (각 session 독립)
- 자식 session 에서 MCP 사용하려면: 자식도 `.mcp.json` 또는 managed settings 필요
- 전역 MCP (`~/.claude/` settings) 는 상속 가능성 높음

### `--mcp-config` 플래그 (subprocess)

```bash
claude -p "..." --mcp-config /path/to/mcp.json
```
해당 설정만 로드 (parent merge 안 함).

**⚠️ v0.3 실험 대상**: `notes/v0.3-experiments/exp-06-mcp.md` 에서 검증 필요.

## Stdio vs HTTP Transport

### Stdio (기본)

- stdin/stdout JSON-RPC
- 프로세스 시작 시 spawn
- 종료: parent process 가 서버 termination 담당
- 장점: 간단, 프로세스 격리
- 가장 일반적

### HTTP / Socket

- 독립 서버 (HTTP endpoint)
- Claude Code 가 HTTP POST 로 통신
- 독립 lifecycle (parent process 와 별개)
- 장점: 복잡 아키텍처, 여러 client 지원
- 설정: `"transport": "socket"`

## `--strict-mcp-config` 동작

- 기본: MCP 서버 실패 → warning 만, session 계속
- `--strict-mcp-config`: MCP 서버 실패 → error, session abort
- startup 검증 강화

## moomoo-ax 관점의 함의

- **ax-qa 가 필요로 했던 Playwright / axe-core / Lighthouse 는 MCP 로 노출 가능**. 하지만 **subprocess 로 자식 `claude` 를 띄웠을 때 parent 의 MCP 가 상속되는지 미확인** → **exp-06 에서 직접 검증**.
- 만약 상속 안 된다면, team-ax 플러그인에 `mcp_servers` 필드로 Playwright MCP 를 **내장** 해야 함 (현재 `.claude-plugin/plugin.json` 에는 mcp_servers 없음).
- managed `allowManagedMcpServersOnly` 를 켜면 team-ax 가 예측 가능한 MCP 환경을 강제 가능.

---

**출처**:
- https://code.claude.com/docs/en/mcp.md
- https://code.claude.com/docs/en/plugins-reference.md#mcp-servers
- https://code.claude.com/docs/en/settings.md
