---
name: ax-review
description: "team-ax 범용 리뷰 스킬 (codex 위임). doc/code/pr 타입 분기. doc 구현, code·pr는 stub. Use when: ax-review, 문서 리뷰, 구현 리뷰, PR 리뷰, scope.md 검증."
argument-hint: "<doc|code|pr> <대상>"
---

# /ax-review

team-ax의 모든 리뷰(문서·구현·PR)를 **codex에 위임**하는 범용 스킬. 작성 엔진(Claude) ≠ 검증 엔진(codex)으로 엔진 수준 분리.

## 동작 개요

1. `$ARGUMENTS` 첫 단어를 **타입**으로 파싱 (`doc` / `code` / `pr`).
2. 나머지를 **대상**으로 사용 (파일 경로 또는 PR 번호).
3. 타입별 체크리스트 경로를 매핑.
4. **read-only** 리뷰 지침을 구성해 codex 또는 호출자(Claude)에게 전달.
5. 출력 첫 줄은 `APPROVE` 또는 `REQUEST_CHANGES: {이유}`. 이후 줄에 항목별 근거.

> 본 스킬 본체는 read-only 분석만. 쓰기 행위 금지(codex `default sandbox = read-only`와 일치). 호출자가 stdout을 받아 scope.md `§리뷰` 등 적절한 위치에 기록한다.

## 인자 파싱

```
$ARGUMENTS = "<type> <target...>"
type   = $ARGUMENTS의 첫 단어
target = 나머지 (공백 포함 가능)
```

| type | 매핑되는 체크리스트 | 상태 | 호출 sandbox |
|---|---|---|---|
| `doc` | `references/doc-checklist.md` | **구현** | `read-only` (codex 기본값) |
| `code` | `references/code-checklist.md` | stub (미구현 안내 후 중단) | `read-only` |
| `pr` | `references/pr-checklist.md` | stub (미구현 안내 후 중단) | (구현 시 `workspace-read`) |

타입이 없거나 위 3종이 아니면 → 오너에게 `doc | code | pr` 중 무엇인지 확인 후 중단.

## 타입별 동작

### `doc`

대상: 문서(주로 `versions/undefined/scope.md`)와 그 문서의 §수정 계획에 등장한 파일들.

1. `references/doc-checklist.md` 본문을 로드.
2. 대상 문서 + §수정 계획에서 언급된 파일들을 함께 읽도록 codex에 지시.
3. **평가 대상 한정**: diff에 §수정 계획 밖 파일이 섞여 있으면 무시한다 (사전 unstaged 잔재 등). 체크리스트 5종은 §수정 계획에 명시된 파일에만 적용.
4. 체크리스트 5종 항목별로 PASS/FAIL을 채우고 첫 줄에 `APPROVE` 또는 `REQUEST_CHANGES: {핵심 이유}`로 판정.
5. 호출자가 출력 전체를 scope.md `§리뷰` 섹션에 그대로 붙여넣는다.

**호출 예시 (Codex 직접 / Claude → codex 위임 둘 다 동일 인자)**

```bash
# Codex에서 직접
$ax-review doc versions/undefined/scope.md

# Claude → codex 위임 (Bash 도구로)
codex exec '$ax-review doc versions/undefined/scope.md'
```

### `code`

대상: 구현 코드. ax-build에서 Codex에 위임하여 호출.

1. `references/code-checklist.md` 본문을 로드.
2. 대상 파일 + 관련 spec을 함께 읽도록 codex에 지시.
3. 체크리스트 항목별로 PASS/FAIL을 채우고 첫 줄에 `APPROVE` 또는 `REQUEST_CHANGES: {핵심 이유}`로 판정.

**호출 예시:**
```bash
codex exec '$ax-review code src/app/api/auth/pin/'
```

### `pr` (stub)

`references/pr-checklist.md`도 단일 줄 stub. 본 스킬이 호출되면:

```
NOT_IMPLEMENTED: ax-review pr 타입 미구현.
```

위 한 줄 출력 후 중단. (`gh pr diff` 실행을 위한 sandbox 정책 확정 후 구현 예정.)

## 출력 포맷

모든 타입(stub 제외) 공통:

```
{APPROVE | REQUEST_CHANGES: {한 줄 이유}}

## 항목별 근거
1. {체크리스트 항목 1}: PASS / FAIL — {근거 한 줄, 파일:라인 인용 가능}
2. {체크리스트 항목 2}: PASS / FAIL — {근거 한 줄}
...

## 재작업 노트 (REQUEST_CHANGES일 때만)
- {수정 지침 1}
- {수정 지침 2}
```

> 첫 줄이 판정. 호출자(또는 SKILL.md ax-define)는 첫 줄로 루프 재진입 여부를 결정한다.

## 가드레일

- **read-only 엄수** — 본 스킬 실행 중 어떤 파일도 수정하지 않는다 (체크리스트와 대상만 읽는다).
- **타입 분기 철저** — 인자 파싱 실패 시 임의 추론 금지. 오너 확인.
- **stub 타입은 즉시 중단** — code/pr 타입 호출 시 NOT_IMPLEMENTED 한 줄만 출력. 부분 결과 만들지 않음.
- **출력 첫 줄 형식 고정** — `APPROVE` 또는 `REQUEST_CHANGES: ...`. 호출자가 grep으로 판정함.

## 참조

- `references/doc-checklist.md` — 문서 리뷰 체크리스트
- `references/code-checklist.md` — 구현 리뷰 (stub)
- `references/pr-checklist.md` — PR 리뷰 (stub)

## 설치

본 스킬을 Codex `$ax-review`로 호출하려면 `~/.codex/skills/ax-review/`로 동기화 필요. `/ax-codex` 스킬로 관리한다.

```bash
# Claude 세션에서
/ax-codex install

# 또는 직접
bash plugin/scripts/ax-codex.sh install
```

자세한 내용은 루트 `AGENTS.md` 참조.
