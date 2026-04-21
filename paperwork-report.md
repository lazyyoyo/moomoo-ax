# Paperwork Report — 2026-04-21 (v0.8.0 릴리즈 직후)

## 요약

- 범위: team-ax 플러그인 리포 전체 문서
- v0.8.0 릴리즈로 인한 breaking change가 문서 전반에 반영 누락
- **A. 코드-문서 불일치 (v0.8 잔재): 15건**
- **B. 중복**: 0건
- **C. Stale 상태 문서**: 3건 (HANDOFF / BACKLOG / CLAUDE)
- **D. 참조 깨짐**: 0건

ax-build SKILL.md / ax-execute SKILL.md / planner.md / orchestrator.sh / parallel-dev-spec.md / migration 가이드 / CHANGELOG는 v0.8로 갱신 완료됨. 나머지 문서들이 v0.7 모델(worktree/.ax-brief/.ax-status/executor.engine)을 아직 전제하고 있음.

## A. 코드-문서 불일치 (v0.8 잔재)

### A-1. 다른 스킬 SKILL.md — v0.7 모델 전제

| 파일 | 라인 | 증상 | 조치 |
|---|---|---|---|
| `plugin/skills/ax-design/SKILL.md` | L11, L33, L35, L95, L113, L224 | worktree + `.ax-brief.md` 전제 (ax-build에서 worktree 안에서 호출되는 시나리오) | v0.8 모델로 갱신 — 단일 브랜치, inbox.md 경유, "디자인 필요" 판단은 plan 단계로 |
| `plugin/skills/ax-deploy/SKILL.md` | L21-23, L89-90, L105 | "워크트리에서 실행 → 독립 트랙 배포", `.ax-status`/`.ax-brief.md`/`git worktree remove` 정리 | v0.8 모델로 갱신 — `.ax/` 정리, worktree 언급 제거 |
| `plugin/skills/ax-help/SKILL.md` | L37, L54, L66, L71, L81-82, L89 | `executor.engine=codex` 토글 언급, `.claude/worktrees/` 진행 중 감지 | v0.8 모델 — `ax-workers` 윈도우 감지, codex 전제 |
| `plugin/skills/ax-clean/SKILL.md` | L53, L116 | `.ax-status`/`.ax-brief.md` 잔재 감지, worktree 활성 시 중단 | `.ax/workers/` 임시파일 감지, `ax-workers` 윈도우로 변경 |
| `plugin/skills/ax-paperwork/SKILL.md` | L123 | "ax-build 중 실행 금지 — 워크트리 활성 상태" | "ax-workers 윈도우 활성 시 중단" 으로 변경 |

### A-2. references / checklist — v0.7 전제

| 파일 | 라인 | 증상 | 조치 |
|---|---|---|---|
| `plugin/skills/ax-paperwork/references/paperwork-checklist.md` | L63 | `.claude/worktrees/` 활성 감지 | ax-workers 윈도우 감지로 |
| `plugin/skills/ax-clean/references/clean-checklist.md` | L64, L88 | `.ax-status`/`.ax-brief.md` 잔재 + `.claude/worktrees/` 활성 | `.ax/workers/` + ax-workers 윈도우로 |

### A-3. templates — v0.7 포맷

| 파일 | 라인 | 증상 | 조치 |
|---|---|---|---|
| `plugin/skills/ax-build/templates/build-plan.md` | L29, L32, L33, L38 | "워크트리 병렬 / version branch 순차" 포맷 | v0.8 — 파일 whitelist 기반 분할, `.ax/plan.json` 연결 |

### A-4. ax-define 계열 — worktree 전제 잔존

| 파일 | 라인 | 증상 | 조치 |
|---|---|---|---|
| `plugin/skills/ax-define/SKILL.md` | L42, L97 | "브랜치/워크트리 생성은 ax-build 소관" | "브랜치 생성은 ax-build 소관" (worktree 삭제) |
| `plugin/skills/ax-define/templates/scope.md` | L19, L85 | `.claude/worktrees/story-N/` 경로 + minor 흐름에 worktree 언급 | v0.8 반영 (파일 집합 기반) |
| `plugin/skills/ax-define/references/story-map.md` | L65 | "Story 단위가 곧 worktree 분기 단위" | "Story 단위 → plan의 파일 집합 분할 단위" |
| `plugin/skills/ax-define/references/semver.md` | L53, L59 | Phase B worktree 생성 / minor 흐름 worktree 언급 | v0.8 반영 |
| `plugin/agents/product-owner.md` | L22 | "Phase B (폴더 승격 / worktree)는 플러그인 v0.2 예정" | 현재 구현 반영 + worktree 제거 (v0.8) |

### A-5. deprecated 본문 정합성

| 파일 | 라인 | 증상 | 조치 |
|---|---|---|---|
| `plugin/agents/executor.md` | L29, L37 | deprecated 표기돼 있지만 본문에 `.ax-brief.md` 참조 유지 | 본문 첫 줄에 "⚠ DEPRECATED — v0.8 참조 이외 무시" 추가 또는 legacy 표기 |

## B. 중복

없음.

## C. Stale (현재 상태 반영 누락)

| 파일 | 증상 | 조치 |
|---|---|---|
| `HANDOFF.md` | v0.7.2 릴리즈 직후 상태로 멈춤. v0.8.0 릴리즈 사실 누락 | v0.8.0 릴리즈 완료 + 실측 대기로 갱신 |
| `BACKLOG.md` | "## ready (sprint-8 편입)" 섹션이 여전히 ready 상태. done 이관 필요 | sprint-8 섹션을 done으로 이관 |
| `CLAUDE.md` | sprint 표의 sprint-8 상태 "plan 확정 (2026-04-21)" — 이미 완료됨 | "완료 (2026-04-21) + v0.8.0 배포" |

## D. 참조 깨짐

파일 경로 링크 스캔 결과 깨진 링크 없음. `worker-inbox.md.tmpl` / `ax-build-orchestrator.sh` / sprint-8 문서 등 신규 생성물 모두 정상 참조됨.

## 수정 계획 (카테고리별 오너 게이트)

대량 수정이라 4카테고리로 분할해 승인받는다 (ax-paperwork 가드레일 #3).

### Group 1 — v0.8 잔재 갱신 (다른 스킬 SKILL.md + templates) — 8건
A-1 (5건) + A-3 (1건) + A-2 (2건)

- `plugin/skills/ax-design/SKILL.md`
- `plugin/skills/ax-deploy/SKILL.md`
- `plugin/skills/ax-help/SKILL.md`
- `plugin/skills/ax-clean/SKILL.md`
- `plugin/skills/ax-paperwork/SKILL.md`
- `plugin/skills/ax-paperwork/references/paperwork-checklist.md`
- `plugin/skills/ax-clean/references/clean-checklist.md`
- `plugin/skills/ax-build/templates/build-plan.md`

### Group 2 — ax-define 계열 (scope 템플릿 + references + product-owner) — 5건
A-4

- `plugin/skills/ax-define/SKILL.md`
- `plugin/skills/ax-define/templates/scope.md`
- `plugin/skills/ax-define/references/story-map.md`
- `plugin/skills/ax-define/references/semver.md`
- `plugin/agents/product-owner.md`

### Group 3 — 상태 문서 (HANDOFF / BACKLOG / CLAUDE) — 3건
C

- `HANDOFF.md` (v0.8.0 릴리즈 + 실측 대기 상태로)
- `BACKLOG.md` (ready sprint-8 → done 이관)
- `CLAUDE.md` (sprint-8 완료로 갱신)

### Group 4 — deprecated 본문 정리 — 1건
A-5

- `plugin/agents/executor.md` (본문에 legacy 경고 한 줄 추가)

## 처리 방침 제안

- Group 1, 2: **문서 내용 갱신** (in-place, 본문 재작성 수준)
- Group 3: **상태 이관** (in-place, 간단)
- Group 4: **경고 한 줄 추가** (최소)

총 17건 수정. 전부 문서만 건드림 (ax-paperwork 가드레일 #1 준수). 코드 변경 0건.

## 후속

- 처리 완료 후 별도 커밋으로 정리. 브랜치 `docs/v0.8-paperwork` 또는 main 직접 푸시 중 선택
- 실측 전 최종 정합성 확보 목적
