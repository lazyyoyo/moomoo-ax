# Claude Code Subagent 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사.

## 개요

Subagent 는 특화 작업을 독립 컨텍스트에서 처리하여 메인 대화를 오염시키지 않는 AI 어시스턴트. 각 subagent 는 독립 컨텍스트 + 커스텀 시스템 프롬프트 + 특화 도구 접근 + 독립 권한 설정.

**Subagent vs Agent Teams**:
- **Subagent**: 단일 세션 내 side task 분리
- **Agent Teams**: 여러 독립 세션이 협력하며 실시간 메시징

## 파일 위치

| 위치 | 경로 | 범위 | 우선순위 |
|------|------|------|---------|
| 관리(managed) | `.claude/agents/` (managed settings) | 조직 전체 | 1순위 |
| 프로젝트 | `.claude/agents/<name>.md` | 현재 프로젝트 | 2순위 |
| 개인 | `~/.claude/agents/<name>.md` | 모든 프로젝트 | 3순위 |
| 플러그인 | `<plugin>/.claude/agents/<name>.md` 또는 `<plugin>/agents/<name>.md` | 플러그인 활성화 시 | `plugin-name:agent-name` |

## 파일 구조

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools:
  - Read
  - Grep
  - Bash(git *)
model: claude-opus-4-1
---

You are an expert code reviewer. When invoked, analyze the provided code
for quality, security, and maintainability issues. Provide constructive feedback.
```

### Frontmatter 필드 (완전 참조)

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | string | 표시명. 소문자/숫자/하이픈 (최대 64자) |
| `description` | string | 용도. 자동 delegation 기준 |
| `tools` | list/string | **화이트리스트**. 부모 세션 도구 상속 아님. 명시된 도구만 사용 |
| `disallowedTools` | list/string | 명시적 차단 |
| `model` | string | 모델 지정. 생략 시 부모 세션 모델 상속 |
| `permissionMode` | string | `ask`(기본)/`auto`/`bypassPermissions`. 부모가 bypassPermissions 면 override 불가 |
| `mcpServers` | list/object | 이 subagent 전용 MCP 서버 설정 |
| `hooks` | object | 라이프사이클 hooks (pre-execution, post-execution) |
| `maxTurns` | int | 최대 턴 수 |
| `skills` | list | 프리로드할 스킬 (시스템 프롬프트에 주입) |
| `initialPrompt` | string | 초기 사용자 입력 (프로그래매틱 호출용) |
| `memory` | string | 메모리 파일 경로 |
| `effort` | string | `low`/`medium`/`high`/`max` |
| `background` | boolean | `true` → 백그라운드 실행 (결과 회신 없음) |
| `isolation` | string | `worktree` → git worktree 격리 |
| `color` | string | 프롬프트 바 색상 |

### Description 의 역할

1. **자동 delegation**: Claude 가 description 매칭으로 자동 위임
2. **컨텍스트 로드**: description 만 메인 세션에 로드. 본문은 호출 시에만 로드
3. **키워드 매칭**: 앞부분 키워드 정확도 향상

예: `"Debugging specialist for errors, test failures, and unexpected behavior. Use proactively when encountering any issues."`

## 호출 방법

### 1. 자동 위임

Claude 가 description 매칭으로 자동 호출.

### 2. @ 멘션

```
@code-reviewer 이 코드 리뷰해줄래?
```

### 3. Agent Tool (프로그래매틱)

```yaml
tools:
  - Agent(code-reviewer)      # 특정 subagent 만
  - Agent(debugger)
  - Agent(*)                  # 모든 subagent
```

### 4. CLI Flag (`--agent`)

```bash
claude --agent code-reviewer
claude --agent plugin-name:agent-name
```

### 5. Agent Teams 통합

```
/team-spawn code-reviewer-type --agent code-reviewer
```

## `--agents` JSON Flag

프로그래매틱 정의:

```bash
claude --agents '[{
  "name": "researcher",
  "description": "Dedicated research agent",
  "prompt": "You are a research specialist...",
  "tools": ["Glob", "Grep", "Read", "WebSearch"],
  "model": "claude-opus-4-1"
}]'
```

**JSON 필드**: frontmatter 와 동일 + `prompt` (본문 상응).

## 도구 접근 (Tools Access)

### 상속 메커니즘

**Subagent 는 부모 세션 도구를 상속하지 않음.** `tools` 필드에 명시된 도구만 사용 가능.

```yaml
---
name: db-reader
description: Execute read-only database queries
tools:
  - Bash(psql *)
  - Read
disallowedTools:
  - Bash(psql drop *)
---
```

### 권한 상속

| `permissionMode` 설정 | 부모 모드 | 동작 |
|---|---|---|
| `ask` (기본) | any | subagent 설정 사용 |
| `auto` | `ask` | subagent auto |
| `auto` | `auto` | 부모 auto 분류기 상속 |
| `auto` | `bypassPermissions` | 불가 (부모 강제) |
| `bypassPermissions` | any | **부모가 강제** (override 불가) |

**주의**: `.git`, `.claude`, `.vscode` 는 항상 확인 프롬프트.

## MCP 서버 설정

```yaml
---
name: api-developer
mcpServers:
  - name: my-api
    command: bash
    args:
      - -c
      - npx @apihost/mcp
    env:
      API_KEY: "${process.env.API_KEY}"
---
```

이미 연결된 서버 참조도 가능:
```yaml
mcpServers:
  - name: existing-server    # 부모 세션 서버 재사용
```

## 스킬 프리로드

```yaml
---
name: api-developer
description: API 개발 전문가
skills:
  - api-conventions
  - error-handling
---
```

Subagent 시작 시 해당 스킬 콘텐츠가 시스템 프롬프트에 주입.

**`context: fork` (스킬) vs `skills` (subagent) 차이**:
- `context: fork`: 스킬이 task, subagent 는 수단
- `skills` field: subagent 가 task, 스킬은 사전 지식

## Subagent 내 Hooks

```yaml
hooks:
  - trigger: pre-execution
    run: echo "Starting review..."
  - trigger: post-execution
    run: echo "Review complete"
```

`Stop` hooks 는 자동으로 `SubagentStop` 이벤트로 변환.

## Subagent 간 통신

중첩 호출 가능:

```yaml
---
name: coordinator
tools:
  - Agent(code-reviewer)
  - Agent(debugger)
  - Agent(db-reader)
---
```

각 subagent 독립 컨텍스트에서 실행, 결과만 상위 반환.

## Context 및 격리

### 워킹 디렉토리

- 부모 세션 워킹 디렉토리에서 시작
- Bash/PowerShell 의 `cd` 변경은 subagent 내에서만 유지 (부모 미영향)

### Worktree Isolation

```yaml
---
name: feature-builder
isolation: worktree
---
```

- 부모 repo 의 git worktree 자동 생성
- 변경사항 부모 repo 영향 없음

## 플러그인 Subagent 제약

| 필드 | 플러그인 | 프로젝트/개인 |
|------|---------|-----------|
| `hooks` | ❌ | ✅ |
| `mcpServers` | ❌ | ✅ |
| `permissionMode` | ❌ | ✅ |

우회: 플러그인 subagent 를 `.claude/agents/` 로 복사.

## 모델 해석 우선순위

1. 호출 시점 `model` 파라미터 (프로그래매틱)
2. 부모 세션 현재 모델
3. Subagent 정의 `model` frontmatter

## 버전 변경 (v2.1.63)

- Task tool → **Agent tool** 로 rename (Task 별칭 유지)
- `Task(...)` 는 여전히 작동하지만 `Agent(...)` 로 마이그레이션 권장

## Context Memory

- Subagent 는 부모 세션의 `CLAUDE.md` 자동 로드
- 부모 대화 히스토리는 로드 **안 함** (격리)

## moomoo-ax 관점의 함의

- **Subagent = 격리 컨텍스트 + 도구 화이트리스트 + 결과 요약만 반환** → levelup loop 의 "각 iter" 를 subagent 로 래핑하면 자연스럽게 컨텍스트 폭발 방지.
- `isolation: worktree` → labs/ax-implement 의 iteration 이 실제 repo 수정 없이 격리 가능. 지금 파이썬에서 수동으로 diff 받아 적용하는 로직 대체 가능.
- `--agents` JSON flag → Python 하네스가 각 iter 를 ad-hoc subagent 로 정의해서 실행 가능. **하이브리드 Path A 의 핵심 빌딩 블록**.
- 플러그인 subagent 는 hooks/mcpServers/permissionMode 제약 → team-ax 내부 구조 설계 시 주의.

---

**출처**:
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/commands.md (`/agents`)
- https://code.claude.com/docs/en/agent-sdk/subagents.md
