# Claude Code Spec — 참조 요약

> v0.3 Phase 0 리서치 산출물.
> 이 문서는 나머지 spec 파일들이 서로를 어떻게 참조하는지, 주요 cross-cut 토픽이 어디에 있는지 인덱스한다.

## 파일 지도

| 파일 | 주제 | 핵심 독자 |
|---|---|---|
| [README.md](README.md) | 디렉토리 목적, 상태 | 다음 세션 진입점 |
| [skill.md](skill.md) | SKILL.md frontmatter, 본문 규약, 호출/라이프사이클 | team-ax 스킬 작성자 |
| [command.md](command.md) | slash command 규약, skill 과의 차이 | 레거시 호환 확인 |
| [agent.md](agent.md) | subagent 정의, tools 화이트리스트, worktree isolation | **levelup loop 설계자** |
| [plugin.md](plugin.md) | plugin.json 스키마, `--plugin-dir`, 설치 스코프 | team-ax 패키징 |
| [hook.md](hook.md) | hook event, 입출력, blocking | 자동화 안전망 |
| [mcp.md](mcp.md) | MCP 설정, subprocess 상속 | ax-qa 도구 체인 |
| [permissions.md](permissions.md) | `--permission-mode`, allow/deny rules, `-p` 모드 | 무개입 운영 모드 |
| [cli.md](cli.md) | `claude` 전체 플래그, subcommand | 하이브리드 설계 기반 |
| [references.md](references.md) | (이 문서) | 인덱스 |

## 주제별 cross-ref

### "SKILL.md 에서 Bash 스크립트를 deterministic 하게 실행하려면?"

→ [skill.md](skill.md) `allowed-tools` + 본문의 `` !`script.py` `` 또는 `[run: ...]` 패턴.
→ 관련: [hook.md](hook.md) `PostToolUse` + `if` field 로 검증 주입.
→ 관련: [permissions.md](permissions.md) `allow: ["Bash(scripts/*)"]`.

### "levelup loop iteration 을 subagent 로 래핑하려면?"

→ [agent.md](agent.md) `--agents` JSON flag 섹션.
→ [agent.md](agent.md) `isolation: worktree` 섹션.
→ 관련: [cli.md](cli.md) `--agents`, `--agent`.
→ 관련: [hook.md](hook.md) `SubagentStop` 이벤트.

### "Python 하네스가 자식 `claude` 에 team-ax 플러그인을 주입하려면?"

→ [plugin.md](plugin.md) `--plugin-dir` 섹션.
→ 관련: [cli.md](cli.md) `--plugin-dir`.
→ 실험: `notes/v0.3-experiments/exp-04-skill-load.md`.

### "자식 `claude -p` 세션에서 도구가 실제로 돌아가려면?"

→ [permissions.md](permissions.md) `-p` (print) 모드 동작 표.
→ [cli.md](cli.md) `--allowedTools` / `--permission-mode acceptEdits`.
→ 실험: `exp-01-echo`, `exp-02-stateful`.

### "Playwright / axe-core / Lighthouse 를 ax-qa 에 연결하려면?"

→ [mcp.md](mcp.md) Plugin 내장 MCP Server 섹션.
→ [mcp.md](mcp.md) Subprocess 상속 (⚠️ 미확인).
→ 실험: `exp-06-mcp`.

### "재귀적으로 `claude` 를 `claude` 안에서 호출 가능한가?"

→ [cli.md](cli.md) `--session-id` 섹션.
→ 실험: `exp-03-recursion`.

### "rubric 을 hook 으로 강제 집행하려면?"

→ [hook.md](hook.md) `Stop` / `SubagentStop` / `PostToolUse` 섹션.
→ 관련: [skill.md](skill.md) frontmatter 의 `hooks` 필드.

## 용어

| 용어 | 정의 |
|---|---|
| Skill | `.claude/skills/<name>/SKILL.md` 로 정의된 재사용 가능 절차 |
| Command | `.claude/commands/<name>.md` 로 정의된 슬래시 명령어 (레거시, 스킬로 통합) |
| Subagent | 독립 컨텍스트 + 도구 화이트리스트를 가진 side task 실행자 |
| Plugin | `plugin.json` 매니페스트 + skills/agents/hooks/mcp 번들 |
| Hook | 특정 이벤트(PreToolUse 등) 에 실행되는 외부 스크립트/HTTP/prompt/agent |
| MCP | Model Context Protocol. 외부 프로세스가 tool/resource/prompt 노출 |
| Permission mode | 도구 사용 승인 정책 (`default`/`acceptEdits`/`plan`/`auto`/`dontAsk`/`bypassPermissions`) |
| Protected paths | 모든 mode 에서 쓰기 시 prompt 하는 경로 (`.git`, `.claude` 등) |
| `--bare` | 재현성 극대화 모드. hook/plugin sync/auto-memory 스킵 |

## 상태

- 초안 작성: 2026-04-11 (v0.3 Phase 0 1일차)
- 다음 업데이트: 실험 6개 완료 후 (`exp-01` ~ `exp-06`)
- Living document: Claude Code 버전 변경 시 재검증
