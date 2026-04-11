# Claude Code 스킬(Skill) 규약

> v0.3 Phase 0 리서치 산출물. 출처: claude-code-guide 에이전트 조사 (공식 docs 기반).

## 개요

스킬(Skill)은 Claude Code에서 재사용 가능한 지식과 절차를 확장하는 메커니즘입니다. 스킬은 `SKILL.md` 파일로 정의되며, YAML frontmatter와 markdown 본문으로 구성됩니다.

## 파일 위치 및 범위

| 위치 | 경로 | 범위 | 우선순위 |
|------|------|------|---------|
| 엔터프라이즈 | (관리 설정) | 조직 전체 | 1순위 (최상) |
| 개인 | `~/.claude/skills/<skill-name>/SKILL.md` | 모든 프로젝트 | 2순위 |
| 프로젝트 | `.claude/skills/<skill-name>/SKILL.md` | 현재 프로젝트만 | 3순위 |
| 플러그인 | `<plugin>/skills/<skill-name>/SKILL.md` | 플러그인 활성화 시 | 플러그인 네임스페이스 (`plugin-name:skill-name`) |

- 같은 이름의 스킬이 여러 레벨에 존재할 경우, 우선순위가 높은 것이 우선.
- 스킬과 동명의 `.claude/commands/` 파일이 있으면 **스킬이 우선**.
- Nested Directory Discovery: 하위 디렉토리에서 작업 시 상위 경로의 `.claude/skills/` 도 자동 발견 (monorepo 지원).

## SKILL.md 구조

### 파일 구성

```yaml
---
name: skill-name
description: What this skill does and when to use it
---

# 스킬 본문 (Markdown)
```

### Frontmatter 필드 (전체 참조)

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | 아니오 | 표시 이름. 생략 시 디렉토리명. 소문자/숫자/하이픈 (최대 64자). `/` 명령어로 변환됨. |
| `description` | 권장 | 스킬 용도 및 사용 시기. Claude 자동 로드 결정에 사용. 250자 이상은 잘림. |
| `argument-hint` | 아니오 | 자동완성 시 인자 힌트. 예: `[issue-number]` |
| `disable-model-invocation` | 아니오 | `true` → 사용자만 호출 (Claude 자동 매칭 금지). 기본 `false`. |
| `user-invocable` | 아니오 | `false` → `/` 메뉴에서 숨김 (Claude만 호출). 기본 `true`. |
| `allowed-tools` | 아니오 | 스킬 활성 중 권한 요청 없이 사용 가능한 도구. 공백 구분 또는 YAML 리스트. 예: `Bash(git *) Read Grep` |
| `model` | 아니오 | 스킬 활성 중 사용할 모델 지정 |
| `effort` | 아니오 | effort level 오버라이드: `low`/`medium`/`high`/`max` (max는 Opus 4.6만) |
| `context` | 아니오 | `fork` → 별도 subagent 컨텍스트에서 실행 |
| `agent` | 아니오 | `context: fork` 일 때 실행할 subagent 유형 (`Explore`/`Plan`/`general-purpose`/커스텀) |
| `hooks` | 아니오 | 스킬 라이프사이클 스코프 hooks |
| `paths` | 아니오 | 스킬 활성화 제한 glob 패턴 |
| `shell` | 아니오 | `bash` (기본) 또는 `powershell` |

### 문자열 치환 (String Substitutions)

| 변수 | 설명 |
|------|------|
| `$ARGUMENTS` | 호출 시 전달된 모든 인자. 본문에 없으면 자동으로 끝에 추가 |
| `$ARGUMENTS[N]` | N번째 인자 (0-indexed) |
| `$N` | `$ARGUMENTS[N]` 축약형 |
| `${CLAUDE_SESSION_ID}` | 현재 세션 ID |
| `${CLAUDE_SKILL_DIR}` | 스킬 `SKILL.md` 디렉토리 (플러그인 스킬은 스킬 서브디렉토리) |

예:
```yaml
---
name: migrate-component
description: Migrate a component between frameworks
---

Migrate the $0 component from $1 to $2.
```
호출: `/migrate-component SearchBar React Vue`

### 본문 Markdown 규약

#### 동적 컨텍스트 주입 (Shell Commands)

`` !`<command>` `` 문법으로 셸 명령어를 실행하고 결과를 삽입:

```markdown
## Environment
- Node version: !`node --version`
- Git status: !`git status --short`
```

실행 시점: 스킬 콘텐츠가 Claude에 **전송되기 전**에 명령어가 실행되고 결과가 플레이스홀더를 대체.

다중 라인 명령어는 펜스드 코드 블록:

````markdown
```!
npm list
git log --oneline -5
```
````

**비활성화**: `settings.json` 의 `disableSkillShellExecution: true` → 모든 명령어가 `[shell command execution disabled by policy]` 로 치환 (bundled 스킬 제외).

#### 파일 참조

같은 디렉토리 내 다른 파일 참조 가능 (자동 주입 아님 — Claude 가 Read tool 로 로드):

```markdown
자세한 내용은 [reference.md](reference.md) 참조.
```

### 지원 디렉토리 구조

```
my-skill/
├── SKILL.md                 # 필수
├── reference.md             # 선택. Claude 가 필요시 Read
├── examples.md              # 선택
└── scripts/
    └── helper.py            # 선택. Bash tool 로 실행
```

## 사용자 호출 방식

- **수동**: `/skill-name arg1 arg2` → `$0=arg1`, `$1=arg2`
- **자동** (auto invocation): Claude 가 대화 컨텍스트와 description 매칭하여 로드. `disable-model-invocation: false` 필요.
- **Skill Tool** (프로그래매틱): tool use 중 `Skill(skill-name)` 또는 `Skill(prefix-*)`.

## 스킬 라이프사이클

### 로드 타이밍

- **Description only**: 설명만 항상 컨텍스트에 로드 (사용 판단용)
- **Full content**: 호출 시에만 본문 전체 로드
- **Re-attachment**: auto-compaction 후 최근 호출 스킬부터 최대 25,000 토큰 예산 내에서 재첨부

### Context 영속성

호출된 스킬은 세션 동안 컨텍스트에 남아있음. 파일 재읽기 없음 — 호출 시점에 고정. 큰 스킬/많은 호출 후 컴팩션 시 재호출로 복원.

## Subagent 컨텍스트에서의 실행

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
allowed-tools: Glob Grep Read
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze code
3. Return structured findings
```

실행 흐름:
1. 새 격리 컨텍스트 생성
2. `agent` 지정 subagent 에서 실행 (기본: `general-purpose`)
3. Subagent 도구 제약 자동 적용
4. 결과 요약만 반환

## `--add-dir` 와의 상호작용

`--add-dir` 로 추가된 디렉토리의 `.claude/skills/` 는 자동 발견되며 live change detection 지원. **단, 다른 `.claude/` 설정(subagent/command) 은 발견되지 않음.**

## 알려진 제약

- `description` 표시 길이: 250자 자르임
- 컨텍스트 예산: 약 8,000자 (또는 컨텍스트 1% 동적 할당)
- 환경변수 `SLASH_COMMAND_TOOL_CHAR_BUDGET` 로 상향 가능
- 앞쪽(front-load) 키워드 배치가 매칭 정확도 향상

## 버전 변동 (v2.1.63+)

`.claude/commands/` 파일은 계속 작동하지만, 같은 이름의 스킬이 있으면 **스킬이 우선**. 점진적 마이그레이션 권장.

## moomoo-ax 관점의 핵심 함의

- `allowed-tools` 로 `Bash` 포함 → SKILL.md 에서 `[run: scripts/check_r_len.py]` 같은 deterministic 스크립트 호출이 **자연어 해석 없이** 가능. 이것이 **Progressive Codification** 의 실체.
- `context: fork` + `agent: Explore` → 스킬 자체가 subagent 를 띄워 컨텍스트 격리 가능. levelup iteration 의 "각 iter 를 격리된 서브컨텍스트로" 구조에 직결.
- `$ARGUMENTS` 바인딩 → 스킬을 entry point 로 쓰면서 Python 하네스가 인자 주입 가능.

---

**출처**:
- https://code.claude.com/docs/en/skills.md (main)
- https://code.claude.com/docs/en/commands.md (commands → skills 통합 섹션)
