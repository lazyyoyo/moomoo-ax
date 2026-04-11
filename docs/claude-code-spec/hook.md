# Claude Code Hook 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사.

## Hook Event 종류

### Per-Session

- `SessionStart` (matcher: `startup|resume|clear|compact`)
- `SessionEnd` (matcher: `clear|resume|logout|prompt_input_exit|bypass_permissions_disabled|other`)

### Per-Turn

- `UserPromptSubmit`: 사용자 프롬프트 제출 직전 (Claude 처리 전)
- `Stop`: Claude 응답 완료 후
- `StopFailure` (matcher: `rate_limit|authentication_failed|billing_error|invalid_request|server_error|max_output_tokens|unknown`)

### Per-Tool

- `PreToolUse`: 도구 실행 직전 (**blocking 가능**)
- `PostToolUse`: 도구 성공 후
- `PostToolUseFailure`: 도구 실패 후
- `PermissionRequest`: 권한 대화창 표시 직전
- `PermissionDenied`: auto mode 분류기가 도구 거부 후

### Async

- `Notification` (matcher: `permission_prompt|idle_prompt|auth_success|elicitation_dialog`)
- `SubagentStart` / `SubagentStop` (matcher: agent type name)
- `TaskCreated` / `TaskCompleted`
- `CwdChanged`
- `FileChanged` (matcher: literal filenames, `|` 구분)
- `WorktreeCreate` / `WorktreeRemove`
- `InstructionsLoaded` (matcher: `session_start|nested_traversal|path_glob_match|include|compact`)
- `ConfigChange` (matcher: `user_settings|project_settings|local_settings|policy_settings|skills`)
- `PreCompact` / `PostCompact` (matcher: `manual|auto`)
- `Elicitation` / `ElicitationResult` (matcher: MCP server name)
- `TeammateIdle`

## 설정 위치 및 우선순위

1. `~/.claude/settings.json` — global
2. `.claude/settings.json` — 프로젝트 공유 (git commit)
3. `.claude/settings.local.json` — 프로젝트 개인 (gitignore)
4. Plugin `hooks/hooks.json` — 플러그인 활성화 시
5. Skill/Agent frontmatter — 컴포넌트 활성화 시
6. Managed settings — 조직 전체 (override 불가)

## 설정 구조

```json
{
  "hooks": {
    "EVENT_NAME": [
      {
        "matcher": "pattern",
        "if": "PermissionRule(pattern)",
        "hooks": [
          {
            "type": "command|http|prompt|agent",
            "command|url|prompt": "...",
            "timeout": 600,
            "statusMessage": "optional text"
          }
        ]
      }
    ]
  },
  "disableAllHooks": false
}
```

## 실행 컨텍스트

### 입력 (stdin JSON)

공통 필드:
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "permission_mode": "default|plan|acceptEdits|auto|dontAsk|bypassPermissions",
  "hook_event_name": "EventName",
  "agent_id": "optional-subagent-id",
  "agent_type": "optional-agent-name"
}
```

Event 별 추가 필드:
- `PreToolUse`: `tool_name`, `tool_input`
- `UserPromptSubmit`: `prompt`
- 등

### 출력 (Exit Code + JSON)

| Exit code | 의미 |
|---|---|
| 0 | 성공. stdout JSON 파싱 후 action 진행 |
| 2 | **blocking error**. stderr 가 Claude 피드백, action 거부 |
| 기타 | non-blocking error. notice 표시, 계속 |

**JSON 출력 (exit 0 일 때 선택)**:
```json
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "Optional warning",
  "stopReason": "reason if continue: false",
  "decision": "block|allow",
  "reason": "Why blocked",
  "additionalContext": "Text injected into Claude context",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "Why",
    "updatedInput": { "command": "modified command" },
    "updatedPermissions": [
      { "type": "setMode", "mode": "acceptEdits", "destination": "session" }
    ]
  }
}
```

## Plugin vs User Hook

**Plugin-provided**:
- 위치: `hooks/hooks.json` 또는 plugin.json inline
- 플러그인 활성화 시 자동 로드
- 비활성 시 로드 안 됨
- 수정은 플러그인 업데이트로만

**User-provided**:
- 위치: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`
- session 중 변경 감지 시 자동 reload
- 언제든 편집 가능
- Plugin hooks 와 merge 되면 **둘 다 실행**

## Tool Blocking 메커니즘

### PreToolUse — Tool 거부

**방법 1 — Exit code 2 (추천)**:
```bash
echo "Blocked reason" >&2
exit 2
```

**방법 2 — JSON**:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Reason"
  }
}
```
(exit 0)

### PostToolUse/Stop Blocking

```json
{
  "decision": "block",
  "reason": "Why"
}
```

### PermissionRequest Blocking

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "updatedPermissions": [...]
    }
  }
}
```

## Matcher Patterns

### 대상별

- `PreToolUse`/`PostToolUse`/`PermissionRequest` 등: tool name
- `SessionStart`: `startup|resume|clear|compact`
- `ConfigChange`: `user_settings|project_settings|local_settings|policy_settings|skills`

### 문법

- 빈 문자열/생략: 모든 경우 match
- 정확 문자: `Bash`, `Edit`
- 정확 list (pipe 구분): `Edit|Write`
- 정규식: `^Notebook`, `mcp__memory__.*`

### MCP 도구 매칭

- 형식: `mcp__<server>__<tool>`
- 예: `mcp__github__search_repositories`
- `mcp__github__.*` (github 서버 모든 도구), `mcp__.*__write.*`

## `if` Field (v2.1.85+)

tool name 과 arguments 를 함께 필터링. permission rule syntax 사용.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm *)",
            "command": "check-rm-policy.sh"
          }
        ]
      }
    ]
  }
}
```

적용 이벤트: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`.

## Hook Type 별 컨텍스트

### Command hook

- stdin: JSON event data
- stdout: JSON response
- stderr: Claude 피드백 또는 debug log
- timeout: 기본 600초

### HTTP hook

- POST JSON body
- Response: 2xx = success, non-2xx = non-blocking error
- Response body: command hook 과 동일한 JSON
- Header 환경변수 치환: `$VAR_NAME` / `${VAR_NAME}` (allowedEnvVars 에만)

### Prompt hook

- Model: 기본 Haiku, `model` field 로 변경 가능
- Input: hook JSON + prompt text
- Output: `{"ok": true}` or `{"ok": false, "reason": "..."}`
- timeout: 기본 30초

### Agent hook

- Subagent spawn (tool access 포함)
- 60초 timeout, 50 turns max
- Input/output prompt hook 과 동일

## `--include-hook-events` CLI Flag

stream-json output 에 hook events 포함. transcript 에 각 hook 실행 기록 표시.

## 비활성화

**전역**:
```json
{ "disableAllHooks": true }
```

**스코프별 우선순위**:
- managed `disableAllHooks: true` → user/project override 불가
- user `true`, project `false` → project 우선

## 환경 변수

Hook script 에서 사용 가능:

- `$CLAUDE_PROJECT_DIR`: 프로젝트 root
- `${CLAUDE_PLUGIN_ROOT}`: 플러그인 디렉토리
- `${CLAUDE_PLUGIN_DATA}`: 플러그인 persistent data
- `$CLAUDE_ENV_FILE`: SessionStart hook 에서 환경변수 추가 (append 만)

## 성능 제약

- 기본 timeout: command 600s, prompt 30s, agent 60s
- 모든 matching hooks 병렬 실행
- 동일 command 자동 deduplication
- 여러 PreToolUse hook 이 `updatedInput` return → 마지막 완료 hook 의 output 사용 (non-deterministic)

## moomoo-ax 관점의 함의

- **`SubagentStop` hook** → levelup loop 가 각 iter 를 subagent 로 래핑하면, 각 iter 종료 시점을 hook 으로 캡처해서 rubric 평가 자동 트리거 가능. Python 폴링 루프 대체.
- **`PostToolUse` + `if` field** → team-ax 의 SKILL.md 가 특정 Bash 스크립트를 실행할 때 hook 으로 rubric check 주입 가능 → **Progressive Codification 의 강제 집행 레이어**.
- **현재 `scripts/ax_post_commit.py`** 는 git post-commit hook 인데, Claude Code hook 시스템과는 별개. 두 레이어를 혼동하지 말 것.
- **plugin 이 제공하는 hook 은 `plugin/hooks/hooks.json` 로 정의** → team-ax 에 장착 가능.

---

**출처**:
- https://code.claude.com/docs/en/hooks-guide.md
- https://code.claude.com/docs/en/hooks.md
- https://code.claude.com/docs/en/hooks-reference.md
