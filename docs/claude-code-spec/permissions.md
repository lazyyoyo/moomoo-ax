# Claude Code Permissions 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사.

## `--permission-mode` 모든 값

### 1. `default`

- 표준 동작. 도구 처음 사용 시 prompt
- Read-only: 승인 불필요
- Write/Bash: 권한 prompt

### 2. `acceptEdits`

- 파일 편집 및 일반 filesystem 명령 자동 승인
- Auto-approve:
  - `Edit`, `Write`
  - Bash: `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed`
  - 환경변수 prefix (`LANG=C`, `NO_COLOR=1` 등)
  - Process wrapper (`timeout`, `nice`, `nohup`)
- 범위: working directory 또는 `additionalDirectories`
- 제약: protected paths 는 여전히 prompt

### 3. `plan`

- Plan mode. 읽기 전용, 수정 불가
- Auto-approve: Read-only
- Deny: Edit/Write/대부분의 Bash

### 4. `auto` (v2.1.83+, research preview)

- Background safety classifier 로 prompt 제거
- **조건**:
  - Plan: Team/Enterprise/API (Pro/Max 제외)
  - Admin: Team/Enterprise 에서 admin 활성화
  - Model: Sonnet 4.6+ 또는 Opus 4.6+ (Haiku/claude-3 제외)
  - Provider: Anthropic API only (Bedrock/Vertex/Foundry 제외)
- **Classifier blocking** 예: `curl | bash`, 민감정보 external 전송, production deploy, DB migration, cloud storage mass deletion, IAM/repo 권한 변경, shared infra 수정, force delete, force push main
- **Classifier allowing** 예: 로컬 파일 작업, lock file dependency 설치, `.env` → matching API 전송, read-only HTTP, 생성한 branch push, sandbox network
- **Fallback**: 3회 연속 거부 또는 20회 총 거부 → 다시 prompt

### 5. `dontAsk`

- Fully non-interactive
- Auto-approve: `permissions.allow` rules 만
- Auto-deny: explicit `ask` rules 도 거부
- 사용처: CI, locked-down script

### 6. `bypassPermissions` ⚠️

- 모든 prompt 스킵 (protected paths 제외)
- **Protected paths (여전히 prompt)**:
  - `.git`, `.vscode`, `.idea`, `.husky`
  - `.claude` (except `.claude/commands|agents|skills|worktrees`)
- Write 무조건: `.gitconfig`, `.gitmodules`, `.bashrc`, `.zshrc` 등
- 주의: **isolated container/VM only**
- CLI: `--permission-mode bypassPermissions` 또는 `--dangerously-skip-permissions`
- Disable: managed `permissions.disableBypassPermissionsMode: "disable"`

## `--allowedTools` / `--disallowedTools`

### CLI 예

```bash
claude --allowedTools "Bash(npm run *)" --allowedTools "Read" --disallowedTools "Bash(rm *)"
```

### Tool 이름

- Simple: `Bash`, `Read`, `Edit`, `Write`, `WebFetch`, `Grep`
- MCP: `mcp__server__tool`
- Agent: `Agent(AgentName)`

### Bash 필터

- Exact: `Bash(npm run build)`
- Prefix: `Bash(npm *)`
- Wildcard: `Bash(npm run test *)`
- Pattern: `Bash(git * main)`

### 경로 필터

- Project relative: `Edit(/src/**/*.ts)`
- CWD relative: `Read(src/*.json)`
- Home: `Read(~/.zshrc)`
- Absolute: `Read(//Users/alice/file)`
- Gitignore patterns: `*`, `**`, `[abc]`

### WebFetch

- Domain: `WebFetch(domain:example.com)`

### Agent

- `Agent(Explore)`, `Agent(my-custom-agent)`

## `--allowedTools` vs `--tools`

### `--allowedTools`

- allow rules **추가** (설정과 merge)
- Bash 세부 필터 지원
- permission rule 문법

### `--tools` (`claude --help` 에 존재)

- **사용 가능 도구 목록 제한**: `""` (전부 비활성), `default` (전부), 특정 목록 (`Bash,Edit,Read`)
- 세트 기반 (필터 문법 아님)
- `--allowedTools` 와는 다른 레이어 — `--tools` 로 사용 가능 세트를 정의, `--allowedTools` 로 승인 정책을 정의

**⚠️ v0.3 실험**: 두 플래그의 상호작용을 `notes/v0.3-experiments/exp-01-echo.md` 에서 확인.

## `--dangerously-skip-permissions`

- 동의어: `--permission-mode bypassPermissions`
- Behavior: 모든 prompt 제거, protected paths 는 여전히 prompt

## settings.json Permission 설정

```json
{
  "permissions": {
    "defaultMode": "default|acceptEdits|plan|auto|dontAsk|bypassPermissions",
    "allow": [
      "Bash(npm run *)",
      "Bash(git commit *)",
      "Read",
      "Edit(/src/**)"
    ],
    "ask": [ "Bash(curl *)" ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force *)"
    ],
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable"
  }
}
```

### Rule Matching Precedence

1. **Deny** → 첫 match 시 block 즉시
2. **Ask** → 첫 match 시 prompt
3. **Allow** → 첫 match 시 auto-approve

### Path Rule 문법

- Absolute: `//Users/alice/secrets/**`
- Home: `~/Documents/*.pdf`
- Project: `/src/**/*.ts`
- CWD: `*.env`, `./path`
- Gitignore: `*`, `**`

### Wildcard Spaces

- `Bash(ls *)` — word boundary enforce. `ls -la` match, `lsof` no match
- `Bash(ls*)` — no boundary. 둘 다 match

### Compound Commands

- `git status && npm test` → 각 subcommand 별 rule
- `cd /dir && npm test` → `Read(/dir)` + npm rule

## `-p` (print) 모드 동작

```bash
claude -p "fix this bug"
```

| Mode | 동작 |
|---|---|
| `default` | prompt 불가 → permission 거부, session 종료 |
| `plan` | prompt 불가 → read-only 실행 |
| `auto` | classifier 사용 (prompt 없음) |
| `dontAsk` | pre-approved 만 실행 |
| `bypassPermissions` | skip all (protected 제외) |

**중요**: `-p` 모드에서 `PermissionRequest` hook 은 **fire 안 함**. `PreToolUse` hook 사용.

### 승인 방식 (`-p` 모드)

- `PreToolUse` hook 의 `permissionDecision: "allow"`
- `--allowedTools` flag
- `permissions.allow` settings

## Managed Settings

- `allowManagedPermissionRulesOnly: true` → user/project rule 무시
- `permissions.disableBypassPermissionsMode: "disable"` → bypass 불가
- `permissions.disableAutoMode: "disable"` → auto mode 불가
- **Managed deny** → user allow 로 override 불가

## Permission Modes Cycle (`Shift+Tab`)

기본:
```
default → acceptEdits → plan → default
```

CLI flag 로 확장:
- `--permission-mode bypassPermissions` / `--allow-dangerously-skip-permissions`
- `--enable-auto-mode`

## Auto Mode Classifier 설정

### 위치

- User: `~/.claude/settings.json` 의 `autoMode`
- Project: `.claude/settings.local.json`
- Managed: managed settings

### 필드

```json
{
  "autoMode": {
    "environment": ["prose descriptions of trusted infrastructure"],
    "allow": ["prose descriptions of safe actions"],
    "soft_deny": ["prose descriptions of blocked actions"]
  }
}
```

### 조회

```bash
claude auto-mode defaults
claude auto-mode config
claude auto-mode critique
```

## Protected Paths

**쓰기 시 항상 prompt (모든 mode)**:

Directories:
- `.git`
- `.vscode`, `.idea`, `.husky`
- `.claude` (except `.claude/commands|agents|skills|worktrees`)

Files:
- `.gitconfig`, `.gitmodules`
- `.bashrc`, `.bash_profile`, `.zshrc`, `.zprofile`, `.profile`
- `.ripgreprc`
- `.mcp.json`, `.claude.json`

Bypass 에서도 예외 아님.

## Additional Directories

```bash
claude --add-dir /path/to/additional
# 세션 중:
/add-dir /path
```

Settings:
```json
{ "additionalDirectories": ["/path1", "/path2"] }
```

### 발견 범위

- `.claude/skills/` → yes (live reload)
- `.claude/settings.json` (enabledPlugins, extraKnownMarketplaces) → yes
- `.claude/rules/`, CLAUDE.md → env `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 필요
- subagents/commands/hooks/LSP → no (parent project 만)

## Settings Precedence

1. Managed (override 불가)
2. CLI args (`--permission-mode`, `--allowedTools`, `--disallowedTools`)
3. `.claude/settings.local.json`
4. `.claude/settings.json`
5. `~/.claude/settings.json`

## Sandboxing 관계

두 계층:
- **Permissions**: 어떤 도구 쓸지 (tool-level)
- **Sandboxing**: Bash 의 FS/network 범위 제한 (OS-level)

- `autoAllowBashIfSandboxed: true` (기본): sandboxed Bash 는 prompt 없음
- Filesystem restrict: sandbox deny rule (permission 과 별도)
- Network restrict: WebFetch permission + sandbox `allowedDomains`

## moomoo-ax 관점의 함의

- **`-p` 모드에서 `default` 는 실질적으로 모든 tool 거부** → v0.1/v0.2 의 `subprocess.run(["claude", "-p", ...])` 가 tool 없이 돈 이유의 일부. **`--permission-mode acceptEdits` 또는 `--permission-mode bypassPermissions` + `--allowedTools` 조합이 필요**.
- **`PreToolUse` hook 에서 `permissionDecision: allow`** → levelup loop 가 자식 세션의 tool 사용을 프로그래매틱으로 승인하는 경로. **하이브리드 Path A 의 안전망**.
- **Protected paths 는 `bypassPermissions` 에서도 prompt** → 자동화 세션이 `.git`, `.claude` 에 쓰려 하면 자동 실패. labs 작업은 `.claude` 밖에서 해야 한다.
- **`dontAsk` + `allow` rules 명시** → CI 스타일의 완전 무개입 운영. levelup loop 의 타겟 mode 후보.

---

**출처**:
- https://code.claude.com/docs/en/permissions.md
- https://code.claude.com/docs/en/permission-modes.md
- https://code.claude.com/docs/en/hooks-guide.md
