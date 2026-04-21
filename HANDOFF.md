# HANDOFF

## v0.8.0 릴리즈 직후 — 실측 대기 + 남편분 공유 대기 (2026-04-21)

### 컨텍스트

- 오늘 sprint-8 진행 → **team-ax v0.8.0 릴리즈 완료**
- PR #9 머지 (fast-forward) → main: `b922c2a`
- 태그 `v0.8.0` push 완료, GitHub Release 생성: https://github.com/lazyyoyo/moomoo-ax/releases/tag/v0.8.0
- v0.8 코어 변경: ax-build 병렬 엔진 재설계 — worktree 제거 + codex 워커 + 파일 whitelist + 단일 브랜치
- v0.7.2 실검증에서 드러난 트러스트 다이얼로그 / worker-visibility / MCP 중복 등 5-6건은 재설계로 **자연 해소**
- 릴리즈 직후 `/ax-paperwork`로 문서 정합성 점검 + v0.7 잔재 17건 일괄 갱신
- 오너 본인이 end-to-end로 돌려본 적 없음 — 이게 next 작업

### 다음 세션에서 할 일

1. **tmux 안에서 claude 시작 (v0.7.2 때와 동일 전제)**
   ```bash
   tmux new-session -s ax
   # 그 안에서
   claude
   ```
2. team-ax 플러그인 v0.8.0 업데이트 + `/ax-codex install` 재실행
   - `~/.codex/skills/ax-execute/`에 v0.8 새 프로토콜 반영됨
3. **사전 점검**
   ```bash
   bash plugin/scripts/ax-build-orchestrator.sh precheck
   ```
   - tmux / codex / codex login / git / ax-execute 스킬 5항목 전부 OK여야 함
4. 실제 리포(rubato/yoyowiki 등)에서 `/ax-build` 시도 — 병렬 라운드 1회 완주 목표
   - planner가 `.ax/plan.json` 생성 → 오너 승인
   - `ax-workers` 윈도우에 codex 워커 pane tiled grid 배치
   - 워커들 `result.json` 수렴 → lead 일괄 커밋 → 다음 라운드 or QA
5. 문제 없으면 남편분에게 v0.8.0 릴리즈 링크 + v0.7 → v0.8 migration 가이드 공유
   - https://github.com/lazyyoyo/moomoo-ax/releases/tag/v0.8.0
   - `docs/guides/v0.7-to-v0.8-migration.md`

### 실측에서 확인할 것

- [ ] planner의 파일 whitelist 분할 품질 — 겹침 없이 2-3개 병렬 가능?
- [ ] codex 워커가 whitelist 가드 잘 지키는지 (`result.json.files_touched` vs `git status` 2중 대조)
- [ ] tmux pane tiled grid가 화면 폭에서 깨지지 않는지 (4 이상 시 codex TUI 렌더)
- [ ] lead 일괄 커밋이 태스크 단위로 깔끔하게 분할되는지
- [ ] timeout / error / blocked 실패 모드 동작 (일부러 깨뜨려서 확인)

### 알아둘 이슈 (v0.9+ 검토용)

- **heartbeat 워치독** — result.json 미작성이지만 pane은 살아있는 경우 상세 감지 (현재는 단순 timeout 30분)
- **role routing** — 태스크 종류별 모델 분기 (예: reviewer에 o3)
- **gemini 워커** — OMC 패턴 차용 가능. 현재 codex만 지원
- **공식 Claude team-mode 연동** — experimental 플래그 안정화 후 claude teammate 하이브리드 검토
- **B-AXCODEXCACHE** — `ax-codex.sh` 캐시 경로 하드코딩 버그 (기능 영향 없음)

### 참조

- PR #9 (v0.8.0): https://github.com/lazyyoyo/moomoo-ax/pull/9
- Release: https://github.com/lazyyoyo/moomoo-ax/releases/tag/v0.8.0
- sprint-8 plan: `docs/sprints/sprint-8/sprint-8-plan.md`
- sprint-8 task: `docs/sprints/sprint-8/sprint-8-task.md`
- sprint-8 build-flow 시각화: `docs/sprints/sprint-8/build-flow.html`
- v0.8 스펙: `docs/specs/parallel-dev-spec.md`
- migration 가이드: `docs/guides/v0.7-to-v0.8-migration.md`
- paperwork report (오늘): `paperwork-report.md` (임시 — 실측 후 휴지통 or BACKLOG 이관)
