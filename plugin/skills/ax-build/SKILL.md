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
  ├─ planner (agent)       → .ax/plan.json 생성 (파일 분할 + glue 태스크)
  ├─ orchestrator (script) → version branch / 백그라운드 워커 기동 / 상태 집계
  ├─ polling + commit      → result.json 읽고 lead가 일괄 커밋
  └─ workers (codex × N)   → /ax-execute <inbox.md> (백그라운드 프로세스, stdout→stdout.log)
```

- **단일 브랜치**: `version/vX.Y.Z`. 워커 브랜치 없음, 머지 없음.
- **격리**: 파일 whitelist. planner가 파일 경로가 겹치지 않게 태스크 분할 + 연결 태스크 별도 분리.
- **워커**: `codex exec` 백그라운드 프로세스. pid는 `.ax/workers/<id>/pid`, 로그는 `stdout.log`. lead 일괄 커밋이므로 워커는 커밋/푸시 금지.
- **프로토콜**: 파일시스템만 (`.ax/plan.json`, `.ax/workers/<id>/inbox.md`, `.ax/workers/<id>/result.json`, `.ax/workers/<id>/stdout.log`).
- **가시성**: lead가 `status` 집계로 진행 요약. 디버깅은 `logs <task_id>` / `tail -f .ax/workers/<id>/stdout.log`. tmux/pane 의존 없음.

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | `versions/undefined/scope.md` (ax-define 산출), `docs/specs/`, `flows/`, `DESIGN_SYSTEM.md`, 기존 코드 |
| **출력** | `versions/vX.Y.Z/build-plan.md` (사람 계획서), `.ax/plan.json` (기계 SSOT), 구현 커밋, 오너 확인 완료 상태 |

## 전제

- **codex CLI 설치 + 로그인** — `npm install -g @openai/codex` + `codex login`
- **ax-execute 스킬 codex 설치** — `/ax-codex install` 1회 필요

사전 점검은 아래 `0단계`에서 스크립트가 검증. tmux 의존 없음 (iTerm/Ghostty/VS Code 어느 터미널에서도 동작).

## 오케스트레이터 스크립트 경로 resolve

SKILL.md 본문의 `bash <ORCH> ...` 예시에서 `<ORCH>`는 플러그인 설치 위치에 따라 다르다. Claude가 다음 방식으로 resolve한다:

```bash
# 설치된 플러그인 기준 (일반 사용자)
ORCH=$(ls -d ~/.claude/plugins/cache/*/team-ax/*/scripts/ax-build-orchestrator.sh 2>/dev/null | sort -V | tail -1)

# moomoo-ax dev 리포 기준 (개발 시)
[[ -z "$ORCH" ]] && [[ -f "plugin/scripts/ax-build-orchestrator.sh" ]] && ORCH="plugin/scripts/ax-build-orchestrator.sh"

[[ -z "$ORCH" ]] && { echo "ERROR: ax-build-orchestrator.sh 경로 resolve 실패"; exit 1; }
```

이하 실행 예시는 `bash "$ORCH" <subcommand>` 형태.

## 동작 순서

### 0단계 — 사전 점검

```bash
bash "$ORCH" precheck
```

codex CLI / codex login / git / ax-execute 스킬 설치 상태 확인. 실패 시 안내 출력 + 중단.

### 1단계 — plan (구현 계획 + 파일 분할)

**메인 세션에서 `planner` 에이전트 호출.** planner는 전체 버전의 구현 계획 수립 + **파일 집합 단위 태스크 분할 + glue 태스크 분리**를 담당.

**산출물 (동시 2개):**
- `versions/vX.Y.Z/build-plan.md` — 사람이 읽는 계획서
- **`.ax/plan.json`** — 기계가 읽는 SSOT (lead가 스폰·폴링·커밋에 사용)

`.ax/plan.json` 스키마는 `plugin/agents/planner.md` 참조. task `kind` 3종:

- `common` — 공통 기반 (타입/DB/공유 유틸). 최우선 순차
- `task` — 일반 병렬 가능 태스크
- `glue` — 연결 태스크 (placeholder→실체 교체 / 콜사이트 연결 등). `blockedBy`로 양쪽 완료 후 실행

**분할 규칙 요약:**
1. 두 태스크 `files` 겹침 → 병렬 불가 (`blockedBy`로 순차화)
2. 공유 파일 → `kind: common` 분리 (최우선)
3. 경계 연결 작업 → `kind: glue` 분리 (사각지대 방지)
4. 1라운드 병렬 대상 최대 5 (기본 2-3)
5. 분할 불가능한 전역 리팩토링 → 단일 태스크 1워커 폴백

**오너 게이트:** lead가 plan.json 요약(태스크 수 / 라운드 수 / 라운드별 워커 수 / 파일 분할 요약 / glue 태스크 목록 / 위험 신호)을 오너에게 보여주고 **승인**. 반려 시 planner 재분할.

→ **커밋** (`docs(build): vX.Y.Z plan + 파일 분할`)

### 2단계 — version branch + 폴더 승격

```bash
bash "$ORCH" init vX.Y.Z
```

- `versions/undefined/` 산출 커밋 (있으면)
- `versions/undefined/` → `versions/vX.Y.Z/` 승격
- `version/vX.Y.Z` 브랜치 생성/체크아웃
- `.ax/workers/` 디렉토리 확보

### 2.5단계 — 재개 진입 (재진입 전용)

이전 세션에서 ax-build가 도중에 끊겼고 `version/vX.Y.Z` 브랜치 + `.ax/plan.json` + 일부 커밋이 이미 존재하는 상태라면:

1. `git branch --list version/*`로 진행 중 버전 확인
2. `git checkout version/vX.Y.Z`
3. `.ax/plan.json` 존재 확인 — 없으면 1단계부터 (재생성)
4. `bash "$ORCH" status`로 각 워커 상태 점검:
   - `done` + 커밋 완료 → skip (plan.json의 완료 플래그로 관리)
   - `done` + 커밋 안 됨 → 3-e 검증+커밋부터
   - `blocked`/`error` → lead가 판단 후 재스폰 또는 플랜 수정
   - 미스폰 태스크 → 3-a부터
5. 남은 태스크로 3단계 루프 재진입

재개 시에도 lead는 오너에게 현재 상황 요약 + 재개 계획을 먼저 보고한다.

### 3단계 — 병렬 라운드 루프

공통 기반(`kind: common`)을 최우선 순차 처리한 뒤, 병렬 가능 태스크를 라운드 단위로 돌린다. 모든 태스크 `done` 될 때까지 반복. `kind: glue`는 선행 태스크들이 완료된 라운드에서 스폰.

**한 라운드 흐름:**

#### 3-a. 라운드 태스크 선정 (lead)

`.ax/plan.json`에서 다음 조건을 만족하는 태스크 집합 추출:

- 아직 완료되지 않음
- `blockedBy`가 전부 완료됨
- 우선순위: `common` > `task` > `glue` (단, common이 하나라도 있으면 그 라운드는 common 1개만)
- 1라운드 최대 5

#### 3-b. inbox.md 생성 (lead)

선정된 각 태스크마다 `.ax/workers/<task_id>/inbox.md`를 `plugin/skills/ax-build/templates/worker-inbox.md.tmpl` 포맷으로 생성.

필수 필드: `task_id`, `title`, `instructions`, `whitelist`(= plan.json의 `files`), `result_path`. preamble/가드 룰은 inbox에 복제하지 않음 (ax-execute SKILL.md 내재).

#### 3-c. 워커 백그라운드 기동 (orchestrator)

각 태스크마다:

```bash
bash "$ORCH" spawn vX.Y.Z <task_id> [model]
```

내부 동작:
- `codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write '$ax-execute <inbox>'`를 **백그라운드**로 실행
- stdout/stderr → `.ax/workers/<task_id>/stdout.log`
- pid → `.ax/workers/<task_id>/pid`
- 종료 코드 → `.ax/workers/<task_id>/exit_code`

**모델**: 기본값은 codex CLI 설정(`~/.codex/config.toml`의 `model`). `AX_CODEX_MODEL` env 또는 spawn 3번째 인자로 오버라이드.

#### 3-d. 폴링 + 수렴 감지 (lead)

```bash
bash "$ORCH" status
```

~15초 간격으로 호출. 집계 예시:
```
total=3 done=2 blocked=0 error=0 running=1 pending=0
```

**판정:**
- 모든 워커 `status: done` → 3-e로
- 1개라도 `status: error` → 즉시 중단 + 오너 보고 (notes + 로그 요약)
- `status: blocked` → notes 기반 오너 개입 유도
- **비정상 종료** (exit_code 있고 result.json 없음) → `bash "$ORCH" logs <task_id>`로 로그 확인 → 오너 보고
- **timeout 30분** (pid 살아있는데 result.json 미작성) → `bash "$ORCH" cleanup`으로 kill + 오너 알림 + 순차 재시도 옵션

진행 중엔 lead가 오너에게 요약을 출력 — `N done / M running / K blocked` 형식.

#### 3-e. lead 검증 + 일괄 커밋 (lead)

1. 각 `result.json`의 `files_touched` 집계
2. `git status --porcelain`과 대조 → **whitelist 밖 변경 탐지** (2중 가드: 워커 self-check + lead 검증)
3. **placeholder/TODO 잔존 스캔** — 이번 라운드 변경 파일에 대해 `grep -nE 'Placeholder|TODO|FIXME' <changed files>` → 발견 시 오너 보고 + 처리 결정:
   - glue 태스크로 다음 라운드에 처리
   - 즉시 수동 수정
   - 의도적 TODO면 스킵 (근거 기록)
4. 범위 밖 변경 발견 시 즉시 중단 + 오너 보고, **임의 되돌리기 금지**
5. 태스크 단위 커밋 (워커별 1개 또는 논리 묶음 1-2개)
6. 커밋 메시지 표준: `<task_id>: <제목> — <주요 변경 요약>` (한글)
7. 빈 워커 (`done`인데 `files_touched=[]`) → 로그만 남기고 커밋 스킵

#### 3-f. plan 업데이트 + 다음 라운드 (lead)

`.ax/plan.json`에서 완료 태스크 마킹. 다른 태스크의 `blockedBy`에서도 해제. 남은 태스크가 있으면 3-a로 루프. 전부 완료면 4단계로.

### 4단계 — 오너 최종 확인 (통합)

전체 커밋 상태에서 통합 동작 확인.

- `version/vX.Y.Z`에서 dev server 실행 (기본 포트)
- **전체 그림 확인** — 개별 태스크가 아니라 통합 상태
- 오너 피드백 → 메인 세션에서 직접 수정 (필요 시 소규모 핫픽스 인라인)
- 확인 완료 → ax-qa로

### 5단계 — QA 넘기기

```bash
bash "$ORCH" cleanup
```

→ 남은 워커 프로세스 kill. `.ax/` 디렉토리(로그 포함)는 보존(선택적으로 `mv ~/.Trash/`).

`/ax-qa` 실행 안내. ax-qa가 통합 테스트 + code review + PR → main.

## 디자인 중 스펙 변경 처리

**프로토콜:**
1. 스펙 변경이 **해당 태스크 내부에서만 영향** → 워커가 `status: blocked` + notes → lead가 scope/plan 갱신 후 재스폰
2. 스펙 변경이 **다른 태스크에도 영향** → lead가 `.ax/plan.json`의 `files`/`blockedBy` 재조정 → 필요 시 새 라운드
3. 스펙 변경이 **scope 자체를 바꿈** → 메인 세션에서 scope.md 갱신 → build-plan 재조정 → plan.json 재생성

## 가드레일

1. **build-plan + plan.json 오너 승인 필수** — 승인 없이 스폰 금지
2. **공통 기반 선행** — `kind: common`이 있으면 첫 라운드에서 순차
3. **타겟 기반 backpressure** — 워커 ax-execute가 변경 파일에 한정된 typecheck/lint/테스트 강제 (전역 lint/test 금지)
4. **워커 커밋 금지** — lead가 일괄. 이중 커밋 방지
5. **placeholder/stub 금지** — ax-execute가 강제 + lead 검증에서 grep 스캔
6. **glue 태스크 의무** — 경계 연결은 독립 태스크로 분리. 각 워커가 자기 영역 placeholder를 남기면 lead 검증에서 걸림
7. **텍스트/보안 하드코딩 금지** — i18n/env
8. **영역 침범 가드 2중** — 워커 self-check(동시 라운드 인지) + lead git status 대조
9. **공유 파일은 공통 기반에서** — 개별 워커에서 만지지 않음 (만지면 blocked)
10. **범위 밖 변경 시 되돌리기 금지** — lead/오너 판단
11. **워커 수 상한 5** — 초과 시 라운드 분할

## 디버깅

- **워커 로그**: `bash "$ORCH" logs <task_id>` 또는 `tail -f .ax/workers/<id>/stdout.log`
- **원격에서 status만 주기적 집계**: `bash "$ORCH" status`
- **비정상 종료 복구**: 로그 확인 → 원인 파악 → inbox 수정 → 재스폰 또는 수동 처리

## 호환성 / breaking change

v0.7 → v0.8 재설계 및 이후 변경은 `docs/guides/v0.7-to-v0.8-migration.md` + CHANGELOG 참조. 현재 모델의 주요 계약:

- 단일 `version/vX.Y.Z` 브랜치. 워커 브랜치/머지 없음
- 파일 whitelist 격리. worktree 없음
- 워커 = codex exec 백그라운드 프로세스. tmux 의존 없음
- 워커 출력 = `result.json` 파일 (스키마 고정). stdout.log는 보조
- 워커는 커밋 금지. lead 일괄 커밋

## 참조

- `references/backpressure-pattern.md` — backpressure + fresh context 패턴
- `references/preflight-checklist.md` — 빌드 전 체크리스트
- `references/security-rules.md` — 보안 규칙
- `templates/build-plan.md` — 사람 읽는 계획서 포맷
- `templates/worker-inbox.md.tmpl` — 워커 inbox 포맷
- `plugin/scripts/ax-build-orchestrator.sh` — orchestrator (precheck/init/spawn/status/logs/cleanup)
- `plugin/agents/planner.md` — 계획 + 파일 분할 + glue 태스크 에이전트
- `../ax-execute/SKILL.md` — 워커 프로토콜 엔진 (codex 스킬, `$ax-execute`)
- `../ax-codex/SKILL.md` — codex 스킬 동기화
- `../ax-design/SKILL.md` — 디자인 필요 시 호출
- `../ax-qa/SKILL.md` — QA 넘기기
- `../ax-review/SKILL.md` — code review (Codex 위임)

## Final Checklist

- [ ] 0단계 precheck 통과
- [ ] 1단계 plan.json 오너 승인 (glue 태스크 분리 확인)
- [ ] 2단계 version branch + 폴더 승격
- [ ] `kind: common` 태스크 순차 완료
- [ ] 병렬 라운드 루프에서 모든 task 완료 (glue 포함)
- [ ] 모든 result.json `status: done` + lead 일괄 커밋 + placeholder 스캔 통과
- [ ] 4단계 오너 통합 확인 완료
- [ ] 워커 cleanup
- [ ] `/ax-qa` 안내
