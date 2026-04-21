# 병렬 개발 오케스트레이션 스펙

v0.8 재설계: worktree를 제거하고 단일 브랜치 위에서 **파일 whitelist 격리**로 codex 워커 N개를 병렬 실행한다. 워커는 **백그라운드 프로세스**로 돌고 stdout은 로그 파일로 저장된다. tmux 의존 없음.

## 설계 목표

- **build 단계 최대 속도** — 병렬 가능한 태스크는 병렬로
- **Claude 토큰 부담 최소화** — 워커는 codex, lead(Claude)는 오케스트레이션만
- **격리 비용 최소화** — worktree/브랜치/머지 대신 파일 whitelist
- **환경 호환성** — tmux/pane 의존 없이 어떤 터미널에서도 동작
- **디버깅 용이성** — 워커 stdout/exit code가 파일로 보존되어 사후 조회 가능

## 구성 요소

```
lead (Claude main session)
  ├─ planner agent            → .ax/plan.json (파일 분할 + glue 태스크)
  ├─ orchestrator script      → version branch / 백그라운드 워커 기동 / 상태 집계
  ├─ polling + commit         → result.json 수집 + whitelist 대조 + placeholder 스캔 + 일괄 커밋
  └─ workers (codex exec × N) → /ax-execute <inbox.md> (백그라운드 프로세스, stdout→stdout.log)
```

- **단일 브랜치** `version/vX.Y.Z` — 워커 브랜치/머지 없음
- **파일 프로토콜** — `.ax/plan.json`, `.ax/workers/<id>/{inbox.md, result.json, stdout.log, pid, exit_code}`
- **lead 커밋** — 워커는 커밋 금지, lead가 result.json 집계 후 일괄 커밋

## 1. 파일 집합 단위 태스크 분할 (planner)

### 원칙

태스크의 병렬 가능성은 **파일 집합 겹침 여부**로 판정한다.

```
Task A → files: [src/admin/timeseries/**, src/api/timeseries/route.ts]
Task B → files: [src/admin/users/**,      src/api/users/route.ts]
Task C → files: [src/types/timeseries.ts, src/types/users.ts]  (공유)
```

- A ∩ B = ∅ → **병렬 가능**
- A ∩ C ≠ ∅ → C를 공통 기반(`kind: common`)으로 분리, A는 `blockedBy: [C]`

### 분할 규칙

| 관계 | 조건 | 대응 |
|---|---|---|
| 독립 | `files` 교차 없음 | 같은 라운드에 병렬 |
| 공유 파일 | 여러 task가 같은 타입/DB/유틸 수정 필요 | `kind: common`으로 분리. 최우선 순차 |
| 논리 의존 | B가 A의 함수/타입에 의존 | `B.blockedBy: [A]` |
| 경계 연결 | A가 만든 컴포넌트를 B의 호출부에 연결 (placeholder 교체 등) | `kind: glue` 별도 분리. 양쪽 완료 후 실행 |
| 파일 겹침 | 같은 파일 다른 변경 | 병합 또는 `blockedBy` |
| 분할 불가 | 전역 리팩토링 등 | 단일 task 1워커 폴백 |

### kind 3종

- **`common`** — 공통 기반 (타입/DB/공유 유틸). 최우선 순차. 다른 모든 task의 `blockedBy`에 들어감
- **`task`** — 일반 병렬 가능 태스크
- **`glue`** — 연결 태스크. 경계 작업이 독립 태스크로 분리됨. 양쪽 완료 후 실행

### glue 태스크의 이유

파일 whitelist 격리의 구조적 약점: 경계 연결 작업이 사각지대가 된다. 예:

- T-a: `library/page.tsx`에 placeholder 렌더 (whitelist: `library/**`)
- T-b: `shelves-grid.tsx` 신규 생성 (whitelist: `components/shelves/**`)
- 필요한 glue: placeholder를 ShelvesGrid로 교체 — 어느 워커도 못함

→ planner가 `kind: glue` 태스크로 분리, `blockedBy: [T-a, T-b]`로 걸어 마지막 라운드에 실행.

### planner 자체 검증

`.ax/plan.json` 작성 후 체크:

- 모든 task에 `files` 존재 (비어있지 않음)
- task 간 `files` 겹침 스캔 → 겹치면 `blockedBy` 필수
- `kind: common`은 모든 다른 task의 `blockedBy`에 포함
- `blockedBy` 사이클 없음
- 태스크 쌍에 경계 연결이 필요하면 `kind: glue` 분리 여부

## 2. 실행 단위 — 병렬 라운드

### 라운드 선정

`.ax/plan.json`에서 이번 라운드 태스크 집합 추출:

1. 미완료
2. `blockedBy` 전부 완료
3. 우선순위: `common` > `task` > `glue` (common이 하나라도 있으면 그 라운드는 common 1개만)
4. 최대 5

### 워커 기동

```bash
bash "$ORCH" spawn vX.Y.Z <task_id> [model]
```

내부적으로:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write \
  '$ax-execute .ax/workers/<task_id>/inbox.md' \
  > .ax/workers/<task_id>/stdout.log 2>&1 &
```

- **백그라운드** 실행, pid는 `.ax/workers/<task_id>/pid`에 저장
- 종료 후 exit code는 `.ax/workers/<task_id>/exit_code`에 기록
- stdout/stderr 전부 `stdout.log`로 redirect — 종료 후에도 조회 가능
- 모델: 기본 codex CLI 설정. `AX_CODEX_MODEL` env 또는 spawn 3번째 인자로 오버라이드

### 폴링 + 수렴

```bash
bash "$ORCH" status
```

15초 간격. 집계 예:
```
total=3 done=2 blocked=0 error=0 running=1 pending=0
```

판정:
- 모두 `done` → lead 검증 + 커밋
- `error` → 중단 + 오너 보고
- `blocked` → 오너 개입
- **비정상 종료** (exit_code 있고 result.json 없음) → `logs <task_id>`로 원인 파악
- **timeout** (pid 살아있는데 result.json 미작성, 30분) → `cleanup` + 재시도 결정

### lead 검증 + 일괄 커밋

1. `result.json.files_touched` 집계
2. `git status --porcelain`과 대조 → whitelist 밖 변경 탐지 (**2중 가드**: 워커 self-check + lead 검증)
3. **placeholder/TODO 잔존 스캔** — 이번 라운드 변경 파일에 `grep -nE 'Placeholder|TODO|FIXME'` → 발견 시 오너 보고, glue 태스크로 다음 라운드 or 즉시 수동 수정
4. 태스크 단위 커밋, 커밋 메시지 한글

### 라운드 루프

완료 task를 `.ax/plan.json`에서 마킹, 다른 task의 `blockedBy`에서 해제. 남은 task가 있으면 라운드 선정으로 돌아감.

## 3. 워커 계약 (ax-execute)

워커는 **codex exec 백그라운드 프로세스**. 프로토콜 엔진은 `plugin/skills/ax-execute/SKILL.md`가 담당한다.

### 입력

`inbox.md` 경로 인자 1개. 필수 필드:
- `task_id`, `title`, `instructions`
- `whitelist` — 편집 허용 파일/디렉토리 glob
- `result_path` — result.json 저장 경로
- (옵션) `hints`

누락 시 워커는 `result.json.status = error`로 즉시 종료.

### 출력

**공식 계약 = `result.json` 파일**:

```json
{
  "task_id": "T1",
  "status": "done | blocked | error",
  "summary": "1-2 문장",
  "files_touched": ["src/a.ts"],
  "notes": "optional"
}
```

**보조 = `stdout.log` 파일** — 디버깅용 전체 stdout/stderr.

### 금지 사항 (워커 preamble)

- sub-agent / Task tool 호출
- 스크립트가 아닌 직접 tmux 조작
- `git commit` / `git push`
- whitelist 밖 파일 편집
- `git reset` / `git checkout --` / `git stash` (임의 revert)

### 동시 라운드 인지 self-check

병렬 라운드에서 다른 워커가 같은 repo에 동시에 파일을 만든다. 자기 `git status`에 **타 워커 산출 파일이 untracked로 잡힘**. 이걸 whitelist 밖으로 오판정 금지.

**3분류:**
1. 내 whitelist 매치 → 정상
2. `.ax/plan.json`의 다른 task whitelist 매치 → 타 워커 영역 (OK)
3. 어디에도 없음 → 진짜 침범 (`status: error`)

### 타겟 기반 backpressure

전역 lint/test 금지 (기존 오류로 막힘). 변경 파일 타겟:
- typecheck: 표준 `tsc --noEmit`
- lint: `npx eslint <files>` 변경 파일만
- 테스트: `package.json scripts.test` 있으면 타겟 지정 실행 (`npm test -- <pattern>`), 없으면 `npx vitest` / `npx jest` 자동 폴백
- 빌드: 변경이 빌드 타깃에 영향 있을 때만

환경 실패(Missing script / command not found)와 코드 실패를 구분. 환경 실패는 `blocked`, 코드 실패는 error.

## 4. 가시성

- **메인 세션** (lead) — 오너 대화 + polling 요약 (`N done / M running`)
- **워커 로그** — `bash "$ORCH" logs <task_id>` 또는 직접 `tail -f .ax/workers/<id>/stdout.log`
- **result.json** — 공식 상태. lead가 항상 참조
- tmux/pane 의존 없음 — 어떤 터미널에서도 동작

## 5. 실패 모드

| 모드 | 감지 | 대응 |
|---|---|---|
| 워커 `status: error` | result.json 파싱 | 중단, 오너 보고, notes 출력 |
| 워커 `status: blocked` | result.json 파싱 | 오너 개입 (외부 답변, 공유 파일 미처리 등) |
| 비정상 종료 | exit_code 있고 result.json 없음 | stdout.log 로그 확인, 원인 파악 |
| timeout | pid 살아있는데 result.json 미작성 30분 | cleanup + 재시도 결정 |
| whitelist 밖 변경 | lead git status 대조 | 중단, 오너 보고, revert 금지 |
| placeholder 잔존 | lead grep 스캔 | glue 태스크 추가 or 즉시 수동 수정 |
| 분할 불가능 | planner 판단 | 단일 task 1워커 폴백 (오너 승인) |

## 6. 재개 (resume)

이전 세션에서 ax-build가 도중에 끊긴 경우:

1. `git checkout version/vX.Y.Z`
2. `.ax/plan.json` 존재 확인 — 없으면 plan 재생성
3. `status`로 각 워커 현재 상태 점검
4. 라운드 선정 논리로 미완료 태스크만 재스폰
5. lead가 오너에게 재개 계획을 먼저 보고

재개 시 `.ax/workers/<id>/result.json`의 존재 + 커밋 history가 완료 판단의 근거.

## 7. 미결 사항 (후속 검토)

- **heartbeat 워치독** — result.json 미작성이지만 프로세스 살아있을 때 상세 감지. 현재는 단순 timeout
- **role routing** — 태스크 종류별 모델 분기
- **gemini 워커** — 현재 codex만 지원
- **공식 Claude team-mode 연동** — experimental 플래그 안정화 시 하이브리드 검토
- **MCP 서버 공유** — codex 측 MCP가 필요해질 때

## 8. 참조

- `plugin/skills/ax-build/SKILL.md` — lead 흐름
- `plugin/skills/ax-execute/SKILL.md` — 워커 프로토콜
- `plugin/agents/planner.md` — 파일 분할 + glue 태스크
- `plugin/scripts/ax-build-orchestrator.sh` — 원시 도구 (precheck/init/spawn/status/logs/cleanup)
- `plugin/skills/ax-build/templates/worker-inbox.md.tmpl` — inbox 포맷
- `docs/guides/v0.7-to-v0.8-migration.md` — 마이그레이션 가이드
- CHANGELOG — 버전별 breaking change 이력
