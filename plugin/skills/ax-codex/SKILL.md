---
name: ax-codex
description: "team-ax의 codex 연동 스킬 동기화 관리. ax-review/ax-execute를 ~/.codex/skills/로 install/uninstall/status. ax-build가 codex 엔진 호출하기 전에 한 번 실행해 두면 됨. Use when: /ax-codex, codex skill 동기화, codex 설치, ax-execute 설치."
argument-hint: "install | uninstall | status"
---

# /ax-codex

team-ax 플러그인 스킬 중 **codex 위임 대상**(`ax-review`, `ax-execute`)을 `~/.codex/skills/`로 동기화하는 관리 스킬. `ax-status`와 같은 패턴.

> **역할 경계**
> - `ax-review` / `ax-execute` = 실제 스킬 본체 (정본은 `plugin/skills/`)
> - `ax-codex` = **동기화/상태 관리**만 담당 (본체 아님)
> - 훅으로 자동화 ❌ — 오너가 명시적으로 호출 (비용/예측 가능성 우선)

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | 서브커맨드 (`install` / `uninstall` / `status`). 인자 없이 호출 시 `status`. |
| **출력** | `~/.codex/skills/{ax-review,ax-execute}/` 생성·삭제, 구버전(`execute/`) 휴지통 이동, 상태 출력 |

## 동작 — 단일 진입점

모든 서브커맨드는 `plugin/scripts/ax-codex.sh`로 위임한다.

```bash
bash plugin/scripts/ax-codex.sh <subcommand>
```

team-ax 플러그인이 cache에 설치된 상태라면:

```bash
bash ~/.claude/plugins/cache/<owner>/team-ax/<version>/scripts/ax-codex.sh <subcommand>
```

스킬은 사용자가 `/ax-codex <subcommand>` 형태로 호출하면 위 명령을 실행해 결과를 그대로 보여준다.

## 서브커맨드

### `/ax-codex install`

`plugin/skills/{ax-review,ax-execute}/` → `~/.codex/skills/{ax-review,ax-execute}/`로 rsync 동기화. Claude 플러그인 캐시가 존재하면 함께 갱신.

**동작:**
1. `~/.codex/skills/` 없으면 생성.
2. 각 대상 스킬(`ax-review`, `ax-execute`)을 `rsync -a --delete --exclude '.DS_Store'`로 동기화.
3. **구버전 정리** — `~/.codex/skills/execute/`(rename 이전 이름)가 있으면 `mv ~/.Trash/execute.<timestamp>`로 휴지통 이동.
4. Claude 플러그인 캐시(`~/.claude/plugins/cache/<owner>/team-ax/<ver>/skills/`)가 존재하면 동일하게 갱신.
5. 설치된 경로 요약 출력.

### `/ax-codex uninstall`

`~/.codex/skills/{ax-review,ax-execute}/`를 휴지통으로 이동. Claude 플러그인 캐시는 건드리지 않음 (플러그인 재설치 시 복원되므로).

**동작:**
1. 각 대상 폴더가 존재하면 `mv ~/.Trash/<name>.<timestamp>`.
2. 없으면 skip.
3. 결과 출력.

### `/ax-codex status`

현재 동기화 상태 확인. 인자 없이 호출 시 기본 동작.

**출력:**
- codex CLI 존재 여부 (`command -v codex`)
- 대상 스킬별 상태:
  - `ax-review` ✓ synced / ✗ missing / ⚠ stale (source와 다름)
  - `ax-execute` ✓ synced / ✗ missing / ⚠ stale
- 구버전 잔재(`~/.codex/skills/execute/`) 존재 여부
- Claude 플러그인 캐시 경로 + 동기화 상태

stale 판정은 `diff -rq source target` 결과가 비어있는지로 판단.

## 가드레일

1. **`rm` 금지** — 제거는 항상 `mv ~/.Trash/<name>.<timestamp>`. (CLAUDE.md 규칙)
2. **정본 단일** — `plugin/skills/`가 정본. codex 사본은 **install로만** 갱신.
3. **수동 호출** — 자동 훅 없음. 스킬/에이전트 수정 후 `/ax-codex install` 명시적 실행.
4. **rsync 옵션 고정** — `-a --delete --exclude '.DS_Store'`. 링크 복제나 권한 변경 없음.
5. **대상 스킬 목록 고정** — 현재는 `ax-review`, `ax-execute` 둘. 확장 필요 시 이 SKILL.md와 `ax-codex.sh`의 `skills` 배열을 함께 수정.

## 참조

- `plugin/scripts/ax-codex.sh` — 실행 엔진 (install / uninstall / status)
- `../ax-review/SKILL.md` — 동기화 대상 1 (범용 리뷰, codex 위임)
- `../ax-execute/SKILL.md` — 동기화 대상 2 (코드 구현, codex 위임)
- `../ax-status/SKILL.md` — 유사 패턴(statusline 설치 관리)
