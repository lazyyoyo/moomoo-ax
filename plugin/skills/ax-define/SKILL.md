---
name: ax-define
description: "team-ax define — 제품 버전 스코프 결정 + 스펙 in-place 갱신 + plan/write/review 검증. 매 제품 버전 시작 시 실행. Use when: /ax-define, 제품 define, 버전 스코프, scope.md 작성, JTBD/Story Map/SLC 결정."
---

# /ax-define

team-ax 플러그인의 **제품 버전 시작 시 1번 실행** 스킬. 외부 IT 제품(rubato, rofan-world 등)에 적용된다.

> **두 종류의 "버전" 주의**
>
> | 용어 | 의미 |
> |---|---|
> | **제품 버전** | 본 스킬이 결정·관리하는 외부 제품의 semver (예: rubato `v1.7.0`) |
> | **플러그인 버전** | team-ax 자체의 버전 (예: team-ax `v0.1`) |
>
> 본 SKILL.md의 `versions/vX.Y.Z/`, `cycle/X.Y.Z`, `scope.md` 등은 모두 **제품 버전**을 가리킨다.

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | 적용 대상 제품 리포의 `BACKLOG.md` inbox, 기존 `docs/specs/` 전체, 오너 인터뷰 응답 |
| **출력 (플러그인 v0.1.1)** | `versions/undefined/` 하위 Phase A 산출물 **3개**(`intake.md` / `interview.md` / `scope.md`) + scope.md 8개 섹션 모두 채움 / `docs/specs/` in-place 갱신 (`⏳ planned` 마커) / `BACKLOG.md` inbox 채택 항목 제거 |

> 플러그인 v0.2 도입 후 출력에 **폴더 승격(`versions/vX.Y.Z/`)**, **`cycle/X.Y.Z` 브랜치**, **worktree**가 추가된다 (Phase B). 본 v0.1은 Phase B를 건너뛴다.

## 에이전트 / 스킬 구성

| 구성요소 | 담당 Phase | 책임 |
|---|---|---|
| `product-owner` (Claude 서브에이전트) | **Phase A 전체 (1~6)** | intake / 인터뷰 / JTBD / Story Map / SLC / 제품 버전명 결정 + scope.md 초안 |
| `analyst` (Claude 서브에이전트) | **Phase C plan + write (9·10)** | §수정 계획 / specs in-place 갱신 / BACKLOG inbox 정리 / §수정 로그 |
| `ax-review doc` (스킬 — codex 위임) | **Phase C review (11)** | §수정 계획 vs 실제 diff 대조 + 강제 장치 4종 검증 + APPROVE/REQUEST_CHANGES |

## Phase 순서 제어

```
Phase A — 범위 분석 (1~6)         → product-owner
Phase B — 부트스트랩 (7~8)        → 플러그인 v0.2 예정 (이번 스프린트 건너뜀)
Phase C — plan/write/review (9~11) → analyst (9·10) + ax-review doc (11)
```

본 v0.1은 Phase B를 **건너뛴다**. Phase A 산출물은 `versions/undefined/`에 머물고, Phase C도 같은 위치의 `scope.md`에 작성한다. 작업은 실행 시점의 현재 브랜치에서 진행.

## 동작 순서

### 사전 점검

1. 적용 대상 제품 리포의 작업 디렉토리에 있는지 확인 (`pwd`).
2. `versions/undefined/` 폴더가 없으면 생성. 이미 있으면 기존 산출물을 무시하지 않고 이어가기.
3. `BACKLOG.md`, `docs/specs/` 존재 확인. 없으면 오너에게 보고하고 중단(제품이 `/product-init` 같은 부트스트랩을 거치지 않은 경우).

### Phase A — 범위 분석 (`product-owner` 호출 + 메인 라운드트립)

> **v0.1.1 변경** — Phase A 산출물을 **3개 파일로 축소**. 3~5단계 결과는 별도 파일을 만들지 않고 scope.md 해당 섹션에 **직접 기록**. 2단계 인터뷰는 **메인 세션 라운드트립**(B안)으로 수행 — AskUserQuestion은 메인 세션에서만 안정 작동.

**산출 파일**

| 파일 | 역할 |
|---|---|
| `versions/undefined/intake.md` | 1단계 수집 노트 + 비자명 항목 목록 (재진입 시 참조) |
| `versions/undefined/interview.md` | 2단계 질문 + 오너 답 로그 (재진입 시 참조) |
| `versions/undefined/scope.md` | 3~6단계 결과가 **직접 기록되는 유일한 산출물**. Phase C 단일 입력 |

**단계별 흐름**

| # | 단계 | 입력 | 산출물 | 기록 위치 |
|---|---|---|---|---|
| 1 | 입력 수집 | `BACKLOG.md` inbox + 기존 `docs/specs/` + `PROJECT_BRIEF.md` | 수집·분석 노트 + 비자명 항목 목록 | `versions/undefined/intake.md` |
| 2 | 오너 인터뷰 (**라운드트립**) | intake의 비자명 항목 | 질문 목록 작성 → **메인 라운드트립** → 답 수신 후 채움 | `versions/undefined/interview.md` |
| 3 | JTBD 정의 | 인터뷰 + 수집 | JTBD 한 줄 ("And 없는 한 문장" 통과) | `scope.md §JTBD` (별도 파일 생성 금지) |
| 4 | Story Map | JTBD | Activity × Story 그리드 + spec 매핑 | `scope.md §Story Map` (별도 파일 생성 금지) |
| 5 | SLC 체크 | Story Map + 슬라이스 후보 | 3축 근거 한 줄씩 | `scope.md §SLC 체크` (별도 파일 생성 금지) |
| 6 | 버전명 결정 + 오너 승인 | SLC 통과 슬라이스 + `references/semver.md` | semver 판정 + 오너 승인 라운드트립 + §비범위 마감 | `scope.md §버전 메타` + `§비범위` |

**2단계 라운드트립 프로토콜 (B안)**

1. `product-owner` 서브에이전트가 `interview.md`에 질문 목록만 작성하고 return.
2. 본 SKILL.md(메인 세션)가 `AskUserQuestion`을 호출해 오너에게 묻는다.
3. 답을 받아 `interview.md` 답 섹션을 채운다.
4. `product-owner`를 3단계로 재호출 (입력: 채워진 interview.md).

> 서브에이전트 세션에서 `AskUserQuestion`은 미가용 반환되는 경우가 있으므로, 인터뷰는 **항상 메인이 수행**한다. product-owner에게는 Hard Guard로 "AskUserQuestion 실패/미가용 시 즉시 중단·자체 추론 금지"가 걸려 있다 (`agents/product-owner.md` Hard Guard 섹션).

**6단계 버전명 승인**

버전명(`vX.Y.Z`)은 `product-owner`가 후보를 제안하더라도 scope.md §버전 메타에 기록하기 전에 **메인 세션이 AskUserQuestion으로 단일 승인 라운드트립**을 돈다. 자답 금지.

> 6단계 종료 시 scope.md의 §수정 계획 / §수정 로그 / §리뷰는 **비워둔다** (Phase C 담당).

**금지 산출물**

- `versions/undefined/jtbd.md`, `story-map.md`, `slc.md` — **만들지 않는다**. 결과는 scope.md 섹션으로 수렴.
- "탈락 후보 사유표", "실패 시뮬레이션" 등 SKILL.md/references가 요구하지 않는 장식 섹션.

### Phase B — 건너뜀 (플러그인 v0.2 예정)

폴더 승격(`versions/undefined/` → `versions/vX.Y.Z/`), 사이클 브랜치(`cycle/X.Y.Z`), worktree 생성은 본 v0.1에서 수행하지 않는다. 모든 산출물은 `versions/undefined/`에 머문다.

### Phase C — plan / write / review 사이클

#### 9단계 — plan (`analyst` 호출)

`analyst`에게 §수정 계획을 작성시킨다 (`templates/scope.md` `§수정 계획` 표 포맷).

- 입력: scope.md §JTBD / §Story Map + 기존 `docs/specs/` 전수 매핑
- 출력: scope.md `§수정 계획` 표 — 파일별 변경 타입 / 변경 요약 / 매핑 근거 / 대응 태스크
- **오너 확인 게이트**: §수정 계획 표를 오너에게 보여주고 승인 받음. 승인 전에는 10단계 진입 금지.

#### 10단계 — write (`analyst` 호출)

`analyst`에게 §수정 계획 각 행을 순서대로 실행시킨다.

- 갱신/마커 → Edit + `> ⏳ planned — ...` 마커 부착
- 신규 → Write (`{기능명}.md` 형식 엄수, 접미사 금지)
- BACKLOG inbox → Edit으로 채택 항목 줄 삭제
- 각 행 실행 직후 scope.md `§수정 로그` 체크박스 체크 + 변경 파일 경로 또는 commit ref 기록

#### 11단계 — review (`$ax-review doc` 호출)

본 SKILL.md가 직접 codex에 위임:

```bash
codex exec '$ax-review doc versions/undefined/scope.md'
```

- 출력 첫 줄을 grep해 판정:
  - `APPROVE` → 12단계(완료 처리)
  - `REQUEST_CHANGES: ...` → 9단계로 되돌아가 §수정 계획 보강 후 재실행
- **출력 전체**를 scope.md `§리뷰` 섹션에 그대로 붙여넣는다 (재작업 시 새 결과로 교체).

#### 12단계 — 완료 처리

- 11단계 판정이 `APPROVE`임을 확인.
- scope.md 8개 섹션 모두 채워졌는지 self-check (§버전 메타 / §JTBD / §Story Map / §SLC 체크 / §비범위 / §수정 계획 / §수정 로그 / §리뷰).
- 오너에게 완료 보고 + define 산출물 경로 출력.

## Phase C 루프 재진입 규칙

- `$ax-review doc` 출력 첫 줄이 `REQUEST_CHANGES`로 시작하면 → 9단계(`analyst` plan)로 되돌아간다.
- 재진입 시 §수정 계획 표를 갱신하고, §수정 로그는 추가 항목만 append (기존 체크 유지).
- §리뷰 섹션은 새 출력으로 교체.
- `APPROVE` 받기 전까지 12단계 완료 처리 금지.
- 무한 루프 방지: 동일 사유로 3회 연속 `REQUEST_CHANGES`면 오너 개입 요청.

## 가드레일

1. **인터뷰 우회 금지 (v0.1.1 신설)** — 2단계는 반드시 메인 세션 라운드트립. 서브에이전트가 AskUserQuestion 실패 시 자체 추론으로 답 생성 금지. `product-owner` Hard Guard 위반 감지 시 즉시 중단.
2. **Phase A 단일 파일 원칙 (v0.1.1 신설)** — `versions/undefined/`에는 `intake.md` / `interview.md` / `scope.md` **3개만** 존재해야 한다. `jtbd.md` / `story-map.md` / `slc.md` 생성 시 위반. 3~5단계 결과는 scope.md 섹션에 직접 기록.
3. **제품 버전명 선결정 금지** — Phase A 6단계 SLC 통과 + 오너 승인 후에만 결정. 1~5단계 중 "v1.7.0 작업 중"이라 부르지 않는다.
4. **major/minor 분기 금지** — 단일 흐름. 자릿수가 무엇이든 JTBD/Story Map/SLC는 항상 수행 (스코프 크기는 결과물 분량에만 영향).
5. **JTBD/Story Map/SLC 단계 생략 금지** — minor / 패치 모음이라도 짧게라도 작성. 단계 자체를 빼면 안 됨.
6. **오버스펙 장식 금지 (v0.1.1 신설)** — scope.md 8개 섹션 외 장식("탈락 후보 사유표", "실패 시뮬레이션", "대안 분석 매트릭스" 등) 추가 금지.
7. **새 spec 파일 생성 전 매핑 탐색 의무** — `analyst`가 §수정 계획에 매핑 근거 한 줄 명시 (`references/spec-lifecycle.md` 장치 1).
8. **파일명 접미사 금지** — `-fix` / `-patch` / `-enhance` / `-redesign` / `-v2` / `.old` / `.legacy` (장치 2).
9. **시간 축 본문 금지** — spec 본문에 "v1.5에서 추가" 등 누적 기술 금지 (장치 3).
10. **spec vs CHANGELOG 분리** — 핫픽스를 신규 spec 파일로 만들지 않음. CHANGELOG는 deploy 단계 (장치 4).
11. **Phase B 액션 금지** — 폴더 승격·브랜치 생성·worktree는 플러그인 v0.2 도입 후. v0.1.x는 모두 `versions/undefined/`.
12. **review는 codex 위임만** — Claude 서브에이전트로 review를 실행하지 않는다. 작성 엔진 ≠ 검증 엔진 분리 원칙.

## 참조

- `references/jtbd.md` — JTBD 정의 + "And 없는 한 문장" 테스트
- `references/story-map.md` — Activity × Story 그리드 작성법 + rubato v1.7.0 예시
- `references/slc.md` — Simple/Lovable/Complete 3축 + 실패 처방
- `references/semver.md` — 제품 버전명(MAJOR/MINOR/PATCH) 판정 플로우
- `references/spec-lifecycle.md` — in-place 갱신 + `⏳ planned` 마커 + 강제 장치 4종
- `references/docs-structure.md` — BACKLOG / scope / CHANGELOG 3-문서 책임 분리 (ROADMAP 제거 근거 포함)
- `templates/scope.md` — scope.md 8개 섹션 템플릿
- `../ax-review/SKILL.md` — Phase C review 단계의 codex 위임 스킬
- `plugin/agents/product-owner.md` — Phase A 전담 서브에이전트
- `plugin/agents/analyst.md` — Phase C plan + write 전담 서브에이전트
