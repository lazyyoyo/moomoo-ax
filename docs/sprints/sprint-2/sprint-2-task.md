# sprint-2 태스크

## T0. 사전 정리 — 분리 감지 폐기

SKILL.md/references에서 "복수 버전 분리" 관련 로직 제거 + "하나의 minor + Story 분해"로 교체.

- [ ] `references/jtbd.md` — "두 관심사 묶이면 제품 버전 쪼갠다" → "하나의 minor에 Story로 분해"
- [ ] `references/slc.md` — "제품 버전을 쪼개기 (분리 감지)" → "Story를 더 작게 쪼개기"
- [ ] `SKILL.md` 가드레일 11번 "Phase B 액션 금지" → 삭제 (Phase B 구현되므로)

## T1. phase-b-setup.sh 스크립트

Phase A 산출물 커밋 → 폴더 승격 → version branch → Story별 worktree 생성.

- [ ] scope.md에서 Story 제목 파싱 (`### Story N:` 패턴)
- [ ] `versions/undefined/` → `versions/vX.Y.Z/` rename + 커밋
- [ ] version branch 생성 (main에서 분기)
- [ ] Story별 worktree 생성 (`.claude/worktrees/story-N/`)
- [ ] 완료 시 worktree 경로 목록 stdout 출력 (SKILL.md가 파싱)

## T2. SKILL.md Phase B 구현

- [ ] Phase B 섹션을 "건너뜀"에서 실제 동작으로 교체
- [ ] Phase A 완료 → 자동 커밋 → `phase-b-setup.sh` 호출 → Phase C 진입 흐름 기술
- [ ] Phase C 진입 조건: worktree 존재 확인
- [ ] 출력 섹션 업데이트 (Phase B 산출물 추가)
- [ ] 11단계 codex 호출 경로 업데이트 (`versions/vX.Y.Z/scope.md`)

## T3. scope.md 템플릿 + doc-checklist 갱신

- [ ] `templates/scope.md` §버전 메타 — worktree 경로 표기 갱신 (`.claude/worktrees/` 기반)
- [ ] `templates/scope.md` §버전 전략 섹션 추가 (minor/patch 구분)
- [ ] `doc-checklist.md` — diff 기준을 version branch 기점으로 변경

## T4. 버전 전략 — minor/patch 이원 체계 명시

- [ ] `SKILL.md` Phase A 3단계 JTBD 판정 — "한 문장 실패 → 분리" 삭제, "하나의 minor + Story 분해" 명시
- [ ] `references/semver.md` — minor/patch 흐름 분기 명시 (patch = hotfix 브랜치, minor = version branch)

## T5. parallel-dev-spec.md 작성 (설계 문서)

v0.3 Build 오케스트레이션 구현을 위한 스펙. 코드 없음.

- [ ] 파일 의존성 분석 — Story 간 파일 교차 탐지 방법
- [ ] 머지 순서 — 의존 관계 기반 순서 결정 로직
- [ ] Story별 태스크 계획 — Story → 구현 태스크 분해 + worktree 컨텍스트 전달 방식

## T6. 릴리즈

- [ ] plugin.json + marketplace.json 버전 bump (0.1.2 → 0.2.0)
- [ ] BACKLOG.md done 섹션에 sprint-2 기록
- [ ] 커밋 + 태그

## T7. 도그푸딩

대상: yoyowiki 또는 rubato. Story 2개 이상 나오는 minor 버전으로 실행.

### 검증 기준

**Phase A (기존 동작 유지)**

| # | 기준 | PASS 조건 |
|---|---|---|
| A1 | intake/interview/scope.md 3파일 생성 | `versions/undefined/`에 3개만 존재 |
| A2 | JTBD 한 문장 | scope.md §JTBD에 "And 없는 한 문장" 통과하는 문장 |
| A3 | Story Map 2개 이상 | scope.md §Story Map에 `### Story N:` 2개 이상 |
| A4 | 버전명 오너 승인 | AskUserQuestion으로 확인 라운드트립 발생 |

**Phase B (신규)**

| # | 기준 | PASS 조건 |
|---|---|---|
| B1 | Phase A 산출물 자동 커밋 | `git log`에 Phase A 커밋 존재 |
| B2 | 폴더 승격 | `versions/vX.Y.Z/` 존재 + `versions/undefined/` 없음 |
| B3 | version branch | `git branch`에 version branch 존재 |
| B4 | Story별 worktree | `.claude/worktrees/story-N/` 디렉토리가 Story 수만큼 존재 |
| B5 | worktree 내용 일치 | 각 worktree에서 `versions/vX.Y.Z/scope.md` 접근 가능 |

**Phase C (worktree 격리 검증)**

| # | 기준 | PASS 조건 |
|---|---|---|
| C1 | Phase C가 worktree에서 실행 | analyst의 `pwd`가 `.claude/worktrees/` 하위 |
| C2 | main working tree 무변경 | main에서 `git status`가 Phase C 변경사항 미포함 |
| C3 | diff 기준 정상 | ax-review doc이 version branch 기점으로 diff — §수정 계획 외 파일 미평가 |
| C4 | Codex 정상 실행 | `codex exec` 호출이 worktree 경로에서 성공 |

**통합**

| # | 기준 | PASS 조건 |
|---|---|---|
| I1 | A→B→C 무중단 | 오너 개입 = 인터뷰 응답 + 버전명 승인 + §수정 계획 승인 (3회만) |
| I2 | 최종 산출물 | scope.md 8섹션 모두 채워짐 + §리뷰 APPROVE |

---

**의존 순서**: T0 → T1 → T2 → T3/T4 (병렬) → T5 → T6 → T7
