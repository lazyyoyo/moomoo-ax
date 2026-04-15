# AGENTS.md

team-ax 플러그인의 활성 스킬·에이전트와 호출 규약. 정본은 `plugin/skills/`·`plugin/agents/` 기준.

## 활성 스킬

| 스킬 | 위치 | 책임 | v0.1 상태 |
|---|---|---|---|
| `ax-define` | `plugin/skills/ax-define/` | 제품 버전 스코프 결정 (Phase A) + 스펙 in-place 갱신 사이클 (Phase C) | 구현 |
| `ax-review` | `plugin/skills/ax-review/` | 범용 리뷰 (codex 위임) — `doc` / `code` / `pr` | `doc`만 구현. `code`/`pr`는 stub |

## 활성 에이전트 (Claude 서브에이전트)

| 에이전트 | 위치 | 담당 Phase |
|---|---|---|
| `product-owner` | `plugin/agents/product-owner.md` | `ax-define` Phase A (1~6단계) — intake / 인터뷰 / JTBD / Story Map / SLC / 버전명 결정 |
| `analyst` | `plugin/agents/analyst.md` | `ax-define` Phase C plan + write (9·10단계) — §수정 계획 / specs in-place 갱신 / BACKLOG 정리 / §수정 로그 |

> Phase C review(11단계)는 별도 `ax-review doc` 스킬(codex 위임) 담당.

## 원본과 로컬 설치

- 원본 저장소: 이 repo
- 로컬 설치 스크립트: `plugin/scripts/install-local-skills.sh`
- 스크립트는 `ax-review`를 Codex 로컬(`~/.codex/skills/ax-review/`)과 Claude 플러그인 캐시에 동기화한다.

```bash
bash plugin/scripts/install-local-skills.sh
```

> `ax-define`은 Codex 위임 대상이 아니므로 동기화 목록에 없다. Claude 플러그인으로만 호출.

## 사용 방식 1 — Claude/Codex가 직접 스킬 사용

### Claude

team-ax 플러그인 설치 후 슬래시 명령 또는 자연어로 호출.

```text
/team-ax:ax-define
/team-ax:ax-review doc versions/undefined/scope.md
```

자연어로 `ax-define` 또는 `ax-review` 명시도 가능.

### Codex

Codex에서는 `$ax-review`로 직접 호출 (설치 스크립트 실행 후).

```text
$ax-review doc versions/undefined/scope.md
$ax-review code <대상>   # v0.1 stub — NOT_IMPLEMENTED 한 줄 출력 후 중단
$ax-review pr <번호>     # v0.1 stub — NOT_IMPLEMENTED 한 줄 출력 후 중단
```

## 사용 방식 2 — Claude가 Codex에게 위임

`ax-define`의 Phase C review는 Claude(`ax-define` SKILL.md)가 Bash 도구로 `codex exec`를 실행해 `ax-review`에 위임한다.

```bash
# doc 리뷰 (read-only — codex 기본 sandbox)
codex exec '$ax-review doc versions/undefined/scope.md'

# 후속 스프린트 (참고)
# codex exec --full-auto '$ax-review code <대상>'   # v0.2+ 예정
# codex exec -s workspace-read '$ax-review pr <번호>' # v0.2+ 예정
```

> `codex exec` 기본은 `approval: never` + `sandbox: read-only`. doc 리뷰는 read-only로 충분하므로 추가 플래그 불필요. `pr` 타입은 `gh pr diff` 호출이 필요해 후속 스프린트에서 sandbox 상향(`workspace-read`) 정책을 함께 결정한다.

## Codex sandbox 가이드 (참고)

| 타입 | sandbox | 비고 |
|---|---|---|
| `doc` | `read-only` | 대상 문서 + diff 읽기만 |
| `code` | `read-only` | 테스트 실행이 필요해지면 v0.2+에서 `workspace-read` |
| `pr` | `workspace-read` | `gh pr diff` 등 CLI 호출 필요. v0.2+ |

## 운영 원칙

- 정본은 `plugin/skills/`·`plugin/agents/` 기준. Codex 사본은 동기화 산물.
- 스킬·에이전트 갱신 후에는 `bash plugin/scripts/install-local-skills.sh`를 다시 실행한다.
- 일반 이름(`review`, `define`)은 사용하지 않는다. 항상 `ax-*` 접두사.
- Phase A → Phase C 흐름에서 review는 단일 진입점(`$ax-review doc`)으로 통일. 향후 모든 리뷰가 이 스킬로 모이도록 단일 소스 유지.
