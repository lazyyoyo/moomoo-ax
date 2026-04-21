# CHANGELOG

team-ax 플러그인 변경 이력. [semver](https://semver.org/lang/ko/) 준수.

## v0.8.2 — 2026-04-21 (hotfix)

v0.8.0 rubato 실검증 8건 피드백 반영. **워커 실행 모델을 tmux pane split → 백그라운드 프로세스 + 로그 파일**로 근본 단순화. tmux 의존 제거, pane 관리 복잡성 전부 소멸.

### Changed (core)
- **워커 실행 모델 단순화** — `tmux split-window`로 워커 pane 띄우던 것을 제거하고 `codex exec`를 **백그라운드로 직접 기동**. stdout/stderr은 `.ax/workers/<id>/stdout.log`, pid는 `.ax/workers/<id>/pid`, 종료 코드는 `.ax/workers/<id>/exit_code`에 기록.
  - tmux 의존 제거 — iTerm/Ghostty/VS Code 어느 터미널에서든 동작
  - pane title race, `remain-on-exit` ambiguous, `{last}` 경쟁조건 등 **전부 자연 소멸**
  - 로그가 파일로 보존돼 종료 후 디버깅 가능
  - 가시성: lead `status` 집계 + 필요 시 `logs <task_id>` 또는 `tail -f`

### Added
- `logs` 서브커맨드 — `bash orchestrator.sh logs <task_id> [-f]`로 워커 stdout 조회 (`-f`는 tail follow)
- `exit_code` 파일 — 비정상 종료 감지용 (exit_code 있고 result.json 없으면 lead가 error로 처리)
- **재개 모드** (`ax-build` §2.5단계) — version branch + plan.json + 일부 커밋이 이미 존재할 때 미완료 태스크만 스폰하는 재진입 절차 명시
- **planner glue 태스크 규칙** — placeholder→실체 교체, A/B 연결 등 경계 작업을 `kind: glue` 독립 태스크로 분리. 파일 whitelist 격리의 사각지대 해소. (rubato T3-8 ↔ T3-9 재현)
- **lead 검증에 placeholder/TODO 스캔 훅** — 3-e에서 이번 라운드 변경 파일에 `grep -nE 'Placeholder|TODO|FIXME'` → 잔존 시 오너 보고

### Fixed
- **ax-execute 동시 라운드 self-check 오판정** — 병렬 라운드에서 타 워커가 만든 untracked 파일을 자기 whitelist 밖으로 오인해 `status: error` 리턴하던 이슈 (rubato T3-2/T3-9/T3-10 전부 재현). 이제 `.ax/plan.json`을 읽어 **모든 task whitelist 합집합**을 인지. (내 whitelist 밖이면서 다른 task whitelist에도 없는 파일)만 진짜 침범.
- **타겟 기반 backpressure** — 전역 `npm run lint` / `npm test`가 기존 오류 / Missing script로 항상 실패하던 이슈. 이제 변경 파일 타겟 `npx eslint <files>`, test script 부재 시 `npx vitest run` / `npx jest` 자동 폴백. 환경 실패(command not found 등)는 `blocked`, 코드 실패는 `error`로 구분.
- **SKILL.md 스크립트 경로 resolve** — `bash plugin/scripts/...`가 설치된 플러그인 환경에서 경로 불일치하던 이슈. SKILL.md 본문에 `$ORCH` resolve 가이드 추가 (설치된 캐시 경로 자동 탐색).

### Removed
- tmux 관련 로직 전부 — `prepare-window`는 no-op 하위호환만 남김, `set-option remain-on-exit`, `split-window`, `select-pane`, pane tag 전부 제거
- v0.8.1에서 이미 해결된 항목(`-c model=` 기본 주입, pane_count=1 분기)은 자연 유지

### Docs
- `docs/specs/parallel-dev-spec.md` — 전면 재작성. 백그라운드 프로세스 모델, glue 태스크, 재개 모드 반영. §breaking change 섹션 제거(이제 CHANGELOG+migration guide로 역사 일원화)
- `plugin/skills/ax-build/SKILL.md` — 워커 기동 / 가시성 / 검증 훅 / 재개 모드 / 경로 resolve 가이드 재작성

## v0.8.1 — 2026-04-21 (hotfix)

v0.8.0 실검증에서 발견된 3건 수정.

### Fixed
- **모델 하드코딩 제거** — `ax-build-orchestrator.sh`가 `-c model='gpt-5-codex'`를 주입했으나 `gpt-5-codex`는 존재하지 않는 모델명. 워커가 바로 실패. 이제 `-c model=` 옵션을 **주지 않고** codex CLI 기본값(`~/.codex/config.toml`의 `model`)을 사용. `AX_CODEX_MODEL` env 또는 spawn 3번째 인자로만 오버라이드.
- **워커 pane이 보이지 않던 이슈** — v0.8.0은 별도 `ax-workers` tmux window에 pane tiled split했으나, 사용자가 `Ctrl-b w`로 전환해야 보여 v0.7.2 worker-visibility 이슈 재현. 이제 **메인 window를 수직 split**해서 왼쪽 pane=lead(claude main), 오른쪽 pane=워커들(추가 spawn 시 수평 split)로 배치. 오너가 한 화면에서 전부 관찰 가능.

### Changed
- `orchestrator.sh` 서브커맨드 간소화 — `prepare-window` 제거(spawn이 알아서 메인 window split 처리). 하위 호환을 위해 no-op으로 허용.
- 워커 pane 식별 태그 → `ax:<task_id>` prefix로 표준화. `cleanup` 및 상태 감지에서 `ax:` prefix로 필터.

### Docs
- 문서 전반에서 "v0.8부터 바뀌었다" 류의 시간축 주석 제거. 현재 상태만 서술하고 역사는 CHANGELOG와 `docs/guides/v0.7-to-v0.8-migration.md`, `docs/specs/parallel-dev-spec.md §호환성` 섹션에만 남김. (PROJECT_BRIEF §6 "시간 축 본문 금지" 원칙 복원)
- `ax-build` SKILL.md §가시성 / §3-c 흐름 / 참조 섹션을 메인 window split 모델에 맞게 재서술
- `ax-execute` SKILL.md 호출 예시의 `gpt-5-codex` 하드코딩 제거

## v0.8.0 — 2026-04-21

**ax-build 병렬 엔진 재설계 (breaking).** worktree 제거 + Codex 워커 N개 + 파일 whitelist 격리 + 단일 브랜치. lead(Claude main session)는 오케스트레이션만, 코드 작성은 전부 codex로 이관해 Claude 토큰 부담 완화 + tmux pane grid로 병렬 관찰성 확보.

v0.7.2 실검증(남편분 환경 재현 포함)에서 드러난 구조적 한계 — workertree별 tmux window는 1개씩만 보여 "병렬 모니터링" 효용 낮음, 워커가 전부 Claude라 N배 토큰, trust dialog/MCP 중복/brief 주입 등 부대 이슈 — 를 아키텍처 레벨에서 일괄 해소.

### Breaking
- `.claude/worktrees/` 워크트리 기반 병렬 흐름 전면 폐기. 단일 브랜치(`version/vX.Y.Z`) 위에서 동작
- `.claude/settings.json`의 `executor.engine: claude|codex` 토글 제거 (codex 고정, 설정값 무시)
- `.ax-brief.md` (공유 지시서) → `.ax/workers/<task_id>/inbox.md` (워커별)
- `.ax-status` (building/review-ready/...) → `.ax/workers/<task_id>/result.json` (done/blocked/error)
- `ax-execute` 스킬의 stdout `DONE`/`BLOCKED` 공식 계약 → `result.json` 파일 스키마
- `ax-execute` `--allow` / `--block` 인자 폐기 — inbox.md 내부 `whitelist`로 통합
- `ax-execute`가 태스크 단위 커밋하던 동작 제거 — **lead가 일괄 커밋**
- 워커 브랜치(`version/vX.Y.Z-<name>`) 생성/머지 로직 제거

v0.7 사용자 마이그레이션은 `docs/guides/v0.7-to-v0.8-migration.md` 참조.

### Changed
- `plugin/skills/ax-build/SKILL.md` — 5단계 흐름 재작성 (precheck → plan(파일 분할) → init → 병렬 라운드 루프 → QA). 공식 team-mode/OMC 분석 결과 반영
- `plugin/skills/ax-execute/SKILL.md` — 워커 프로토콜 엔진으로 재정의. inbox 1건 실행 + whitelist 가드 + result.json 출력 + no-commit
- `plugin/agents/planner.md` — 파일 집합 단위 태스크 분할 책임 추가. `.ax/plan.json` 스키마 + 분할 규칙 + 자체 검증 체크리스트 정의
- `plugin/scripts/ax-build-orchestrator.sh` — 원시 도구 6개(precheck/init/prepare-window/spawn/status/cleanup). worktree 관련 제거, tmux pane tiled split 도입, `codex exec '$ax-execute <inbox>'` 스폰
- `docs/specs/parallel-dev-spec.md` — v0.8 모델로 전면 재작성

### Added
- `plugin/skills/ax-build/templates/worker-inbox.md.tmpl` — 워커 과제 입력 포맷
- `.ax/plan.json` / `.ax/workers/<id>/inbox.md` / `.ax/workers/<id>/result.json` 파일 프로토콜
- `ax-workers` tmux 윈도우에 워커 pane tiled grid 자동 배치 (가시성 개선)
- `docs/guides/v0.7-to-v0.8-migration.md` — 마이그레이션 가이드 (절차/대체물/트러블슈팅)
- `docs/sprints/sprint-8/` — plan + task + build-flow.html 시각화

### Deprecated
- `plugin/agents/executor.md` — Claude legacy executor. v0.8 ax-build에서 자동 호출 경로 없음. 수동 호출만 유효. v0.9 제거 검토
- `plugin/skills/ax-build/templates/ax-brief.md` — v0.7 공유 지시서 포맷. worker-inbox.md.tmpl로 대체. v0.9 제거 검토

### 자연 해소 (구조 변경으로)
- **B-AXBUILD-TRUST-DIALOG** — 워커가 codex라 Claude trust dialog 무관
- **B-AXBUILD-MCP-SHARE** — codex는 MCP 호출 안 함
- **B-AXBUILD-BRIEF-INJECT** — inbox.md + ax-execute 스킬 분리 구조
- **B-AXBUILD-CLAUDENATIVE** — worktree 폐기로 `claude --worktree` 빌트인 검토 불필요
- **B-AXBUILD-WORKER-VISIBILITY** — tmux pane tiled grid로 해결
- **B-AXBUILD-TMUX-NESTED** — precheck에서 `$TMUX` 감지 처리

## v0.7.2 — 2026-04-21 (hotfix)

**ax-build 병렬(워크트리) 흐름 — 실동작 fix.** v0.4부터 내재된 dead code였음 (my-agent-office 재현 리포트에서 발견).

### Fixed
- `plugin/scripts/ax-build-orchestrator.sh` (line 80 근방):
  - `claude -p '...'` → `claude '...'` — `-p`(print-and-exit) 제거. 기본 인터랙티브 TUI로 동작. 기존엔 워커가 MCP 부팅 후 응답 없이 종료되던 사고
  - `tmux new-window` → `tmux new-window -d` — 자동 포커스 전환으로 오너 키 입력이 워커 stdin으로 새는 "화면 깨짐" 사고 차단
  - tmux 세션 밖에서 호출 시 WARN 스킵 → ERROR(exit 1) 승격 — 무음 실패가 버그 은폐 원인이었음
  - `.ax-brief.md` 없으면 WARN 스킵 → ERROR(exit 1)
  - 세션 레벨 `remain-on-exit on` 자동 설정 — 워커 비정상 종료 시 디버깅 흔적 유지

### Changed
- `plugin/skills/ax-build/SKILL.md`:
  - 사전 점검에 "메인 claude 세션이 tmux 안에서 기동 중인지 확인" 추가
  - §3-b 예시 코드(`tmux new-window`)를 orchestrator와 동일하게 갱신
  - `-d` / `-p` 없음 / positional prompt 세 가지 근거 설명 추가

## v0.7.1 — 2026-04-20 (hotfix)

**ax-codex 스킬 + execute → ax-execute rename.**

### Added
- `/ax-codex` 스킬 (`plugin/skills/ax-codex/SKILL.md`) + `plugin/scripts/ax-codex.sh` — codex 위임 스킬 동기화 관리. 서브커맨드: `install` / `uninstall` / `status`. ax-status와 동일 패턴. 구버전 `~/.codex/skills/execute/` 자동 휴지통 이동

### Changed
- `plugin/skills/execute/` → `plugin/skills/ax-execute/` rename — team-ax 플러그인 `ax-` 프리픽스 통일. codex 호출도 `$execute` → `$ax-execute`
- `plugin/skills/ax-build/SKILL.md` — codex 엔진 호출부를 `$ax-execute`로 갱신
- `AGENTS.md` — 활성 스킬 표에 ax-execute/ax-codex 추가, 설치 안내를 `/ax-codex install`로 일원화
- `plugin/scripts/install-local-skills.sh` — deprecated stub. 내부적으로 `ax-codex.sh install`로 위임 (하위 호환)

## v0.7.0 — 2026-04-20

**statusline v2 + executor 엔진 토글 + define wireframe + preflight fix.**

### Added
- `ax-statusline.sh` v2 — CTX/5H/7D 행 + 반응형 레이아웃(L/M/S) + settings.json 토글 키(`.statusline.{ctx,5h,7d,branch}`) + stale 감지
- `plugin/scripts/fetch-usage.sh` — Anthropic OAuth quota 캐시(`/tmp/claude-usage-cache.json`, TTL 120s). my-agent-office/statusline에서 이식
- `plugin/scripts/templates/hud-wrapper.sh` — 버전 무관 statusline 래퍼. `installed_plugins.json`에서 team-ax 경로 런타임 resolve (플러그인 업데이트 시 재설치 불필요)
- `/ax-status` 스킬 + `plugin/scripts/ax-status.sh` 통합 엔진 — install / uninstall / toggle / on / off / show. 글로벌 `~/.claude/settings.json` `statusLine.command` 교체 + 백업 자동 생성 + 토글 키 기본값 주입
- `/execute` 스킬 (`plugin/skills/execute/SKILL.md`) — codex가 직접 실행하는 코드 구현 스킬. TDD/backpressure/영역 침범 가드 포함. 출력 첫 줄 `DONE` / `BLOCKED: {이유}`
- `plugin/skills/ax-define/templates/wireframe.html` — Phase C 13단계 wireframe 템플릿 (단일 정적 HTML, 디자인 없음 가드)
- scope.md `§ 화면 정의` 섹션 — 화면 ID/주요 영역/상태 변형/다음 화면 표준 (wireframe 입력)
- ax-define Phase C 13단계 — wireframe.html 생성 게이트 (오너 AskUserQuestion, 기본 미생성)

### Changed
- `plugin/agents/executor.md` — Constraint #12 영역 침범 가드 추가 (차단 영역 명시 + git status self-check + 임의 되돌리기 금지 + 공유 파일 사전 처리). Investigation Protocol/Failure Modes/Final Checklist 동기화
- `plugin/agents/ux-designer.md` — 두 모드 분기(`flows-and-components` / `wireframe-only`). wireframe-only는 색상/폰트/컴포넌트 가드 6종
- `plugin/skills/ax-build/SKILL.md` — `executor.engine: claude | codex` 토글 (`.claude/settings.json`). claude는 기존 executor 에이전트, codex는 `$execute` 스킬. 영역 침범 가드(#12)와 공유 파일 처리(#13) 가드레일 추가
- `plugin/skills/ax-build/templates/ax-brief.md` — 허용/차단 영역 섹션 추가, 완료 조건에 self-check 명시
- `plugin/scripts/install-local-skills.sh` — `execute` 스킬도 `~/.codex/skills/`로 동기화
- `plugin/scripts/deploy-preflight.sh` — 버그 3종 fix (rubato admin 도그푸딩 피드백):
  - spec 경로 자동 탐지 (`docs/specs/` 하드코딩 제거 → `find` 기반, dev/docs/specs/ 같은 subdirectory 인지)
  - `grep -c` 다중 결과 안전 처리 (`safe_grep_count` 헬퍼, `[[: 0\n0` syntax error 제거)
  - 본 트랙 scope 한정 마커 검사 (`git diff` 기반, 다른 도메인 잔재 무시)
  - § 화면 정의 섹션 검사 추가 (T6 동기화)
  - macOS bash 3.2 호환

### Deferred (v0.8+)
- `ax-review pr` 타입 본격 구현
- Hook 기반 자동 강제 (PreToolUse)
- 의존성 그래프 기반 머지 순서 자동화
- ax-deploy v2 묶음 (rubato admin 도그푸딩 피드백 4건):
  - track-type 메타 분기 (product/admin/infra)
  - worktree 환경 호환성 (gh pr merge 에러 + 임시 worktree 패턴)
  - Vercel "Ignored Build Step" 인지
  - cleanup PR 패턴 명문화
- 도그푸딩 실측 1회 (별도 세션)

## v0.6.0 — 2026-04-18

**문서/디렉토리 품질 관리 + 환경 정리.**

### Added
- `ax-paperwork` 스킬 — 문서-코드 정합성 탐지 + 중복/stale/참조깨짐 점검 + in-place 갱신 (오너 게이트 포함)
- `ax-clean` 스킬 — 미사용 파일/고아 문서/QA잔재 탐지 + 휴지통 이동 (`mv ~/.Trash/`, `rm` 금지)
- `plugin/scripts/paperwork-inventory.sh` — 문서 인벤토리 스캔
- `plugin/scripts/clean-scan.sh` — 정리 후보 탐지
- `plugin/scripts/ax-statusline.sh` — team-ax 전용 statusline (repo/branch/sprint/version/worktree)
- `docs/guides/plugin-compatibility.md` — team-design/team-product 충돌 해소 가이드

### Changed
- `.claude/settings.json` — 프로젝트 전용 statusLine 등록 (글로벌 설정 override)
- `README.md` — 플러그인 충돌 섹션 추가

### Deferred (v0.7+)
- `ax-review pr` 타입 본격 구현
- Hook 기반 자동 강제 (PreToolUse)
- 대시보드 연동 (오너 개입/토큰/iteration 지표)
- 도그푸딩 1회 실측 — 별도 세션에서 진행, 피드백은 hotfix 또는 후속 버전 반영

## v0.5.1 — 2026-04-18

**hotfix.** ax-deploy 잔재 정리에 브랜치 삭제 추가.

## v0.5.0 — 2026-04-18

**전 사이클 완성 + 도그푸딩 피드백 반영.**

- `ax-deploy` 스킬 — 산출물 확인 → CHANGELOG → PR → preview → 오너 승인 → 머지+태그 → 배포 → 정리
- `ax-qa` 강화 — product-qa 수준 (인벤토리 + Playwright + Visual + Viewport + axe-core + Lighthouse + 오너 게이트)
- tmux 세션 자동 생성 수정
- `ax-help` 스킬 — 스킬 목록 + 실행 순서 + 현재 상태 감지
- ax-build 속도 개선 — 파일 경로만 전달 + 작업 단위 diff + 동일 사유 2회 오너 위임

## v0.4.0 — 2026-04-17

**ax-build + ax-qa + ax-review code. 개발팀 역할 전체 사이클.**

- `ax-build` 스킬 (7단계 플로우) + orchestrator + planner / executor 에이전트
- `ax-qa` 스킬 — 통합 테스트 + code review
- `ax-review code` 타입 구현 (stub 해소)
- Phase B를 `ax-define`에서 `ax-build`로 이동

## v0.3.x — 2026-04-16

- v0.3.0: `ax-design` 스킬 신규 — 8단계 컴포넌트 확정 → 조합 플로우. ux-designer / design-builder 에이전트, DS 게이트, CheckEval, 훅 자동 주입
- v0.3.1 / v0.3.2: hotfix

## v0.2.0 — 2026-04-16

**Phase B 인프라 + 버전 전략 재설계 + 병렬 개발 설계.**

- `phase-b-setup.sh` — Phase A 산출물 커밋 → 폴더 승격 → version branch → Story별 worktree 생성
- 버전 전략 재설계 — minor(Story 분해) + patch(hotfix) 이원 체계
- `docs/specs/parallel-dev-spec.md` — 병렬 Build 오케스트레이션 설계

## v0.1.x — 2026-04-15

- v0.1.0: `ax-define` + `ax-review` (doc 구현, code/pr stub). product-owner / analyst 에이전트
- v0.1.1: Phase A 구조 개선 (interview 분리, 산출물 3개로 축소, AskUserQuestion 가드)
- v0.1.2: ax-review doc 평가 대상 한정 규칙 추가
