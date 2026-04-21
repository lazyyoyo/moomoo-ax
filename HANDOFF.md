# HANDOFF

## v0.8.3 hotfix 진행 중 (2026-04-21)

### 컨텍스트

- v0.8.0 sprint-8 릴리즈 → v0.8.1(모델 하드코딩+window split) → v0.8.2(pane→백그라운드 전환) → 재 paperwork → **v0.8.3(사고 기록/외부 제품/시간축 주석 제거)**
- PROJECT_BRIEF §6 원칙 재확립 — 스킬 본문은 현재 규칙만, 사고/히스토리/제품 예시는 CHANGELOG/회고/BACKLOG로
- skill-creator 활용해 static audit 1회 실시 (eval 실행 없음). 발견 포인트 중 기능 영향 있는 건 v0.8.3 반영, 나머지는 BACKLOG v0.8.4+ 후보로 이관

### 현재 상태

- 브랜치 `hotfix/v0.8.3` (커밋 대기)
- 수정 파일 약 20건 — 스킬/에이전트/references/template/README/CHANGELOG/BACKLOG/paperwork-report
- 오너 지시: **PR 생성 후 머지 전 대기**

### 다음 세션에서 할 일

1. v0.8.3 PR 검토 → 머지 → 태그 + Release (오너 승인 시)
2. 제품 리포에서 team-ax v0.8.3 업데이트 + `/ax-codex install` 재실행
3. 실제 `/ax-build` 1회 완주 재시도 — 동시 라운드 self-check 오판정 해소 확인, glue 태스크 사각지대 해소 확인
4. 남편분에게 v0.8.3 릴리즈 공유 + migration 가이드 링크

### BACKLOG 이관 항목 (v0.8.4+ 후보)

- B-SCRIPTS-RESOLVE — 다른 스킬의 `plugin/scripts/` 경로 systematic resolve (ax-build만 `$ORCH` 패턴)
- B-DESIGN-GATE-CODIFY — ax-design 게이트 자동 재작업 로직 script 이관
- B-AXHELP-DEPRECATED — ax-help 보조 스킬 목록에서 deprecated executor 제외

### 참조

- Release v0.8.0 ~ v0.8.2: https://github.com/lazyyoyo/moomoo-ax/releases
- PR #9 (sprint-8), #10 (paperwork v0.8 1차), #11 (v0.8.1), #12 (v0.8.2)
- migration: `docs/guides/v0.7-to-v0.8-migration.md`
- spec: `docs/specs/parallel-dev-spec.md`
