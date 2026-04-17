# sprint-2 plan

**목표**: team-ax 플러그인 **v0.2** 배포 — Phase B 인프라 + 버전 전략 재설계 + 병렬 개발 설계.

> worktree 생성(인프라)과 버전 전략을 구현하고, 병렬 개발 오케스트레이션(파일 의존성/머지 순서/Story별 태스크 계획)은 설계 문서까지만 잡는다.

## 전제

- sprint-1(v0.1.0) + hotfix v0.1.1/v0.1.2 완료
- Phase A + Phase C 구현 완료
- `.claude/worktrees/`에서 Codex 정상 동작 검증 완료

## 범위

### 1. Phase B — worktree 인프라

Phase A 완료(버전명 확정) 직후 실행.

**동작:**
1. Phase A 산출물 자동 커밋
2. `versions/undefined/` → `versions/vX.Y.Z/` 승격
3. version branch 생성 (main에서 분기)
4. Story별 worktree 생성 (Story Map 기반, 각 Story에 1개)

| 변경 대상 | 내용 |
|---|---|
| `ax-define/SKILL.md` | Phase B 단계 추가 |
| `plugin/scripts/phase-b-setup.sh` | 폴더 승격 + 브랜치 + worktree N개 생성 |
| `doc-checklist.md` | diff 기준을 version branch 기점으로 변경 |

### 2. 버전 전략 재설계

| 구분 | minor (vX.Y.0) | patch (vX.Y.Z) |
|---|---|---|
| 트리거 | 계획된 feature 묶음 | 긴급 수정 |
| 흐름 | A → B → C → Build(병렬) → 머지 → QA → 배포 | main hotfix → 즉시 배포 |
| JTBD | 하나의 minor + Story 분해 | 해당 없음 |

- "JTBD 분리 → 복수 버전" 폐기
- patch/hotfix는 version branch와 독립 진행

| 변경 대상 | 내용 |
|---|---|
| `ax-define/SKILL.md` | JTBD 판정 규칙 변경 — "하나의 minor + Story 분해" |
| `ax-define/references/` | 분리 감지 관련 언급 제거 |
| `scope.md` 템플릿 | §버전 전략 섹션 추가 |

### 3. 병렬 개발 오케스트레이션 — 설계 문서

v0.3 구현을 위한 스펙 정의. **코드 구현 없이 설계 문서만 작성.**

| 주제 | 설계할 내용 |
|---|---|
| 파일 의존성 분석 | Story 간 파일 교차 탐지 방법, 충돌 예방 전략 |
| 머지 순서 | 의존 관계에 따른 순서 결정 로직, 충돌 시 해소 방식 |
| Story별 태스크 계획 | Story → 구현 태스크 분해 방법, 각 worktree에 전달하는 컨텍스트 |

산출물: `docs/specs/parallel-dev-spec.md` (v0.3 구현 시 SSOT)

## 비범위

- 병렬 개발 구현 (자동 실행/모니터링/머지) → v0.3
- version branch 통합 QA → v0.3
- ~~분리 감지 / 의존성 분석 (복수 버전 간)~~ → 폐기

## 성공 기준

- [ ] Phase B에서 Story Map 기반 worktree N개 자동 생성
- [ ] 각 worktree에서 독립 Claude 세션 + Codex 실행 가능
- [ ] SKILL.md/references에서 "복수 버전 분리" 완전 제거
- [ ] `parallel-dev-spec.md` 작성 완료 — v0.3 구현 착수 가능한 수준
- [ ] 도그푸딩 1회에서 A→B→C 전 구간 완주

## 상태

- [x] 범위 리파인
- [x] worktree + Codex 호환 검증
- [x] 태스크 분해
- [x] 구현
- [x] 도그푸딩 (jojo 테스트 통과)
- [x] v0.2.0 태그 + 배포
