# docs/claude-code-spec

> moomoo-ax v0.3 Phase 0 리서치의 **영구 레퍼런스**.
> Claude Code CLI / skill / plugin / subagent / hook / MCP / permissions 의 공식 규약 정리.

## 왜 이 디렉토리?

v0.2 E/F 에서 두 구조 결함이 실증됨:

1. **자연어 압축 ≠ codification** (SKILL.md 의 자연어 rule 은 매번 LLM 이 해석)
2. **`claude -p` one-shot ≠ Claude Code tool loop** (tool/MCP/Agent/Skill 모두 원천 접근 불가)

v0.3 재설계의 모양이 **Claude Code CLI 의 실 기능/제약** 에 달려 있어, 가설을 먼저 검증해야 한다.
이 디렉토리는 그 검증의 기반 자료 — **"Claude Code 가 공식적으로 무엇을 허용하는가"** 를 한 곳에 모은다.

## 파일

| 파일 | 주제 |
|---|---|
| [cli.md](cli.md) | `claude` 전체 플래그 & subcommand (`v2.1.101`) |
| [skill.md](skill.md) | SKILL.md frontmatter, 본문 규약, 호출/라이프사이클 |
| [command.md](command.md) | slash command 규약, skill 과의 차이 |
| [agent.md](agent.md) | subagent 정의, 도구 화이트리스트, `--agents` JSON, worktree isolation |
| [plugin.md](plugin.md) | plugin.json 스키마, `--plugin-dir`, 설치 스코프 |
| [hook.md](hook.md) | hook event 종류, 입출력, blocking 메커니즘 |
| [mcp.md](mcp.md) | MCP 설정, plugin 내장 MCP, subprocess 상속 |
| [permissions.md](permissions.md) | `--permission-mode`, allow/deny rules, `-p` 모드 동작 |
| [references.md](references.md) | 주제별 cross-ref 인덱스 |

## 수집 방법

- 주 참조: `claude-code-guide` 플러그인 에이전트 (공식 docs + 플러그인 예시)
- CLI 소스: `claude --help` (v2.1.101, 2026-04-11 캡처)
- 보조: WebFetch 로 https://code.claude.com 공식 문서

## 상태 (2026-04-11)

- ✅ 9개 파일 초안 작성 완료
- ⏳ 실험 6개 (`notes/v0.3-experiments/exp-01 ~ exp-06`) 결과로 "확인 필요" 항목 보완 예정
- ⏳ `notes/2026-04-12-v0.3-feasibility.md` — Path A / Path B 판정 리포트

## 관련 문서

- [notes/2026-04-11-v0.3-research-scope.md](../../notes/2026-04-11-v0.3-research-scope.md) — 리서치 전체 스코프
- [notes/2026-04-11-v0.2-e-f-codification-insight.md](../../notes/2026-04-11-v0.2-e-f-codification-insight.md) — v0.2 마감 회고 (이 리서치의 배경)
- [HANDOFF.md](../../HANDOFF.md) — 세션 인계
- [PROJECT_BRIEF.md](../../PROJECT_BRIEF.md) — 프로젝트 SSOT
