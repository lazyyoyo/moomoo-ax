# CHANGELOG

team-ax 플러그인 변경 이력. [semver](https://semver.org/lang/ko/) 준수.

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
