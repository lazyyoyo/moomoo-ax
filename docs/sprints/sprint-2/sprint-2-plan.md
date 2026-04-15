# sprint-2 plan (초안)

**목표**: team-ax 플러그인 **v0.2** 배포 — `define`의 **Phase B 부트스트랩** + **복수 제품 버전 분리 감지** + **의존성 분석** 도입.

> sprint-1(플러그인 v0.1)이 Phase A(분석) + Phase C(수정 사이클)를 구현한 상태를 전제로 한다. 본 문서는 플러그인 v0.2 범위의 뼈대 초안이며, sprint-1 종료 후 리파인한다.

## 용어

| 용어 | 의미 | 예시 |
|---|---|---|
| **제품 버전** | team-ax 플러그인이 적용되는 외부 IT 제품의 버전 (semver) | rubato `v1.7.0` |
| **플러그인 버전** | team-ax 플러그인 자체의 버전 | team-ax `v0.2` (이번 스프린트 목표) |

> 본 plan에서 `versions/vX.Y.Z/`, `cycle/X.Y.Z`, worktree 경로 등은 모두 **제품 버전**을 가리킨다.

## 범위 (플러그인 v0.2)

- **Phase B 부트스트랩** — 제품 버전명 확정 직후 자동 실행되는 결정적 부트스트랩 단계. 산출물:
  - `versions/undefined/` → `versions/vX.Y.Z/` 폴더 승격 (rename 또는 신규 생성 후 이동)
  - `cycle/X.Y.Z` 사이클 브랜치 생성 (main 또는 의존 브랜치에서 분기)
  - `../{repo}-X.Y.Z` **worktree 생성** (`git worktree add`)
- **분리 감지 (제품 버전 분리)** — Phase A에서 JTBD가 하나로 묶이지 않을 때 ("And 없는 한 문장" 실패) 복수 제품 버전 후보로 쪼개고, 각 제품 버전에 대해 Phase B + Phase C를 순차 실행.
- **의존성 분석** — 복수 제품 버전 간 관계 판정 + scope.md `§ 의존성` 섹션 채우기:
  - **독립**(independent) — 파일 교차 없음, 기능 선후 없음 → 병렬 가능
  - **파일 중복**(file-overlap) — 같은 spec/코드 파일 수정 → merge 충돌 예상
  - **기능 선행**(functional-dep) — A 배포 후에만 B가 의미 있음 → 순차
  - **상호 배타**(mutex) — 같은 문제에 대한 다른 해법 → 한쪽 폐기
- **scope.md `§ 의존성` 섹션 추가** — 각 scope.md에 의존 타입·대상 제품 버전 명시.
- (선택) **의존성 그래프 요약 문서** — `versions/graph.md` 또는 인덱스. 전체 제품 버전 관계 조감용.

## 비범위 (플러그인 v0.3+)

- Worktree 기반 **병렬 실행 오케스트레이션** — 독립 제품 버전을 동시에 build. 플러그인 v0.3+ build 단계 설계 시.
- 의존성 그래프 기반 **merge 순서 관리** — 파일 중복 / 기능 선행 케이스의 자동 rebase·대기. 플러그인 v0.3+ deploy 단계.
- 상호 배타 제품 버전의 A/B 실측 게이트 (PROJECT_BRIEF 장기 비전).

## 메모 — 병렬의 두 축

병렬은 두 차원으로 존재한다. 플러그인 v0.2 설계 시 둘을 구분해야 함.

### 축 1 — 버전 내(intra-version) feature 병렬

하나의 제품 버전에 Story(feature) 여러 개가 있을 때, Story별로 worktree 분리 → 각자 구현 → 버전 통합 브랜치로 merge → 통합 QA → deploy.

```
cycle/1.7.0                    ← 제품 버전 통합 브랜치
 ├─ cycle/1.7.0-profile        ← Story "프로필 보기" worktree
 ├─ cycle/1.7.0-theme          ← Story "테마 변경" worktree
 └─ cycle/1.7.0-password       ← Story "비밀번호 변경" worktree
                 │ 각 Story 완료 후 merge
                 ▼
          cycle/1.7.0에서 통합 QA → deploy (v1.7.0)
```

- **Deploy 단위 = 제품 버전** (Story 단위 아님)
- scope.md §Story Map이 이 feature 분해의 SSOT

### 축 2 — 버전 간(inter-version) 병렬

여러 제품 버전을 동시에 진행. 각자 독립 worktree. 의존성에 따라 병렬/순차. 독립 배포.

```
./rubato                 ← main (define 실행 위치)
../rubato-1.7.0          ← cycle/1.7.0 worktree (버전 A)
../rubato-1.8.0          ← cycle/1.8.0 worktree (버전 B)
```

- **독립 버전은 각자 독립 PR·deploy**
- scope.md §의존성이 이 버전 관계의 SSOT

### 두 축의 합성

축 1과 축 2는 겹칠 수 있다. 예: cycle/1.7.0 내부에서 Story 2개 병렬 + 동시에 cycle/1.8.0도 다른 worktree에서 진행 → 총 3개 이상의 동시 Claude 세션.

### 책임 분담 (어느 단계가 어느 worktree를 만드는가)

| 대상 | 누가 생성 | 타이밍 |
|---|---|---|
| 제품 버전 worktree (`cycle/X.Y.Z`) | **define Phase B** (플러그인 v0.2) | 제품 버전명 확정 직후 |
| Story worktree (`cycle/X.Y.Z-story-N`) | **build 진입 시** (플러그인 v0.3+) | plan 단계에서 Story 분해 후 |

→ define은 **버전 단위 부트스트랩**까지만. Story 단위 분해·병렬은 build 소관. 이 경계를 플러그인 v0.2 스펙에 명시.

### 설계 질문 (v0.2에서 초기 결정 필요)

- Story worktree 네이밍: `cycle/X.Y.Z-story-name` vs `cycle/X.Y.Z/story-name` vs `feature/X.Y.Z-name`?
- 통합 QA는 Story merge 후 버전 브랜치에서만? 각 Story 단위 부분 QA도?
- Story 간 의존성도 파악해야 하나? (scope.md §Story Map 수준에서 표현?)
- Story 병렬 실행 중 같은 파일 수정 충돌은 어떻게?

---

## 메모 — 병렬 워크트리 오케스트레이션 (플러그인 v0.3+ 참고)

플러그인 v0.2가 "제품 버전 분리 + 버전 worktree 준비"까지 끝내면, 플러그인 v0.3+에서 다음을 구현할 수 있는 토대가 된다. (아래의 `vX.Y.Z`는 모두 **제품 버전** 예시)

### 제품 브랜치/폴더 규약

```
main (제품 리포)
 ├─ cycle/1.7.0   ← versions/1.7.0/
 ├─ cycle/1.8.0   ← versions/1.8.0/
 └─ cycle/1.9.0   ← versions/1.9.0/
```

### Worktree 배치 (제품 리포 기준)

```
./rubato              ← main (define 실행 위치)
../rubato-1.7.0       ← cycle/1.7.0 worktree
../rubato-1.8.0       ← cycle/1.8.0 worktree
```

- 각 worktree = **독립 Claude Code 세션** 실행 가능
- 워크트리 경로 규약: 리포 형제 디렉토리 + 제품 버전 suffix
- 완료 후 `git worktree remove`로 정리

### 병렬 가능성 판정 알고리즘 (플러그인 v0.3+ 설계 힌트)

1. 모든 scope.md의 `§ 의존성` 수집 → 의존성 그래프 구성
2. **독립** 노드 → worktree 분리 + 병렬 실행 후보
3. **파일 중복** 노드 → 병렬 실행 허용, 먼저 merge된 쪽 기준으로 나머지 rebase
4. **기능 선행** 노드 → 위상정렬 순서대로 직렬 실행
5. **상호 배타** 노드 → 한쪽만 채택, 나머지 scope 폐기

### Merge·Deploy 순서 (플러그인 v0.3+ deploy 설계 힌트)

- 제품 deploy는 **제품 버전별 독립 PR** → 제품 리포 main 머지
- 파일 중복: 먼저 머지된 쪽 반영 후 다른 쪽 rebase + 재qa
- 기능 선행: 선행 머지까지 대기

### 남은 질문

- 의존성 판정을 **자동** vs **오너 확인** 중 어디까지? (플러그인 v0.2에서 초기 결정)
- 브랜치 명명 규약 고정 (`cycle/X.Y.Z`? 다른 형태?)
- worktree 경로 규약 환경변수화 여부

## 상태

- [ ] sprint-1(플러그인 v0.1) 종료 후 범위 리파인
- [ ] 태스크 분해
- [ ] 구현
- [ ] 플러그인 v0.2.0 태그 + 배포
