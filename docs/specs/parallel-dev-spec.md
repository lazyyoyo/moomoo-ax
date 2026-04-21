# 병렬 개발 오케스트레이션 스펙 (v0.3 구현용)

> v0.2에서 Phase B가 Story별 worktree를 생성한다. 본 문서는 그 worktree 위에서 **Story별 병렬 Claude 세션을 어떻게 실행·조율·머지하는지** 정의한다.

## 전제

- Phase B 완료 상태: version branch + Story별 worktree N개 존재
- 각 worktree에서 Claude + Codex 독립 실행 가능 (v0.2에서 검증)
- scope.md §Story Map이 Story 분해의 SSOT

## 1. 파일 의존성 분석

### 문제

Story A와 B가 같은 파일을 수정하면 머지 시 충돌 발생.

### 분석 방법

Phase C 완료 후 (§수정 계획이 채워진 상태), 각 Story의 §수정 계획에서 수정 대상 파일 목록을 추출한다.

```
Story 1 → [profile.md, user.md, BACKLOG.md]
Story 2 → [theme.md, BACKLOG.md]
Story 3 → [password.md, user.md]
```

**교차 판정:**

| 관계 | 조건 | 대응 |
|---|---|---|
| 독립 | 파일 교차 없음 | 완전 병렬 실행 |
| 공유 파일 (비충돌) | BACKLOG.md 등 append-only 파일만 교차 | 병렬 실행, 머지 시 수동 해소 (낮은 충돌 확률) |
| 공유 파일 (충돌 예상) | 같은 spec 파일의 같은 섹션 수정 | 순차 실행 또는 선행 Story 머지 후 후행 Story rebase |

### 자동 vs 오너 확인

- **자동**: 파일 교차 탐지 + 관계 분류
- **오너 확인**: 충돌 예상 Story에 대한 실행 순서 결정

## 2. 머지 순서

### 원칙

1. 독립 Story는 어떤 순서로든 version branch에 머지 가능
2. 공유 파일이 있는 Story 쌍은 한쪽 먼저 머지 → 다른 쪽 rebase 후 머지
3. 기능 선행 관계 (Story B가 Story A의 결과를 전제)는 A 먼저 머지

### 머지 흐름

```
story-1 ──완료──→ version/vX.Y.Z에 머지
story-2 ──완료──→ rebase (story-1 반영) → version/vX.Y.Z에 머지
story-3 ──완료──→ rebase (story-1+2 반영) → version/vX.Y.Z에 머지
                                           ↓
                                    통합 QA → main 머지 → 배포
```

### 충돌 해소

- 자동 rebase 성공 → 바로 머지
- 자동 rebase 실패 (conflict) → 오너에게 충돌 파일 보고 + 해소 방법 제안

## 3. Story별 태스크 계획

### Story → 구현 태스크 분해

각 Story에 대해 ax-define Phase C(§수정 계획)가 이미 spec 수준 태스크를 정의한다. Build 단계에서는 이를 **구현 태스크**로 변환:

| spec 수준 (§수정 계획) | 구현 수준 (Build) |
|---|---|
| `profile.md` 갱신 — 프로필 카드 시나리오 추가 | 컴포넌트 구현 + API + 테스트 |
| `theme.md` 신규 — 테마 변경 시나리오 | 페이지 구현 + 스토리지 + 테스트 |

### worktree 컨텍스트 전달

각 worktree의 Claude 세션에 전달해야 하는 정보:

| 항목 | 소스 |
|---|---|
| 이 Story의 JTBD 기여 | scope.md §JTBD |
| 이 Story의 태스크 목록 | scope.md §Story Map > 해당 Story |
| 수정 대상 spec 파일 | scope.md §수정 계획 (이 Story 대응 행만) |
| 다른 Story와의 파일 교차 | 의존성 분석 결과 |
| version branch 이름 | Phase B 출력 |

### 세션 실행 방식 (후보)

| 방식 | 장점 | 단점 |
|---|---|---|
| 수동 (`cd worktree && claude`) | 유연, 오너가 각 세션 관찰 가능 | N개 터미널 수동 관리 |
| 스크립트 (`ax-build` 스킬) | 자동화, 컨텍스트 자동 전달 | 구현 복잡도 |
| 서브에이전트 (`isolation: worktree`) | Claude Code 네이티브, 정리 자동 | 커스텀 worktree 위치 불가 (Phase B가 이미 만든 것과 별도) |

> v0.3 초기에는 **수동 방식**으로 시작하고, 패턴이 안정되면 `ax-build` 스킬로 코드화 (Progressive Codification).

## 미결 사항

- [ ] Story 간 기능 선행 관계를 어떻게 표현할지 (scope.md에 섹션 추가? 별도 파일?)
- [ ] 통합 QA의 범위와 실행 방법
- [ ] 병렬 세션 수 제한 (토큰 비용 / API 동시 호출 한도)
- [ ] Story 완료 기준 — 테스트 통과? 코드 리뷰? 둘 다?
