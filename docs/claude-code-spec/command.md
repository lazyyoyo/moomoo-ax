# Claude Code 명령어(Command) 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사.

## 개요

Slash command (`/`) 는 Claude Code 세션을 제어하는 빠른 방법. 두 가지 유형:

1. **Built-in commands**: 코드로 구현된 고정 동작 (`/help`, `/config`, `/clear`)
2. **Bundled skills**: prompt 기반 스킬 (`/debug`, `/simplify`, `/batch`)

사용자 정의 명령어는 **스킬 시스템과 통합**됨. `.claude/commands/` 는 호환 유지지만 스킬로 마이그레이션 권장.

## 파일 위치

### 레거시 (`.claude/commands/`)

```
.claude/commands/
├── deploy.md        # /deploy
├── commit.md
└── build.md
```

**상태**: 호환성 유지. 스킬 시스템 선호.

### 현재 방식 (스킬)

```yaml
---
name: deploy
description: Deploy the application to production
disable-model-invocation: true    # 사용자 호출만
---

Deploy $ARGUMENTS to production:
1. Run tests
2. Build
3. Push to target
```

`~/.claude/skills/deploy/SKILL.md` → `/deploy` 명령어 생성.

## Frontmatter 필드

`.claude/commands/` 파일도 스킬과 **동일** frontmatter 지원:

| 필드 | 설명 |
|------|------|
| `name` | 명령어명. 생략 시 파일명 |
| `description` | 자동 호출 여부 결정 |
| `argument-hint` | CLI 자동완성 표시 |
| `disable-model-invocation` | `true` → 사용자만 |
| `user-invocable` | `false` → Claude 만 |
| `allowed-tools` | 권한 없이 사용 가능 도구 |
| `model` | 실행 모델 |
| `context` | `fork` → subagent |
| `agent` | fork 시 subagent 유형 |
| `effort` | effort level |
| `hooks` | 라이프사이클 hooks |
| `paths` | glob 제한 |
| `shell` | `bash`/`powershell` |

## 인자 바인딩

| 문법 | 설명 |
|------|------|
| `$ARGUMENTS` | 전체 인자 문자열 |
| `$ARGUMENTS[N]` | N번째 인자 (0-indexed) |
| `$N` | `$ARGUMENTS[N]` 축약 |
| `${CLAUDE_SESSION_ID}` | 세션 ID |

- 인자 미지정 시 자동으로 끝에 `ARGUMENTS: <input>` 추가
- 멀티워드 인자는 따옴표: `/my-skill "hello world" second`

예:
```yaml
---
name: fix-issue
description: Fix a GitHub issue
disable-model-invocation: true
---

Fix GitHub issue $ARGUMENTS following our standards:

1. Read the issue
2. Implement the fix
3. Write tests
4. Create commit
```

`/fix-issue 123` → "Fix GitHub issue 123..."

## Bash 실행 및 파일 참조

### 동적 커맨드 실행

```yaml
---
name: pr-summary
description: Summarize pull request changes
context: fork
---

## PR Context
- Changed files: !`gh pr diff --name-only`
- PR comments: !`gh pr view --comments`

## Your task
Summarize this PR...
```

### 파일 참조

```markdown
See [guide.md](guide.md) for detailed steps.
```

## Skill vs Command

| 측면 | Skill | Command (레거시) |
|------|-------|--------|
| 저장 위치 | `.claude/skills/`, `~/.claude/skills/` | `.claude/commands/` |
| 우선순위 | **같은 이름일 때 우선** | skill 에 양보 |
| 기능 | 발견, 자동 로드, subagent context | 고정 슬래시 명령어 |
| 진화 | 활발 | deprecated |

## Bundled Skills (코드 구현)

| 명령어 | 용도 |
|--------|------|
| `/debug` | 디버그 로깅 활성화 |
| `/simplify` | 코드 단순화/최적화 |
| `/batch` | 병렬 작업 분산 |
| `/loop` | 반복 프롬프트 실행 |
| `/claude-api` | Claude API 참고자료 |

## 허용 도구 설정

```yaml
allowed-tools: Bash(git *) Read Grep
```

또는 YAML 리스트:
```yaml
allowed-tools:
  - Bash(git *)
  - Read
  - Grep
  - Skill(deploy)          # 정확 매칭
  - Skill(fix-*)           # prefix 매칭
```

## Built-in Commands (참고)

| 명령어 | 목적 |
|--------|------|
| `/help` | 도움말 |
| `/config` | 설정 |
| `/clear` | 히스토리 초기화 |
| `/model [model]` | 모델 선택 |
| `/effort [level]` | effort level |
| `/permissions` | 권한 관리 |
| `/agents` | subagent 설정 |
| `/compact [instructions]` | 대화 요약 |
| `/cost` | 토큰 사용량 |
| `/status` | 상태 |

## 호환성 및 마이그레이션

```bash
# Before
.claude/commands/deploy.md

# After
.claude/skills/deploy/SKILL.md
```

동일 frontmatter 지원이므로 콘텐츠 변경 불필요.

## moomoo-ax 관점의 함의

- **team-ax 는 `.claude-plugin/skills/` 트리로 작성 → 자동으로 `/team-ax:ax-implement` 같은 슬래시 명령어 생성됨.** 별도 commands/ 작성 불필요.
- `disable-model-invocation: true` + `user-invocable: true` → levelup loop 가 **명시 호출만** 허용하도록 잠그면 Claude 자동 매칭 방지 (재현성 확보).

---

**출처**:
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/commands.md
