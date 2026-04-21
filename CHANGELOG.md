# CHANGELOG

team-ax 플러그인 변경 이력. [semver](https://semver.org/lang/ko/) 준수.

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
