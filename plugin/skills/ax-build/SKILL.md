---
name: ax-build
description: "team-ax 빌드 스킬. 개발팀 역할 전체 — plan(실행 전략) → 공통 기반 → 구현(순차/병렬) → 오너 확인 → 머지 → QA. Use when: /ax-build, 구현, 빌드, 개발."
argument-hint: "<대상 제품 리포 경로>"
---

# /ax-build

team-ax의 빌드 스킬. **개발팀의 업무 시작부터 끝까지** — plan 수립부터 구현/리뷰/오너 확인/QA 넘기기까지.

> **역할 경계**
> - ax-define = PM ("무엇을 만들지" — scope 확정)
> - ax-build = 개발팀 ("어떻게 만들지" — plan → 구현 → 리뷰 → 오너 확인)
> - ax-qa = QA ("제대로 됐는지" — 통합 테스트)

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | `versions/undefined/scope.md` (ax-define 산출물), `docs/specs/`, `flows/`, `DESIGN_SYSTEM.md`, 기존 코드 |
| **출력** | `versions/vX.Y.Z/build-plan.md`, version branch, 구현 코드, 테스트, 오너 확인 완료 상태 |

## 에이전트 구성

| 에이전트 | 담당 | 책임 |
|---|---|---|
| `planner` | 1단계 | gap 분석 + 작업 분해 + 실행 전략 결정 |
| `executor` (claude) | 3단계 | BE/FE 구현 (TDD + backpressure + 영역 침범 가드) |
| `ax-execute` 스킬 (codex) | 3단계 | 동일 책임을 codex가 수행 (`executor.engine=codex` 토글 시) |
| `design-builder` | 3단계 | 디자인 필요 작업에서 ax-design 호출 후 FE 구현 |

### executor.engine 토글

3단계 코드 구현의 작성 엔진을 **claude / codex** 중 선택할 수 있다. 위치는 프로젝트 `.claude/settings.json`:

```json
{
  "executor": { "engine": "claude" }
}
```

| 값 | 동작 |
|---|---|
| `claude` (기본) | `executor` 에이전트(`plugin/agents/executor.md`)를 메인 세션의 Task 도구로 호출 |
| `codex` | `codex exec '$ax-execute <task-spec> [--allow ...] [--block ...]'`로 위임 (`plugin/skills/ax-execute/SKILL.md`) |

두 엔진 모두 동일한 제약(TDD / backpressure / 영역 침범 가드 / 보안)을 따른다. ax-build 오케스트레이터(워크트리 / tmux / 머지)는 그대로 유지되고 **executor 단계만 분기**한다.

산출물 인터페이스도 동일: 태스크 단위 git 커밋 + 결과 요약. codex의 경우 stdout 첫 줄이 `DONE` / `BLOCKED: {이유}`이며, 메인 세션이 이를 보고 다음 태스크 진행 또는 오너 보고 결정.

## 동작 순서

### 사전 점검

1. 제품 리포 루트에 있는지 확인 (`pwd`).
2. `versions/undefined/scope.md` 존재 확인 (ax-define 완료 전제).
3. `docs/specs/` 존재 확인.
4. **메인 claude 세션이 tmux 안에서 기동 중인지 확인** (`echo $TMUX`가 비어있지 않아야 함). 3-b(워크트리 병렬) 흐름은 같은 tmux 세션에 새 윈도우를 여는 방식이므로, 메인이 tmux 밖이면 orchestrator가 ERROR로 중단한다. 밖이면 `tmux new-session -s ax-build` 후 그 안에서 claude를 다시 시작할 것.

### 1단계 — plan (구현 계획 수립)

메인 세션에서 `planner` 에이전트가 실행. **전체 버전의 구현 계획을 세운다.**

**입력:**
- `versions/undefined/scope.md` (§Story Map, §수정 계획)
- `flows/` (UX 플로우, 있으면)
- `docs/specs/` (기존 스펙)
- 기존 코드 gap 분석 (subagent로 탐색 — "구현되어있다고 가정하지 말고 확인")
- `DESIGN_SYSTEM.md` (기존 DS, 있으면)

**planner가 결정하는 것:**
1. **공통 기반** — 여러 작업이 공유하는 DB/API/타입/DS 식별
2. **작업 단위 분해** — Story 단위가 아닌 **구현 단위**로 분해
3. **의존 관계** — 작업 간 선후 관계
4. **디자인 필요 여부** — 작업별 판단
5. **실행 전략** — 워크트리 병렬 여부 결정

**실행 전략 결정 기준:**

| 조건 | 전략 |
|---|---|
| 작업이 1~2개이고 작음 | 워크트리 없이 version branch에서 순차 |
| 독립 작업이 2개 이상 + 각각 규모 있음 | 워크트리 분리 → 병렬 |
| 연결된 UX 흐름 | 같은 워크트리에서 함께 |
| 작업 B가 작업 A에 의존 | A 완료 후 B 시작 |
| 전체가 한 흐름 | 워크트리 불필요 — version branch에서 순차 |

**산출물: `versions/vX.Y.Z/build-plan.md`** (templates/build-plan.md 포맷)

**오너 확인**: build-plan.md를 오너에게 보여주고 승인. **승인 없이 구현 착수 금지.**

→ **커밋** (`docs(build): vX.Y.Z build-plan 수립`)

### 2단계 — 공통 기반 구축

여러 작업이 공유하는 기반을 version branch에서 먼저 구축. **공통 기반 없으면 워크트리 생성 금지.**

**version branch 생성** (없으면):
```bash
git checkout -b version/vX.Y.Z
```

**폴더 승격** (Phase B에서 이동):
```bash
# Phase A 산출물 커밋
git add versions/undefined/
git commit -m "Phase A 완료 — vX.Y.Z scope 확정"

# 폴더 승격
mv versions/undefined versions/vX.Y.Z
git add versions/
git commit -m "vX.Y.Z 폴더 승격"
```

**공통 기반 구축 순서**: DB → API → 타입 → DS (하위 레이어부터)

| 영역 | 내용 |
|---|---|
| DB | 공통 테이블/컬럼 마이그레이션 |
| API | 여러 작업이 쓰는 공통 엔드포인트 |
| 타입 | 공통 타입/인터페이스 정의 |
| DS | 신규 컴포넌트 (ax-design 호출 → 오너 확정 → DS 등록) |

build-plan.md에 공통 기반 항목이 없으면 이 단계 스킵.

각 항목 완료 → backpressure (lint/typecheck/unit/build) → **커밋**.

### 3단계 — 실행

build-plan.md의 실행 전략에 따라 진행.

**진입 시 `executor.engine` 확인:**
```bash
ENGINE=$(jq -r '.executor.engine // "claude"' .claude/settings.json 2>/dev/null || echo "claude")
```

- `claude` → `executor` 에이전트 호출 (메인 세션의 Task 도구)
- `codex` → `codex exec '$ax-execute <task-spec> --allow <허용경로> --block <차단경로>'`

두 엔진 모두 **차단 파일 경로를 반드시 명시해서 호출**한다 (영역 침범 가드 발동 조건).

#### 3-a. 워크트리 없이 (version branch에서 순차)

메인 세션에서 `executor` 에이전트(claude) 또는 `$ax-execute` 스킬(codex)로 직접 구현:

```
태스크 선택 → 차단 영역 명시 → 구현 → backpressure → git status self-check
        → 커밋 → codex code review → 다음 태스크
```

완료 → 서버 띄우기 → 4단계(오너 확인)로.

#### 3-b. 워크트리 병렬

메인 세션이 `ax-build-orchestrator.sh`를 실행:

1. **워크트리 생성** (build-plan의 작업 단위별)
2. **`.ax-brief.md` 생성** (templates/ax-brief.md 포맷으로 작업 지시서 작성 → 워크트리에 저장)
3. **tmux 윈도우 자동 생성 (백그라운드):**
   ```bash
   tmux new-window -d -n "work-a" \
     "cd .claude/worktrees/work-a && claude 'Read .ax-brief.md and follow the instructions.'"
   ```

   **세 가지 중요:**
   - `-d` — 메인에 포커스 유지. 미지정 시 새 윈도우로 자동 전환되어 오너 키 입력이 워커 stdin으로 샌다 (과거 "메인 화면 깨짐" 사고 원인).
   - `-p` 없음 — claude 기본이 인터랙티브 TUI이며, `-p`는 "응답 1회 출력 후 종료" 모드라 워커가 조용히 죽는다.
   - positional prompt — TUI 시작과 동시에 brief 참조 지시 주입. Claude가 MCP 부팅 후 Read 도구로 `.ax-brief.md`를 읽어 작업을 시작한다.

**각 세션 내부 흐름:**

```
.ax-brief.md 읽기 (현재 작업 + 차단 영역 + executor.engine 확인)
  → 디자인 필요? → ax-design 실행 → 구현
  → 디자인 불필요? → 바로 구현
  → 태스크별: 구현 → backpressure → git status self-check → 커밋
  → 전체 완료 → codex code review
  → 서버 띄우기 (할당 포트)
  → .ax-status = "review-ready"
```

`.ax-brief.md`에는 반드시 **차단 영역**을 명시한다. `executor.engine=codex`로 호출 시 `--allow` / `--block` 인자에 그대로 전달된다.

**backpressure (모든 세션 공통):**
- lint + typecheck + unit + build 통과 전 다음 태스크 금지
- 태스크 완료 = 커밋 (커밋 없이 다음 태스크 금지)
- placeholder/stub 금지

**code review (Codex 위임):**
```bash
codex exec '$ax-review code {변경 파일 경로}'
```
- **변경 파일 경로만 전달** — 전체 컨텍스트/diff를 프롬프트에 붙이지 않음 (속도)
- **작업 단위 diff만** — 전체 diff가 아니라 이번 작업에서 변경된 파일만
- spec 정합 / DS 준수 / silent failure / 보안 / 텍스트 하드코딩 검증
- APPROVE → review-ready. REQUEST_CHANGES → 수정 후 재리뷰.
- **동일 사유 2회 연속 REQUEST_CHANGES → 오너에게 위임** (무한 루프 방지)
- **사전 체크**: `$ax-review code`가 stub(구 버전 캐시)이면 경고 출력 + 플러그인 업데이트 안내

**포트 할당:**
```
기본 포트 + 10 + 작업 번호
예: rubato(3001) → work-a: 3011, work-b: 3012
```

**오너 대화**: 빌드 중 오너가 tmux 윈도우 전환으로 해당 세션에 직접 대화 가능.

### 4단계 — 오너 확인

빌드 완료된 작업은 dev server가 떠 있는 상태.

**`.ax-status` 상태 전이:**

| 상태 | 의미 |
|---|---|
| `building` | 빌드 진행 중 |
| `review-ready` | 빌드 + code review 완료, 서버 실행 중, 오너 확인 대기 |
| `needs-fix` | 오너 피드백 → 수정 중 |
| `merge-ready` | 오너 OK → 머지 대기 |

**오너 흐름:**
1. tmux 윈도우 전환 → 해당 세션
2. `localhost:{포트}` 접속 → 동작 확인
3. OK → `merge-ready`
4. 수정 필요 → 세션에서 피드백 → 수정 → 재확인

워크트리 없이 진행한 경우: version branch에서 서버 띄우고 메인 세션에서 오너 확인.

### 5단계 — 머지

전체 `merge-ready` 후 메인 세션에서 version branch에 순차 머지.

```bash
git merge version/vX.Y.Z-work-a
git merge version/vX.Y.Z-work-b
```

충돌 시 → 오너에게 보고 + 해소 방법 제안.
워크트리 없이 진행한 경우 이미 version branch에 있으므로 스킵.

### 6단계 — 오너 최종 확인

전체 머지 상태에서 통합 동작 확인.

- version branch에서 dev server 실행 (기본 포트)
- **전체 그림 확인** — 개별 작업이 아니라 통합 상태
- 오너 피드백 → 메인 세션에서 직접 수정
- 확인 완료 → ax-qa로 넘기기

### 7단계 — QA 넘기기

`/ax-qa` 실행 안내. ax-qa가 통합 테스트 후 PR → main 머지까지 진행.

## 디자인 중 스펙 변경 처리

**프로토콜:**
1. 스펙 변경이 **해당 작업 내부에서만 영향** → 워크트리에서 직접 수정
2. 스펙 변경이 **다른 작업에도 영향** → version branch에서 수정 후 영향받는 워크트리에 merge 전파
3. 스펙 변경이 **scope 자체를 바꿈** → 메인 세션에서 scope.md 갱신 → build-plan 재조정

## 가드레일

1. **build-plan 오너 승인 필수** — plan 없이 구현 착수 금지.
2. **공통 기반 없으면 워크트리 금지** — 공통 DB/API/타입/DS가 안 깔렸으면 분리 금지.
3. **backpressure** — lint/typecheck/unit/build 통과 전 다음 태스크 금지.
4. **태스크 완료 = 커밋** — 커밋 없이 다음 태스크 금지.
5. **placeholder/stub 금지** — 모든 기능 완전 구현.
6. **텍스트 하드코딩 금지** — i18n/copy 경유.
7. **보안 하드코딩 금지** — 키/토큰은 환경 변수.
8. **env 파일 읽기 금지** — 변수명만 .env.example에서 확인.
9. **code review는 Codex 위임** — 작성 엔진 ≠ 검증 엔진.
10. **발견한 버그** → 해결하거나 plan에 기록 (무시 금지).
11. **스펙 불일치** → 메인 세션에 보고.
12. **영역 침범 가드 필수** — executor 호출 시 차단 영역 명시 + 각 태스크 후 `git status` self-check. 침범 발견 시 임의 되돌리기 금지, 오너 보고. claude/codex 양쪽 동일 적용.
13. **공유 파일은 공통 기반에서 처리** — 타입 정의 등 여러 태스크 공유 파일은 2단계(공통 기반)에서 미리. 3단계의 individual executor가 만지지 않음.

## 참조

- `references/backpressure-pattern.md` — backpressure + fresh context 패턴
- `references/preflight-checklist.md` — 빌드 전 체크리스트
- `references/security-rules.md` — 보안 규칙
- `templates/build-plan.md` — build-plan 포맷
- `templates/ax-brief.md` — 워크트리 작업 지시서 포맷
- `plugin/scripts/ax-build-orchestrator.sh` — tmux + 워크트리 + 머지 자동화
- `plugin/agents/planner.md` — 구현 계획 에이전트
- `plugin/agents/executor.md` — 구현 에이전트 (claude 분기, 영역 침범 가드 포함)
- `../ax-execute/SKILL.md` — 코드 구현 스킬 (codex 분기, `$ax-execute`로 호출)
- `../ax-codex/SKILL.md` — codex 스킬 동기화 (install/uninstall/status)
- `../ax-design/SKILL.md` — 디자인 필요 시 호출
- `../ax-qa/SKILL.md` — QA 넘기기
- `../ax-review/SKILL.md` — code review (Codex 위임)
