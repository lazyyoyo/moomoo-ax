# 병렬 개발 오케스트레이션 스펙 (v0.8)

> v0.7까지 이 문서는 Story별 worktree + Claude 병렬 세션을 기술했다. **v0.8부터 워크트리는 제거**되고 단일 브랜치 위에서 **파일 whitelist 격리**로 codex 워커 N개를 병렬 실행한다. 본 문서는 v0.8 기준으로 전면 재작성된 사본이다.

## 설계 목표

- **build 단계 최대 속도** — 병렬 가능한 태스크는 병렬로
- **Claude 토큰 부담 최소화** — 워커는 codex, lead(Claude)는 오케스트레이션만
- **격리 비용 최소화** — worktree/브랜치/머지 대신 파일 whitelist
- **오너 관찰성** — tmux pane grid로 모든 워커를 한눈에

## 구성 요소

```
lead (Claude main session)
  ├─ planner agent            → .ax/plan.json (파일 집합 단위 태스크 분할)
  ├─ orchestrator script      → version branch / tmux pane / codex 스폰 / 상태 수집
  ├─ polling + commit         → result.json 수집 + whitelist 대조 + 일괄 커밋
  └─ workers (codex exec × N) → /ax-execute <inbox.md> (tmux pane에서 one-shot)
```

- **단일 브랜치** `version/vX.Y.Z` — 워커 브랜치/머지 없음
- **파일 프로토콜** — `.ax/plan.json`, `.ax/workers/<id>/inbox.md`, `.ax/workers/<id>/result.json`
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
- B ∩ C ≠ ∅ → 마찬가지

### 분할 규칙

| 관계 | 조건 | 대응 |
|---|---|---|
| 독립 | `files` 교차 없음 | 같은 라운드에 병렬 스폰 |
| 공유 파일 (공통 기반) | 여러 task가 같은 타입/DB/유틸 수정 필요 | `kind: common` 태스크로 분리. 최우선 순차 처리 후 다른 태스크 스폰 |
| 논리 의존 | B가 A의 함수/타입에 의존 | `B.blockedBy: [A]` |
| 파일 겹침 | 같은 파일의 다른 변경 | 병합해서 한 task로 or `blockedBy`로 순차 |
| 분할 불가 | 전역 리팩토링 등 | 단일 task 1워커 순차 폴백 |

### planner 산출물

- `versions/vX.Y.Z/build-plan.md` — 사람 읽는 계획서
- `.ax/plan.json` — 기계 SSOT (스키마는 `plugin/agents/planner.md`)

### 자체 검증

planner가 plan.json 작성 후 자체 검증:

- 모든 task에 `files` 존재
- task 간 `files` 겹침 스캔 → 겹치면 `blockedBy` 필수
- `kind: common`은 모든 다른 task의 `blockedBy`에 포함
- `blockedBy` 그래프에 사이클 없음

오너 게이트에서 승인 후 2단계 진행.

## 2. 실행 단위 — 병렬 라운드

### 라운드 선정

`.ax/plan.json`에서 이번 라운드 태스크 집합 추출:

1. 미완료
2. `blockedBy` 전부 완료
3. `kind: common` 우선. common이 하나라도 있으면 **그 라운드는 common 1개만** (순차)
4. common 전부 끝나면 이후 라운드는 `task` 병렬 (최대 5)

### 워커 스폰

```bash
# 공통
bash plugin/scripts/ax-build-orchestrator.sh prepare-window   # 1회
bash plugin/scripts/ax-build-orchestrator.sh spawn vX.Y.Z T1
bash plugin/scripts/ax-build-orchestrator.sh spawn vX.Y.Z T2
...
```

내부적으로:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox -s workspace-write \
  -c model='gpt-5-codex' \
  '$ax-execute .ax/workers/T1/inbox.md'
```

- `ax-workers` tmux 윈도우에 pane tiled split
- pane title = task_id (구분 용이)
- `remain-on-exit on` — 비정상 종료 pane 잔존(디버깅)

### 폴링 + 수렴

```bash
bash plugin/scripts/ax-build-orchestrator.sh status
```

10초 간격. 집계 예:
```
total=3 done=2 blocked=0 error=0 in-progress=1
```

판정:
- 모두 `done` → lead 검증 + 커밋 단계로
- `error` → 즉시 중단 + 오너 보고
- `blocked` → 오너 개입 유도 (notes 기반)
- timeout 30분 → pane 로그 캡처 + 재시도 옵션

### lead 검증 + 일괄 커밋

1. `result.json.files_touched` 집계
2. `git status --porcelain`과 대조 → whitelist 밖 변경 탐지 (**2중 가드**: 워커 preamble + lead 검증)
3. 범위 밖 변경 시 즉시 중단 + 오너 보고, **임의 revert 금지**
4. 태스크 단위 커밋 (`<task_id>: <title> — <요약>` 한글)

### 라운드 루프

완료 task를 `.ax/plan.json`에서 마킹, 다른 task의 `blockedBy`에서 해제. 남은 task가 있으면 라운드 선정으로 돌아감.

## 3. 워커 계약 (ax-execute)

워커는 **codex one-shot**. 프로토콜 엔진은 `plugin/skills/ax-execute/SKILL.md`가 담당한다.

### 입력

`inbox.md` 경로 인자 1개. inbox 필수 필드:

- `task_id`, `title`, `instructions`
- `whitelist` — 편집 허용 파일/디렉토리 glob
- `result_path` — result.json 저장 경로
- (옵션) `hints`

누락 시 워커는 `result.json.status = error`로 즉시 종료.

### 출력

`result.json` 스키마:

```json
{
  "task_id": "T1",
  "status": "done | blocked | error",
  "summary": "1-2 문장",
  "files_touched": ["src/a.ts"],
  "notes": "optional"
}
```

stdout은 보조 로그. lead의 공식 계약은 **result.json 파일**.

### 금지 사항 (워커 preamble)

- sub-agent / Task tool 호출
- tmux orchestration
- `git commit` / `git push`
- whitelist 밖 파일 편집
- `git reset` / `git checkout --` / `git stash` (임의 revert)

### 가드 5종

v0.7 sprint-7에서 확정된 영역 침범 가드 유지:

1. whitelist 명시 의무 (inbox 필수)
2. 작업 전 whitelist stdout 출력
3. `git status --porcelain` self-check
4. 침범 시 `status: error` + notes, revert 금지
5. 공유 파일은 공통 기반 선행 (미처리면 `status: blocked`)

## 4. 가시성

- **메인 윈도우** (lead) — 오너 대화 + polling 요약 (`workers: N done / M in-progress`)
- **`ax-workers` 윈도우** — 워커 pane tiled grid. 오너가 `Ctrl-b w`로 이동해 진행 관찰
- **(옵션) statusline 요약** — `.ax/workers/*/result.json` 집계 값 노출

## 5. 실패 모드

| 모드 | 감지 | 대응 |
|---|---|---|
| 워커 `status: error` | result.json 파싱 | 즉시 중단, 오너 보고, notes 출력 |
| 워커 `status: blocked` | result.json 파싱 | 오너 개입 (외부 답변, 공유 파일 미처리 등) |
| timeout (result.json 미작성) | 30분 경과 | pane 로그 캡처, 오너 알림, kill-pane, 순차 재시도 옵션 |
| whitelist 밖 변경 | lead git status 대조 | 즉시 중단, 오너 보고, revert 금지 |
| 분할 불가능 | planner 판단 | 단일 task 1워커 폴백 (오너 승인) |

## 6. v0.7에서 v0.8 breaking change

| 항목 | v0.7 | v0.8 |
|---|---|---|
| 격리 | git worktree per worker | 파일 whitelist per task |
| 브랜치 | `version/vX.Y.Z` + `-<name>` 워커 브랜치 | `version/vX.Y.Z` 단일 |
| 머지 | 워커 브랜치 → version | 머지 개념 없음 |
| 워커 | claude or codex (`executor.engine`) | codex 고정 |
| 지시 | 공유 `.ax-brief.md` | 워커별 `.ax/workers/<id>/inbox.md` |
| 상태 | `.ax-status` (building/review-ready/...) | `.ax/workers/<id>/result.json` (done/blocked/error) |
| 출력 계약 | stdout `DONE` / `BLOCKED` | result.json 파일 스키마 |
| 커밋 | 워커가 태스크 단위 커밋 | lead 일괄 커밋 |
| 가시성 | tmux window 1개씩 | tmux `ax-workers` 윈도우 pane grid |
| trust dialog | claude 워커라 repo당 1회 수동 dismiss | codex는 claude trust와 무관 |
| MCP | 워커마다 MCP 중복 부팅 | codex는 MCP 미사용 → 해소 |

v0.7 사용자 migration은 `docs/guides/v0.7-to-v0.8-migration.md` 참조.

## 7. 미결 사항 (v0.9+ 검토)

- [ ] **heartbeat 워치독** — result.json 미작성이지만 pane은 살아있는 경우의 상세 감지. 현재는 단순 timeout
- [ ] **role routing** — 태스크 종류별 모델 분기 (예: 리뷰어는 o3, executor는 gpt-5-codex). OMC 패턴 차용 시
- [ ] **gemini 워커** — 현재 codex만 지원
- [ ] **공식 Claude team-mode 연동** — claude teammate도 섞을 수 있는 하이브리드. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 이 안정화된 뒤
- [ ] **MCP 서버 공유 옵션** — codex 측 MCP가 필요해질 때

## 8. 참조

- `plugin/skills/ax-build/SKILL.md` — lead 흐름
- `plugin/skills/ax-execute/SKILL.md` — 워커 프로토콜
- `plugin/agents/planner.md` — 파일 분할 책임
- `plugin/scripts/ax-build-orchestrator.sh` — 원시 도구 6종 (precheck/init/prepare-window/spawn/status/cleanup)
- `plugin/skills/ax-build/templates/worker-inbox.md.tmpl` — inbox 포맷
- `docs/sprints/sprint-8/sprint-8-plan.md` — v0.8 스프린트 계획
- `docs/sprints/sprint-8/build-flow.html` — v0.8 플로우 시각화
- `docs/guides/v0.7-to-v0.8-migration.md` — 마이그레이션 가이드
