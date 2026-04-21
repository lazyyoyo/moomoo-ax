# sprint-8 태스크

병렬 빌드 엔진 재설계 — worktree 제거 + Codex 워커 + 파일 whitelist.

## T0. 선행 조사 + 설계 확정

본격 구현 전 설계 미확정 지점 해소.

- [ ] `codex --version` / 로그인 확인 명령 실측 — precheck 조건 확정
- [ ] codex 스킬 호출 규약 확인 — `/ax-execute <path>` 슬래시 커맨드 vs positional prompt, 어느 쪽이 안정적인지 실측
- [ ] codex 기본 모델 토글 위치 결정 — `.claude/settings.json` `codex.model` (ax-build 전체 기본) vs `.ax/plan.json` 태스크별 오버라이드
- [ ] `.ax/` 디렉토리 구조 확정
  - [ ] `.ax/plan.json` — plan SSOT
  - [ ] `.ax/workers/<id>/inbox.md` — 워커 과제
  - [ ] `.ax/workers/<id>/result.json` — 워커 결과
  - [ ] `.gitignore`에 `.ax/` 추가 여부 결정
- [ ] v0.7.x `executor.engine=claude` legacy 경로 처리 결정 — 유지(옵션) vs 명시적 제거(breaking). 릴리즈 노트 반영 준비
- [ ] 설계 문서 갱신 — `docs/specs/parallel-dev-spec.md`를 v0.8 모델로 재작성

## T1. B-AXEXECUTE-AS-PROTOCOL — ax-execute를 워커 프로토콜 엔진으로 확장

모든 후속 태스크의 전제. 워커가 따르는 프로토콜 엔진.

- [ ] `plugin/skills/ax-execute/SKILL.md` 재작성 — 입력: inbox 경로 인자
- [ ] inbox.md 파서 — 태스크 ID / 지시 본문 / 파일 whitelist / result.json 경로 추출
- [ ] **whitelist 가드** — 편집 시 경로 검증, 밖이면 중단
- [ ] **preamble 강제 문구** 내재
  - [ ] NEVER spawn sub-agents / Task tool
  - [ ] NEVER tmux orchestration
  - [ ] NEVER commit / push
- [ ] TDD + backpressure 가드 (sprint-7 유지)
- [ ] 영역 침범 가드 5종 (sprint-7 유지)
- [ ] result.json 작성 — 스키마 `{task_id, status, summary, files_touched, notes}`
- [ ] `git status --porcelain` self-check — whitelist 밖 변경 발견 시 `status: error` + notes에 기록
- [ ] 종료 (커밋/푸시 안 함)
- [ ] 단일 수동 호출 동작 검증 — `/ax-execute some-inbox.md` 단독 실행
- [ ] `/ax-codex install` 동기화 확인 — `~/.codex/skills/ax-execute/`에 반영
- [ ] v0.7 전체 plan 받아 커밋까지 하던 동작 breaking 명시 (릴리즈 노트 초안)

## T2. B-FILE-WHITELIST-PLAN — planner 파일 분할

planner 에이전트 확장.

- [ ] `plugin/agents/planner.md` 갱신 — "태스크를 파일 집합 단위로 분할" 책임 추가
- [ ] `.ax/plan.json` 스키마 정의 — `{version, tasks: [{id, title, files, blockedBy, instructions}]}`
- [ ] 분할 규칙 문서화
  - [ ] 파일 겹침 없음 → 병렬
  - [ ] 겹침/논리 의존 → `blockedBy`
  - [ ] 공유 파일 → "공통 기반" 태스크로 분리 (최우선 순차)
  - [ ] 분할 불가능한 전역 리팩토링 → 단일 태스크 1워커 폴백
- [ ] planner 산출 검증 — `files` 겹침 자동 탐지 + 경고
- [ ] 오너 게이트 — plan.json 초안 승인 / 반려 / 재분할 플로우
- [ ] 샘플 케이스 드라이런 — 가상 태스크 3-5개 분할 결과 확인

## T3. B-WORKER-INBOX — inbox.md 생성 로직

lead가 plan.json → 워커별 inbox.md 생성.

- [ ] inbox.md 템플릿 작성 — `plugin/skills/ax-build/templates/worker-inbox.md.tmpl`
- [ ] 포함 필드 — 태스크 ID/제목/지시/whitelist/result.json 경로/(옵션)과제 힌트
- [ ] preamble은 inbox에 **복제하지 않음** (ax-execute SKILL.md 내재)
- [ ] 생성 스크립트 — `.ax/plan.json` → 태스크별 `.ax/workers/<id>/inbox.md` N개 일괄 생성
- [ ] 멱등성 — 재생성 시 기존 result.json 안 덮음
- [ ] 참고 파일 / 기존 패턴 힌트 주입 방식 (선택) — plan.json의 `instructions` 필드 재활용

## T4. B-ORCHESTRATOR-V2 — ax-build-orchestrator.sh worktree 제거

현 오케스트레이터 재작성.

- [ ] 현 `plugin/scripts/ax-build-orchestrator.sh` 백업 (참고용)
- [ ] **제거**
  - [ ] `git worktree add` / `remove` 호출
  - [ ] `version/vX.Y.Z-<name>` 워커 브랜치 생성/머지
  - [ ] 워커 worktree 디렉토리 관리
  - [ ] `.ax-brief.md` (단일 공유) 생성 로직
  - [ ] `.ax-status` 파일 (지금 쓰던 방식)
- [ ] **신규/변경**
  - [ ] `version/vX.Y.Z` 단일 브랜치 생성/체크아웃
  - [ ] `.ax/workers/<id>/` 디렉토리 준비
  - [ ] tmux 기동 — 이미 tmux 안이면 현재 세션 사용, 밖이면 ERROR exit (sprint-7 B-AXBUILD-TMUX-PREREQ 승계)
  - [ ] tmux 윈도우 `ax-workers` 생성 (없으면)
  - [ ] `tmux split-window` tiled 레이아웃 N pane
  - [ ] 각 pane에 codex 스폰 명령 주입 (T5)
- [ ] 회귀 방지 — sprint-7 `remain-on-exit on` 유지 (워커 비정상 종료 디버깅)
- [ ] 단일 브랜치 동작 검증 — `git worktree list` 결과가 메인만

## T5. B-CODEX-WORKER-SPAWN — Codex 워커 스폰

T4에서 분리된 스폰 로직.

- [ ] 스폰 명령 표준화 — `codex --dangerously-bypass-approvals-and-sandbox --model <m> "/ax-execute .ax/workers/<id>/inbox.md"`
- [ ] 모델 resolve — `.claude/settings.json` `codex.model` 읽기, 기본 `gpt-5-codex`
- [ ] 워커 수 제한
  - [ ] 기본 2-3 (plan 분할 결과에 따름)
  - [ ] 최대 5 (넘으면 오너에게 확인 + 진행 or 분할 재검토)
- [ ] pane 폭 검증 — 40 columns 미만이면 경고 + "창 크기 확대" 안내
- [ ] 스폰 타이밍 — N pane 준비 후 send-keys 일괄, race 방지
- [ ] 실패 탐지 — pane이 바로 종료되면 로그 캡처 + 오너 알림

## T6. B-CODEX-PRECHECK — 환경 검증

ax-build 진입 사전 점검.

- [ ] `plugin/skills/ax-build/SKILL.md` 사전 점검 섹션 확장
- [ ] codex 설치 확인 — `codex --version` exit 0 + 버전 파싱
- [ ] codex 로그인 확인 — `codex auth status` 또는 등가 (T0 실측 결과에 따라)
- [ ] 미설치/미로그인 시 출력
  - [ ] `npm install -g @openai/codex`
  - [ ] `codex login` (또는 실제 명령)
- [ ] tmux 중첩 처리 — `$TMUX` 체크해서 이미 안이면 현재 세션 사용 공지
- [ ] **B-AXBUILD-TMUX-NESTED** 해소 (BACKLOG inbox)

## T7. B-WORKER-POLL — lead 폴링 + 수렴 감지

ax-build 메인 루프.

- [ ] `plugin/skills/ax-build/SKILL.md` 폴링 로직 명시 (lead 절차)
- [ ] 폴링 간격 10초 기본 (가변)
- [ ] `.ax/workers/*/result.json` 읽기 — 전체 status 집계
- [ ] 모든 `status: done` → 수렴 → T8로
- [ ] 1개라도 `status: error` → 즉시 중단 + 오너 보고 + notes 출력
- [ ] `status: blocked` → notes 출력 + 오너 개입 유도
- [ ] **timeout** 30분 기본 — result.json 미작성 시 pane 로그 캡처 + 오너 알림 + kill-pane + 순차 재시도 옵션
- [ ] 폴링 중 statusline 또는 로그에 요약 출력 — `workers: N done / M in-progress`

## T8. B-COMMIT-STRATEGY — lead 일괄 커밋

워커 수렴 후 커밋 단계.

- [ ] `result.json.files_touched` 집계
- [ ] `git status --porcelain` 실제 변경 파일과 대조
- [ ] 범위 밖 변경 탐지 → 즉시 중단 + 오너 보고 (2중 가드: 워커 preamble + lead 검증)
- [ ] 태스크 단위 커밋 — 워커별 1개 또는 논리 묶음 1-2개 (lead 판단)
- [ ] 커밋 메시지 표준 — `<task-id>: <제목> — <주요 변경 요약>` (한글)
- [ ] 빈 워커 (done인데 files_touched 없음) → 로그만 남기고 커밋 스킵
- [ ] plan.json 업데이트 — 완료 태스크 마킹 + 다른 태스크 `blockedBy`에서 해제

## T9. B-WORKER-VISIBILITY-PANE — pane grid 가시성

B-AXBUILD-WORKER-VISIBILITY (BACKLOG inbox) 해소.

- [ ] tmux 윈도우 `ax-workers`를 `select-layout tiled`로 자동 배치
- [ ] pane 수가 1-2면 세로 split, 3+는 tiled
- [ ] 워커 수 5 초과 시 경고 + 진행 확인
- [ ] 메인 윈도우(lead Claude) 별도 유지 — `tmux list-windows`로 확인
- [ ] statusline 요약 (선택) — `.ax/workers/*/result.json` 집계 값 노출 (sprint-7 `.statusline.plugin` 토글 연동)
- [ ] `SKILL.md`에서 "window = 병렬 워커 모니터, 대화 입구 아님" 명시 수정 (sprint-7 SKILL.md L206/222)

## T10. B-ROUND-LOOP — blockedBy 해소 라운드 루프

병렬 라운드가 여러 번 돌 때.

- [ ] lead 루프 — 매 라운드 후 `.ax/plan.json`에서 다음 병렬 가능 집합 재선정
- [ ] 모든 태스크 완료 시 루프 종료 → 다음 Phase (ax-qa 전달)
- [ ] 공통 기반 태스크 식별 — 첫 라운드에서 최우선 순차 처리
- [ ] 라운드 간 상태 보존 — `.ax/plan.json`이 SSOT

## T11. B-DOC-UPDATE — 문서 일괄 갱신

- [ ] `plugin/skills/ax-build/SKILL.md` — 병렬 흐름 재작성 (본 plan + build-flow.html 기반)
- [ ] `plugin/skills/ax-execute/SKILL.md` — T1 반영 완료 확인
- [ ] `plugin/agents/planner.md` — T2 반영 완료 확인
- [ ] `plugin/agents/executor.md` — legacy 경로 처리 결정에 따라 보존/제거
- [ ] `AGENTS.md` — Codex conductor/worker 규약 정리 (lead vs 워커 역할 구분)
- [ ] `docs/specs/parallel-dev-spec.md` — v0.8 모델로 전면 재작성 (워크트리 언급 제거)
- [ ] `README.md` — codex 설치 전제 섹션 추가
- [ ] `docs/guides/` — 필요 시 migration 가이드 신규 (v0.7 → v0.8 breaking change 안내)

## T12. 검증

### T12-a (구현 중 자동화)

- [ ] ax-execute 단위 — 샘플 inbox로 단독 실행 → result.json 스키마 준수
- [ ] planner 분할 — 가상 태스크로 plan.json 출력 + 겹침 없음 검증
- [ ] orchestrator — 단일 브랜치만 생성, worktree 없음
- [ ] 워커 스폰 — pane N개 동시 기동, codex 정상 실행

### T12-b (v0.8.0 release 직후 실측)

- [ ] 본인 환경 (iTerm+tmux+Mac) — 실제 리포에서 `/ax-build` 1회 완주
- [ ] 3-4 워커 병렬 실행 확인
- [ ] whitelist 가드 동작 — 일부러 위반 inbox 투입 시 error 보고
- [ ] timeout 동작 — 긴 작업 inbox로 30분 초과 시 흐름 확인
- [ ] 남편 환경 — clean 환경에서 codex 설치 포함 부트스트랩 완주
- [ ] sprint-7 기능 회귀 없음 — statusline v2 / wireframe / preflight / ax-define/qa/deploy

## T13. 릴리즈

- [ ] `plugin.json` + `marketplace.json` 버전 bump (0.7.x → 0.8.0)
- [ ] CHANGELOG.md — v0.8.0 섹션 (병렬 엔진 재설계 + breaking change 안내)
- [ ] README.md — 위 T11 반영 확인
- [ ] BACKLOG.md — sprint-8 편입 inbox 항목 done 이관 (B-AXBUILD-WORKER-VISIBILITY, 자연 해소 6종)
- [ ] migration 가이드 — v0.7 사용자 대상 (worktree 흐름 의존 시)
- [ ] 커밋 + PR + 태그 (`v0.8.0`)

## 검증 기준

### 병렬 엔진 코어

| # | 기준 | PASS 조건 |
|---|---|---|
| C1 | 단일 브랜치 | `git worktree list` 결과 메인만 |
| C2 | 병렬 실행 | Codex 워커 2-3개가 tmux pane에서 동시 실행 |
| C3 | 파일 격리 | 워커별 whitelist 밖 파일 변경 없음 (self-check + lead 검증 2중) |
| C4 | 수렴 감지 | 모든 result.json.status=done 시 다음 단계 진입 |
| C5 | 일괄 커밋 | lead가 태스크 단위 커밋, git index race 없음 |

### 프로토콜 (ax-execute)

| # | 기준 | PASS 조건 |
|---|---|---|
| A1 | inbox 파싱 | 필드 누락 시 error 보고 + 즉시 중단 |
| A2 | whitelist 가드 | 밖 파일 편집 시도 시 차단 + result.json.error |
| A3 | preamble | commit/push/sub-agent/tmux 호출 없음 |
| A4 | self-check | git status --porcelain으로 whitelist 검증 |
| A5 | 단일/병렬 통일 | `/ax-execute <inbox>` 단독 호출도 동일 동작 |

### planner 분할

| # | 기준 | PASS 조건 |
|---|---|---|
| P1 | 파일 집합 분할 | 각 태스크 `files` 배열 산출 |
| P2 | 겹침 탐지 | 겹치는 태스크는 `blockedBy` 선언 |
| P3 | 공통 기반 | 공유 파일은 별도 태스크로 분리 |
| P4 | 오너 게이트 | plan.json 승인/반려 플로우 동작 |

### 가시성

| # | 기준 | PASS 조건 |
|---|---|---|
| V1 | pane grid | `ax-workers` 윈도우에 tiled 배치 |
| V2 | 메인 유지 | lead 윈도우 별도, 오너 대화 깨지지 않음 |
| V3 | statusline | (옵션) 워커 진행 요약 노출 |

### 환경 검증

| # | 기준 | PASS 조건 |
|---|---|---|
| E1 | codex precheck | 미설치/미로그인 시 친절한 에러 + 설치 안내 |
| E2 | tmux 중첩 | `$TMUX` 감지해 현재 세션 사용 |
| E3 | breaking 안내 | v0.7 사용자 migration 가이드 제공 |

### 실패 모드

| # | 기준 | PASS 조건 |
|---|---|---|
| F1 | error 중단 | 워커 error → 즉시 중단 + 오너 보고 |
| F2 | timeout | 30분 초과 → kill-pane + 재시도 옵션 |
| F3 | blocked | notes 기반 오너 개입 유도 |
| F4 | 범위 밖 변경 | lead 검증에서 탐지 + 중단 |

---

**의존 순서**: T0 → T1 → (T2, T3 병렬) → T4 → (T5, T6 병렬) → T7 → (T8, T9, T10 병렬) → T11 → T12 → T13

- T0 (설계 확정): 실측/결정 선행
- T1 (ax-execute 프로토콜): 모든 워커 동작의 전제
- T2 (planner) / T3 (inbox 생성): ax-execute 이후 병렬 가능
- T4 (orchestrator): T1-T3 산출 사용
- T5 (스폰) / T6 (precheck): T4 내부 병렬
- T7 (폴링): orchestrator + 스폰 완성 후
- T8-T10 (커밋/가시성/라운드): 폴링 이후 병렬
- T11 (문서) / T12 (검증) / T13 (릴리즈): 구현 완료 후 순차
