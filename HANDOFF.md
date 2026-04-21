# HANDOFF

## v0.7.2 릴리즈 직후 — 실전 검증 + 남편 공유 대기 (2026-04-21)

### 컨텍스트

- 오늘 hotfix v0.7.1(ax-codex + execute rename) + v0.7.2(ax-build 병렬 흐름 fix) 2건 연달아 릴리즈
- v0.7.2는 남편분(my-agent-office) 재현 리포트 발견 → `-p` 제거 + `-d` 추가 + tmux 전제 강화
- 코어 fix는 programmatic 검증 통과 (별도 테스트 repo에서 orchestrator 직접 호출)
- **오너 본인이 end-to-end로 돌려본 적 없음** — 이게 next 작업

### 다음 세션에서 할 일

1. **tmux 안에서 claude 시작** — 현재 iTerm은 tmux 밖이었음
   ```bash
   tmux new-session -s ax
   # 그 안에서
   claude
   ```
2. 실제 리포(rubato/yoyowiki 등)에서 `/ax-build` 시도 — 3-b 워크트리 병렬 흐름 1회 완주 목표
3. 문제 없으면 남편분에게 v0.7.2 릴리즈 링크 + 주의사항 공유
   - https://github.com/lazyyoyo/moomoo-ax/releases/tag/v0.7.2

### 알아둘 이슈 (BACKLOG inbox)

- **B-AXBUILD-TRUST-DIALOG**: 첫 워크트리 진입 시 "trust this folder?" 다이얼로그 뜸. 오너가 수동 `1 Enter` 눌러야 진행됨. `-p` 제거의 부작용. 자동화 완결하려면 v0.7.3으로 후속 fix 필요.
- **B-AXBUILD-TMUX-NESTED**: 이미 tmux 안인데 `tmux new-session` 또 치면 경고. 사전 점검 가이드 보강 필요.

### 참조

- PR #7 (v0.7.1): https://github.com/lazyyoyo/moomoo-ax/pull/7
- PR #8 (v0.7.2): https://github.com/lazyyoyo/moomoo-ax/pull/8
- 재현 리포트 원본: `~/Downloads/moomoo-ax-build-parallel-issue-2026-04-21.md`
- BACKLOG inbox — ax-build 후속(CLAUDENATIVE/BRIEF-INJECT/MCP-SHARE/TRUST-DIALOG/TMUX-NESTED) + ax-codex 캐시 경로 버그 + statusline 8건
