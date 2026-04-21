---
name: ax-build
description: "team-ax 빌드 스킬. 개발팀 역할 전체 — plan(파일 분할) → 공통 기반 → 병렬 라운드(codex 워커 N개) → 오너 확인 → QA. 단일 브랜치 + 파일 whitelist 격리. Use when: /ax-build, 구현, 빌드, 개발."
argument-hint: "<대상 제품 리포 경로>"
---

# /ax-build

team-ax의 빌드 스킬. **개발팀의 업무 시작부터 끝까지** — plan 수립 → 공통 기반 → 병렬 구현 → 오너 확인 → QA 넘기기.

> **역할 경계**
> - ax-define = PM ("무엇을 만들지" — scope 확정)
> - ax-build = 개발팀 ("어떻게 만들지" — plan → 구현 → 리뷰 → 오너 확인)
> - ax-qa = QA ("제대로 됐는지" — 통합 테스트)

lead(Claude main session)는 오케스트레이션 전담. 코드 작성은 전부 codex 워커가 담당. 단일 `version/vX.Y.Z` 브랜치 위에서 **파일 whitelist 격리**로 병렬 라운드를 돌린다.

## 모델

```
lead (Claude main session)
  ├─ planner (agent)       → .ax/plan.json 생성
  ├─ orchestrator (script) → version branch / tmux pane / 워커 스폰 / 상태 수집
  ├─ polling + commit      → result.json 읽고 lead가 일괄 커밋
  └─ workers (codex × N)   → /ax-execute <inbox.md> (각 tmux pane에서 one-shot)
```

- **단일 브랜치**: `version/vX.Y.Z`. 워커 브랜치 없음, 머지 없음.
- **격리**: 파일 whitelist. planner가 파일 경로가 겹치지 않게 태스크 분할.
- **워커**: codex `exec` one-shot. lead 일괄 커밋이므로 워커는 커밋/푸시 금지.
- **프로토콜**: 파일시스템만 (`.ax/plan.json`, `.ax/workers/<id>/inbox.md`, `.ax/workers/<id>/result.json`).
- **가시성**: **메인 window를 수직 split**. 왼쪽 pane = lead(claude main), 오른쪽 pane = 워커들(추가 spawn 시 수평 split으로 워커 영역 내부 분할). 오너가 한 화면에서 전부 관찰 가능.

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | `versions/undefined/scope.md` (ax-define 산출), `docs/specs/`, `flows/`, `DESIGN_SYSTEM.md`, 기존 코드 |
| **출력** | `versions/vX.Y.Z/build-plan.md` (사람 계획서), `.ax/plan.json` (기계 SSOT), 구현 커밋, 오너 확인 완료 상태 |

## 전제

- **codex CLI 설치 + 로그인** — `npm install -g @openai/codex` + `codex login`
- **tmux 안에서 기동** — `echo $TMUX` 비어있지 않아야 함
- **ax-execute 스킬 codex 설치** — `/ax-codex install` 1회 필요

사전 점검은 아래 `0단계`에서 스크립트가 검증.

## 동작 순서

### 0단계 — 사전 점검

```bash
bash plugin/scripts/ax-build-orchestrator.sh precheck
```

tmux / codex CLI / codex login / git / ax-execute 스킬 설치 상태 확인. 실패 시 안내 출력 + 중단.

### 1단계 — plan (구현 계획 + 파일 분할)

**메인 세션에서 `planner` 에이전트 호출.** planner는 전체 버전의 구현 계획 수립 + **파일 집합 단위 태스크 분할**을 담당.

**입력:**
- `versions/undefined/scope.md`
- `flows/`, `docs/specs/`, `DESIGN_SYSTEM.md` (있으면)
- 기존 코드 gap 분석

**산출물 (동시 2개):**
- `versions/vX.Y.Z/build-plan.md` — 사람이 읽는 계획서 (templates/build-plan.md 포맷)
- **`.ax/plan.json`** — 기계가 읽는 SSOT (lead가 이걸 보고 스폰·폴링·커밋)

`.ax/plan.json` 스키마는 `plugin/agents/planner.md` 참조. 필드:

- `tasks[].id` — 고유 식별자 (예: `T0-common`, `T1`, `T2`)
- `tasks[].title` — 사람 제목
- `tasks[].kind` — `common` (공통 기반, 최우선) | `task` (일반 병렬)
- `tasks[].files` — 편집 허용 파일/디렉토리 glob (whitelist 원천)
- `tasks[].blockedBy` — 선행 태스크 id 배열
- `tasks[].instructions` — 구체 지시 (scope/spec에서 추출)
- `tasks[].hints` — (옵션) 참고 spec, 기존 패턴 등

**분할 규칙 (planner가 적용):**
1. 두 태스크가 같은 파일 건드리면 → 병렬 불가 (`blockedBy`로 순차화)
2. 공유 파일(타입, 공통 유틸)은 `kind: common`으로 분리 → 최우선
3. 1라운드 병렬 대상 최대 5 (기본 2-3)
4. 분할 불가능한 전역 리팩토링 → 단일 태스크 1워커 폴백

**오너 게이트:** lead가 plan.json 요약(태스크 수 / 라운드 수 / 라운드별 워커 수 / 파일 분할 요약 / 위험 신호)을 오너에게 보여주고 **승인**. 반려 시 planner 재분할.

→ **커밋** (`docs(build): vX.Y.Z plan + 파일 분할`)

### 2단계 — version branch + 폴더 승격

```bash
bash plugin/scripts/ax-build-orchestrator.sh init vX.Y.Z
```

- `versions/undefined/` 산출 커밋 (있으면)
- `versions/undefined/` → `versions/vX.Y.Z/` 승격
- `version/vX.Y.Z` 브랜치 생성/체크아웃
- `.ax/workers/` 디렉토리 확보

### 3단계 — 병렬 라운드 루프

공통 기반(`kind: common`)을 최우선 순차 처리한 뒤, 병렬 가능 태스크를 라운드 단위로 돌린다. 모든 태스크 `done` 될 때까지 반복.

**한 라운드 흐름:**

#### 3-a. 라운드 태스크 선정 (lead)

`.ax/plan.json`에서 다음 조건을 만족하는 태스크 집합 추출:

- 아직 완료(commit)되지 않음
- `blockedBy`가 전부 완료됨
- 이번 라운드 우선순위: `kind: common` > `kind: task`
- `common` 태스크가 있으면 **이번 라운드는 common 1개만** (순차 처리)
- `common`이 전부 끝나면 이후 라운드는 `task` 병렬

라운드 워커 수 = 선정된 태스크 수 (최대 5).

#### 3-b. inbox.md 생성 (lead)

선정된 각 태스크에 대해:

```
.ax/workers/<task_id>/inbox.md
```

`plugin/skills/ax-build/templates/worker-inbox.md.tmpl` 포맷으로 채운다. 필수 필드:

- `task_id`, `title`, `instructions`
- `whitelist` = plan.json의 `files`
- `result_path` = `.ax/workers/<task_id>/result.json`
- `hints` (옵션)

preamble/가드 룰은 inbox에 복제하지 않음 (ax-execute SKILL.md에 내재).

#### 3-c. 워커 pane 스폰 (orchestrator)

각 태스크마다:

```bash
bash plugin/scripts/ax-build-orchestrator.sh spawn vX.Y.Z <task_id> [model]
```

내부 동작:
- 첫 워커 → 메인 window를 수직 split (왼쪽 lead 60%, 오른쪽 워커 40%)
- 추가 워커 → 첫 워커 pane을 수평 split (워커 영역 내부에서 나눔)
- 각 pane에 아래 명령 주입:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write \
  '$ax-execute .ax/workers/<task_id>/inbox.md'
```

**모델 선택:**
- 기본: codex CLI 기본값 (`~/.codex/config.toml`의 `model`)
- 오버라이드: `AX_CODEX_MODEL` env 또는 spawn 3번째 인자 — 지정 시 `-c model=<값>` 주입

**pane 관리:**
- pane title = `ax:<task_id>` (식별 용이)
- `remain-on-exit on` — 비정상 종료 시 pane 잔존 (디버깅)
- 스폰 직후 포커스는 자동으로 메인 pane 복귀

#### 3-d. 폴링 + 수렴 감지 (lead)

```bash
bash plugin/scripts/ax-build-orchestrator.sh status
```

10초 간격으로 호출. 집계 예시:
```
total=3 done=2 blocked=0 error=0 in-progress=1
```

**판정:**
- 모든 워커 `status: done` → 3-e로
- 1개라도 `status: error` → 즉시 중단 + 오너 보고 (notes 출력)
- `status: blocked` → notes 기반 오너 개입 유도 (외부 답변 필요 / 공유 파일 미처리 등)
- **timeout 30분** (result.json 미작성) → pane 로그 캡처 + 오너 알림 + `tmux kill-pane` 후 순차 재시도 옵션

진행 중엔 lead가 요약을 출력 — `workers: N done / M in-progress` 형식.

#### 3-e. lead 검증 + 일괄 커밋 (lead)

1. 각 `result.json`의 `files_touched` 집계
2. `git status --porcelain`과 대조 → **whitelist 밖 변경 탐지** (2중 가드: 워커 preamble + lead 검증)
3. 범위 밖 변경 발견 시 즉시 중단 + 오너 보고, **임의 되돌리기 금지**
4. 태스크 단위 커밋 (워커별 1개 또는 논리 묶음 1-2개)
5. 커밋 메시지 표준: `<task_id>: <제목> — <주요 변경 요약>` (한글)
6. 빈 워커 (`done`인데 `files_touched=[]`) → 로그만 남기고 커밋 스킵

#### 3-f. plan 업데이트 + 다음 라운드 (lead)

`.ax/plan.json`에서 완료 태스크 제거(또는 상태 마킹). 다른 태스크의 `blockedBy`에서도 해제. 남은 태스크가 있으면 3-a로 루프. 전부 완료면 4단계로.

### 4단계 — 오너 최종 확인 (통합)

전체 커밋 상태에서 통합 동작 확인.

- `version/vX.Y.Z`에서 dev server 실행 (기본 포트)
- **전체 그림 확인** — 개별 태스크가 아니라 통합 상태
- 오너 피드백 → 메인 세션에서 직접 수정 (필요 시 소규모 핫픽스 인라인)
- 확인 완료 → ax-qa로

### 5단계 — QA 넘기기

```bash
bash plugin/scripts/ax-build-orchestrator.sh cleanup
```

→ 워커 pane 전부 kill. `.ax/` 디렉토리는 로그로 남김(선택).

`/ax-qa` 실행 안내. ax-qa가 통합 테스트 + code review + PR → main.

## 디자인 중 스펙 변경 처리

**프로토콜:**
1. 스펙 변경이 **해당 태스크 내부에서만 영향** → 워커가 `status: blocked` + notes → lead가 scope/plan 갱신 후 재스폰
2. 스펙 변경이 **다른 태스크에도 영향** → lead가 `.ax/plan.json`의 `files`/`blockedBy` 재조정 → 필요 시 새 라운드
3. 스펙 변경이 **scope 자체를 바꿈** → 메인 세션에서 scope.md 갱신 → build-plan 재조정 → plan.json 재생성

## 가드레일

1. **build-plan + plan.json 오너 승인 필수** — 승인 없이 스폰 금지
2. **공통 기반 선행** — `kind: common` 태스크가 있으면 첫 라운드에서 순차 처리
3. **backpressure** — 워커의 ax-execute가 `lint + typecheck + unit + build` 통과를 강제. 통과 전 `done` 불가
4. **워커 커밋 금지** — lead가 일괄. 이중 커밋 방지
5. **placeholder/stub 금지** — ax-execute가 강제
6. **텍스트/보안 하드코딩 금지** — i18n/env
7. **영역 침범 가드 2중** — 워커 preamble + lead git status 대조
8. **공유 파일은 공통 기반에서** — 개별 워커에서 만지지 않음 (만지면 blocked)
9. **범위 밖 변경 시 되돌리기 금지** — lead/오너 판단
10. **워커 수 상한 5** — 초과 시 라운드 분할

## 호환성 / breaking change (v0.7 → v0.8)

- **worktree 흐름 제거** — `.claude/worktrees/` 생성 안 함. 워커 브랜치(`version/vX.Y.Z-<name>`)도 없음
- **`executor.engine` 토글 제거** — codex 고정. `.claude/settings.json`의 `executor.engine`은 무시됨
- **Claude `executor` 에이전트 경로 deprecated** — legacy 보존이 필요하면 별도 플래그로만 (사전 협의)
- **`.ax-brief.md` (단일 공유) 폐기** → 워커별 `.ax/workers/<id>/inbox.md`
- **`.ax-status` (파일 기반 상태) 폐기** → `.ax/workers/<id>/result.json` 스키마
- **ax-execute의 stdout DONE/BLOCKED 공식 계약 → result.json 파일**. stdout은 보조 로그
- **ax-execute 커밋 금지** (v0.7은 태스크 단위 커밋했음)

v0.7 사용자 migration: `/ax-codex install` 재실행으로 새 ax-execute 주입 → ax-build가 자동으로 v0.8 흐름 사용.

## 참조

- `references/backpressure-pattern.md` — backpressure + fresh context 패턴
- `references/preflight-checklist.md` — 빌드 전 체크리스트
- `references/security-rules.md` — 보안 규칙
- `templates/build-plan.md` — 사람 읽는 계획서 포맷
- `templates/worker-inbox.md.tmpl` — 워커 inbox 포맷
- `plugin/scripts/ax-build-orchestrator.sh` — orchestrator (precheck/init/spawn/status/cleanup)
- `plugin/agents/planner.md` — 계획 + 파일 분할 에이전트
- `../ax-execute/SKILL.md` — 워커 프로토콜 엔진 (codex 스킬, `$ax-execute`)
- `../ax-codex/SKILL.md` — codex 스킬 동기화
- `../ax-design/SKILL.md` — 디자인 필요 시 호출
- `../ax-qa/SKILL.md` — QA 넘기기
- `../ax-review/SKILL.md` — code review (Codex 위임)

## Final Checklist

- [ ] 0단계 precheck 통과
- [ ] 1단계 plan.json 오너 승인
- [ ] 2단계 version branch + 폴더 승격
- [ ] `kind: common` 태스크 순차 완료
- [ ] 병렬 라운드 루프에서 모든 task 완료
- [ ] 모든 result.json `status: done` + lead 일괄 커밋 완료
- [ ] 4단계 오너 통합 확인 완료
- [ ] 워커 pane cleanup
- [ ] `/ax-qa` 안내
