# sprint-8 plan

**목표**: team-ax 플러그인 **v0.8.0** 배포 — ax-build 병렬 엔진 재설계. worktree 제거 + Codex 워커 N개 + 파일 whitelist 격리 + 단일 브랜치 단순화.

> v0.7.2 실검증(2026-04-21)에서 현 구조(git worktree + claude 워커 N개 + tmux window)의 근본적 한계가 드러남. (1) tmux window는 한 번에 1개만 보여서 "병렬 모니터링" 효용 낮음 (B-AXBUILD-WORKER-VISIBILITY), (2) 워커가 전부 Claude라 N배 토큰 소비, (3) trust dialog / MCP 중복 부팅 / brief 주입 등 부대 이슈 다수.
>
> 공식 Claude Code `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 및 OMC(`oh-my-claudecode`) 팀 스킬을 조사한 결과, 우리 규모에는 둘 다 오버킬. 목표가 "build 단계 병렬 속도 극대화 + Claude 토큰 절약"이면 최소 구조로 재설계 가능:
>
> - **lead**: Claude main session 1개 (orchestration, git, 커밋, 머지)
> - **워커**: Codex one-shot N개 (executor 역할 전담, 토큰 부담 이관)
> - **격리**: worktree 대신 **파일 whitelist** (planner가 파일 집합 단위로 태스크 분할, 겹침 없으면 병렬/겹치면 순차)
> - **브랜치**: 단일 `version/vX.Y.Z` (워커별 브랜치/머지 개념 제거)
> - **프로토콜**: 파일시스템만 (`.ax/workers/<id>/inbox.md` + `result.json`). 공식 team-mode MCP 프로토콜 / OMC `omc team api` 게이트웨이 CLI 불필요 — one-shot + pre-assigned라 claim/release/send-message 쓸 일 없음
> - **가시성**: tmux pane split grid (한 윈도우 안에 워커들 pane으로, 한눈에 관찰)

OMC에서 검증된 패턴 중 우리 구조에 맞는 것만 이식: inbox.md 파일 프로토콜, 워커 preamble(금지 목록), pre-assigned ownership, result.json(verdict) 스키마, tmux pane grid. 이식 안 하는 것: `omc team api` CLI, claim/release, SendMessage/mailbox, heartbeat 워치독(v0.9+ 검토), gemini 지원(v0.9+ 검토), role routing(v1.0+).

## 범위 (10건)

### 1. B-ORCHESTRATOR-V2 — ax-build-orchestrator.sh worktree 제거 리팩토링

`plugin/scripts/ax-build-orchestrator.sh`를 단일 브랜치 + tmux pane grid 모델로 재작성.

**제거:**
- `git worktree add` / `remove` 호출 전부
- `version/vX.Y.Z-<name>` 워커 브랜치 생성/머지 로직
- 워커 worktree 디렉토리 관리

**신규/변경:**
- `version/vX.Y.Z` 단일 브랜치 생성/체크아웃만
- tmux 윈도우 1개(`ax-workers`) 안에 `tmux split-window`로 워커 pane N개 배치
- 워커별 `.ax/workers/<id>/` 디렉토리 초기화 (inbox.md / result.json 자리)
- 기존 `.ax-brief.md`, `.ax-status` 폐기 (아래 B-WORKER-INBOX / B-WORKER-POLL로 대체)

**B-AXBUILD-CLAUDENATIVE(inbox) 처리**: worktree 폐기로 `claude --worktree --tmux` 빌트인 검토 자체가 불필요. 백로그에서 제거.

### 2. B-FILE-WHITELIST-PLAN — planner 에이전트 파일 분할 책임

`planner` 에이전트에 "태스크를 파일 경로 집합으로 분할" 책임 추가.

**산출물:** `.ax/plan.json`
```json
{
  "version": "vX.Y.Z",
  "tasks": [
    { "id": "T1", "title": "...", "files": ["src/a.ts", "src/b.ts"], "blockedBy": [] },
    { "id": "T2", "title": "...", "files": ["src/c.ts"], "blockedBy": ["T1"] }
  ]
}
```

**규칙:**
- 태스크 간 `files` 겹침 없음 → 병렬 후보
- 겹침 or 논리 의존(리팩토링 → 사용처 수정) → `blockedBy` 선언, 순차
- 공유 파일(타입 정의 등)은 planner가 "공통 기반" 태스크로 별도 분리 → 최우선 순차 실행 (sprint-7 영역 침범 가드의 공통 기반 개념 승계)
- 분할 불가능한 전역 리팩토링은 단일 태스크 1워커 순차로 폴백

**오너 게이트:** planner가 `.ax/plan.json` 초안 생성 후 오너 승인 단계. 분할 품질 낮으면 병렬 효과 반감하므로 초기엔 수동 게이트 유지.

### 3. B-WORKER-INBOX — 워커별 inbox.md 프로토콜

`.ax-brief.md`(단일 공유) 폐기 → 워커별 `.ax/workers/<id>/inbox.md` 신설.

**역할 분담:**
- **inbox.md = 과제 단위 입력** (워커마다 다름)
- **ax-execute SKILL.md = 워커 프로토콜 엔진** (모든 워커 공통, codex 스킬로 주입 — B-AXEXECUTE-REPOSITION 참조)

preamble/whitelist 가드/TDD/result.json 스키마 등 **공통 룰은 ax-execute SKILL.md에 고정**. inbox는 과제 본문만 담음. 프로토콜 변경 시 ax-execute 한 곳만 갱신.

**inbox.md 구성 (과제 단위만):**
- 태스크 ID + 제목 + 지시 본문 (scope/plan에서 추출)
- **파일 whitelist** — 건드려도 되는 경로 목록 (planner가 결정)
- `result.json` 저장 경로
- (옵션) 과제별 힌트 — 참고 파일, 기존 패턴, 테스트 위치 등

**result.json 스키마 (ax-execute SKILL.md에 고정):**
```json
{
  "task_id": "T1",
  "status": "done | blocked | error",
  "summary": "1-2 sentences",
  "files_touched": ["src/a.ts"],
  "notes": "optional — blockers, TODO, owner input 필요 등"
}
```

**B-AXBUILD-BRIEF-INJECT(inbox) 처리**: 주입 방식 재설계 이슈는 inbox.md + ax-execute 스킬 분리 구조로 자연 해결. 백로그에서 제거.

### 4. B-CODEX-WORKER-SPAWN — Codex one-shot 워커 스폰

tmux pane split 후 각 pane에 Codex CLI 기동.

**스폰 명령 (워커당):**
```bash
codex --dangerously-bypass-approvals-and-sandbox --model <model> \
  "/ax-execute .ax/workers/<id>/inbox.md"
```

`/ax-codex install`(v0.7)로 이미 `~/.codex/skills/ax-execute/`에 동기화된 ax-execute 스킬이 워커 프로토콜을 담당. inbox.md는 과제 단위 입력만.

**설정:**
- 기본 워커 수: 2~3 (plan 분할 결과에 따름)
- 최대 워커 수: 5 (tmux pane 좁아져서 codex TUI 깨짐 리스크)
- 모델: 기본 `gpt-5-codex` (프로젝트 `.claude/settings.json` `codex.model` 토글 가능)
- 인증: 호스트에 `codex` CLI 설치 + 로그인 전제 (B-CODEX-PRECHECK에서 검증)

**B-AXBUILD-TRUST-DIALOG(inbox) 처리**: 워커가 claude 아니라 codex로 바뀌므로 Claude trust dialog 무관 → 자동 해소. 백로그에서 제거.

**B-AXBUILD-MCP-SHARE(inbox) 처리**: codex는 MCP 호출 안 함 → 중복 부팅 이슈 자동 해소. 백로그에서 제거.

### 5. B-WORKER-POLL — lead 폴링 루프

lead(Claude main session)가 `.ax/workers/*/result.json`을 주기적으로 확인.

**동작:**
- 폴링 간격: 10초 (초기값, 필요 시 조정)
- 모든 워커 `status: done` → 수렴 → 다음 단계(커밋/머지)
- 1개라도 `status: error` → 즉시 중단 + 오너 보고 + 해당 태스크 수동 처리 유도
- `status: blocked` → notes 읽어서 오너 보고 (외부 답변 필요 등)
- **timeout** (기본 30분, 태스크당) 초과 + result.json 미작성 → 오너 알림 + `tmux kill-pane` 후 순차 재시도 옵션 제시

**가시성:**
- lead는 폴링 중 statusline/로그에 요약 표시 (`workers: 2 done / 1 in-progress / 0 error`)

### 6. B-COMMIT-STRATEGY — lead 일괄 커밋

워커는 작업만, lead가 일괄 커밋.

**흐름:**
1. 모든 워커 수렴 확인
2. lead가 `result.json.files_touched` 집계 + `git status --porcelain` 대조 → 범위 일치 검증
3. 범위 밖 파일 발견 시 즉시 보고(영역 침범 가드 2중 검증 — 워커 preamble + lead 검증)
4. 태스크 단위 커밋 (워커별 1개 or 논리 단위 묶어서 1-2개) — lead가 판단
5. 커밋 메시지: 태스크 ID + 제목 + 주요 변경 요약 (한글)

**이유:** 워커가 각자 커밋하면 git index race + 커밋 순서 비결정. lead 일괄 커밋이 단순하고 재현 가능.

### 7. B-WORKER-VISIBILITY-PANE — tmux pane grid

`B-AXBUILD-WORKER-VISIBILITY`(inbox) 해소.

**구현:**
- tmux 윈도우 1개(`ax-workers`)에 `split-window -h/-v`로 pane N개 그리드 배치
- 레이아웃: `tiled` (워커 2~5 기준 자동 타일링)
- 각 pane = 1워커 codex TUI
- 메인 윈도우(lead Claude)는 별도 유지 — 오너는 워커 관찰 시 `Ctrl-b {n}`으로 이동

**폴백:**
- 워커 수 5 초과 또는 pane 폭 < 40 columns → 경고 + "tmux 창 크기 확대 권장" 안내 + 스폰은 진행
- tmux 환경 없으면 에러 exit (sprint-7에서 이미 tmux 전제 박음)

**statusline 요약:** 메인 statusline에 `.ax/workers/*/result.json` 집계 표시 (옵션)

### 8. B-CODEX-PRECHECK — ax-build 진입 시 Codex 환경 검증

`plugin/skills/ax-build/SKILL.md` 사전 점검 확장.

**검사:**
- `codex --version` exit code 0 + 버전 출력
- `codex auth status` (또는 등가 명령) — 로그인 확인
- 미설치/미로그인 시 즉시 중단 + 설치 명령 출력:
  ```
  npm install -g @openai/codex
  codex login
  ```

**sprint-7 B-AXBUILD-TMUX-PREREQ 강화**: tmux 중첩(`tmux new-session` in tmux) 경고 처리도 여기서 함께 — 이미 tmux 안이면 새 세션 생성 스킵, 현재 세션에 윈도우 추가. `B-AXBUILD-TMUX-NESTED`(inbox) 해소.

### 9. B-AXEXECUTE-AS-PROTOCOL — ax-execute 스킬을 워커 프로토콜 엔진으로 확장

**확정 방향**: ax-execute는 **모든 codex 워커의 공통 프로토콜 엔진** 역할을 맡는다. ax-build는 워커마다 codex를 `/ax-execute <inbox>` 형태로 스폰 → 1워커 수동 호출(`/ax-execute some-inbox.md`)과 동일 진입점.

**ax-execute SKILL.md 확장 (v0.8):**
- 입력: inbox 경로 인자 (`$1` 또는 codex 스킬 호출 규약)
- 동작:
  1. inbox.md 읽기 (태스크 ID, 지시, whitelist, result.json 경로)
  2. **whitelist 가드** — 범위 밖 파일 편집 금지
  3. **preamble 강제 문구** (내재):
     - NEVER spawn sub-agents / use Task tool
     - NEVER run tmux orchestration
     - NEVER commit / push (lead가 일괄 커밋)
  4. TDD / backpressure / 영역 침범 가드 — sprint-7 5종 유지
  5. 작업 완료 시 `result.json` 작성 (스키마는 B-WORKER-INBOX 참조)
  6. `git status` self-check — whitelist 밖 변경 발견 시 `status: error`로 기록
  7. 종료 (커밋/푸시 안 함)

**장점:**
- DRY — inbox 템플릿에 preamble 복제 불필요
- 프로토콜 변경 시 ax-execute 한 곳만 갱신
- 단일/병렬 진입점 통일 (`/ax-execute <inbox>`)
- v0.7 `/ax-codex install` 인프라 승계 — 새 인프라 불필요

**sprint-7과의 차이:**
- v0.7 ax-execute: `executor.engine=codex` 토글 시 전체 plan을 codex 1개가 받아 처리 (커밋 포함)
- v0.8 ax-execute: inbox 1개 = 1태스크 단위 실행, 커밋은 lead 담당

v0.7의 "전체 plan 받아서 커밋까지" 사용 사례는 breaking change. 릴리즈 노트 명시 + migration 안내.

### 10. B-DOC-UPDATE — 관련 문서 일괄 갱신

- `plugin/skills/ax-build/SKILL.md` — 병렬 흐름 재작성, pane 모델 반영, codex 전제 명시
- `plugin/skills/ax-execute/SKILL.md` — 위상 재정비 반영
- `plugin/agents/planner.md` — 파일 whitelist 분할 책임 추가
- `plugin/agents/executor.md` — 현 역할/폐기 여부 결정 (executor.engine=codex가 기본이면 claude executor는 legacy/fallback)
- `AGENTS.md` — Codex conductor/worker 규약 정리
- `docs/specs/parallel-dev-spec.md` — v0.8 모델로 재작성 (워크트리 언급 제거)
- `README.md` / `docs/guides/*` — codex 설치 전제 안내 추가

## 비범위

- **gemini 워커 지원** — v0.9+. OMC는 지원하지만 현 목표(토큰 절약 + 병렬 속도)엔 codex만으로 충분
- **공식 Claude team-mode 연동** — v0.9+. claude teammate를 섞어 쓰고 싶을 때 검토
- **heartbeat 워치독 + 자동 재할당** — v0.9+. v0.8은 단순 timeout(30분) + 오너 알림
- **role routing(`.claude/omc.jsonc` 스타일)** — v1.0+. 역할별 모델/provider 분기가 필요해질 때
- **ax-deploy v2 묶음** (B-TRACKTYPE/B-WTHOST/B-VERCELIGN/B-CLEANUPPR) — **sprint-9 후보** (v0.7 sprint-7에서 미뤄둔 항목 유지)
- **statusline 누락 기능 8종** (B-SL-*) — sprint-9+ 후보 (ax-build 재설계와 무관)
- **B-AXCODEXCACHE** — ax-codex 캐시 경로 버그, 기능엔 영향 없음. sprint-9+ 정리 묶음으로

## 성공 기준

**병렬 엔진 코어:**
- [ ] `version/vX.Y.Z` 단일 브랜치 위에서 Codex 워커 2~3개 병렬 실행 1회 완주
- [ ] worktree 디렉토리/브랜치 생성 없음 (`git worktree list` 결과 메인만)
- [ ] 각 워커가 자기 whitelist 밖 파일 건드리지 않음 — 워커 preamble + lead git status 대조 2중 검증 통과
- [ ] lead가 모든 워커 수렴 감지 → `result.json` 집계 → 일괄 커밋 → 다음 단계 자동 진행
- [ ] 1개 워커 error/timeout 시 오너 알림 + 중단 흐름 동작

**가시성:**
- [ ] tmux `ax-workers` 윈도우에 워커 pane grid로 배치, 오너가 한눈에 N개 워커 진행 관찰 가능
- [ ] statusline(옵션)에 워커 진행 요약 표시
- [ ] 메인 윈도우(lead Claude)는 별도 유지, 오너 대화 흐름 깨지지 않음

**Codex 통합:**
- [ ] ax-build 진입 시 codex 미설치/미로그인 환경에서 친절한 에러 + 설치 안내
- [ ] codex 모델 토글 (`.claude/settings.json` `codex.model`) 동작
- [ ] ax-execute 단일 워커 진입점 유지 — ax-build가 내부적으로 재사용

**회귀 방지:**
- [ ] v0.7.x `executor.engine=claude` 경로 — legacy 지원 유지 여부 결정 + 동작 검증 (또는 명시적 제거 + 릴리즈 노트)
- [ ] sprint-7 영역 침범 가드(5종) 새 구조에서도 유효
- [ ] sprint-7 preflight fix / statusline v2 / wireframe 기능 회귀 없음

**문서 정합성:**
- [ ] ax-build/ax-execute SKILL.md + planner/executor 에이전트 + parallel-dev-spec 모두 v0.8 모델 반영
- [ ] 워크트리 관련 언급 전부 제거 (spec/README/guide)
- [ ] codex 설치 전제 README/guide에 명시

**실환경 검증:**
- [ ] 오너 환경(iTerm+tmux+Mac) 1회 완주
- [ ] 남편분(my-agent-office) 환경에서도 1회 완주 — codex 설치 포함 부트스트랩 가이드 확인

## 리스크

- **파일 분할 품질**: planner가 겹치지 않게 잘 분할해야 병렬 효과. 품질 낮으면 순차 폴백이라 효과 없음. 초기엔 오너 수동 게이트로 품질 담보.
- **codex 동작 신뢰성**: codex가 whitelist 무시/모호한 지시에 엉뚱한 파일 수정할 가능성. preamble + lead 검증 2중 가드. 사고 시 재현 로그 수집.
- **codex 긴 태스크**: 한 워커에 너무 큰 태스크 주면 TUI 스크롤/타임아웃. 태스크 크기 가이드(토큰/파일 수 상한) 문서화.
- **pane 폭 제한**: 모니터 좁거나 워커 많으면 pane에서 codex TUI 깨짐. 경고 + 최대 5 워커 권장.
- **기존 사용자 breaking change**: v0.7.x worktree 흐름 의존하던 사용자(남편분 포함)에게 breaking. 릴리즈 노트에 명시 + migration 안내.

## 상태

- [x] BACKLOG 수집 (v0.7.2 실검증 + worker-visibility 추가 — 본 plan에 편입)
- [x] 공식 team-mode + OMC 팀 스킬 분석 완료
- [x] sprint-8 범위 합의 (worktree 제거 + codex 워커 + 파일 whitelist)
- [ ] 태스크 분해 (sprint-8-task.md)
- [ ] 구현
- [ ] 검증 (오너 환경 + 남편분 환경)
- [ ] v0.8.0 태그 + 배포
