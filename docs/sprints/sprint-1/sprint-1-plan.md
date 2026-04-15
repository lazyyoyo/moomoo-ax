# sprint-1 plan

**목표**: team-ax 플러그인 **v0.1** 배포 — `define` 단계 구현.

## 용어: 두 종류의 "버전"

| 용어 | 의미 | 예시 |
|---|---|---|
| **제품 버전** | team-ax 플러그인이 적용되는 외부 IT 제품의 버전 (semver) | rubato `v1.7.0`, rofan-world `v0.3.0` |
| **플러그인 버전** | team-ax 플러그인 자체의 버전 | team-ax `v0.1` (이번 스프린트), team-ax `v0.2` (다음 스프린트) |

> 본 plan에서 `versions/vX.Y.Z/` 폴더, `cycle/X.Y.Z` 브랜치, `scope.md` 등은 모두 **제품 버전**을 가리킨다. "v0.1 / v0.2"처럼 소수점 1자리 숫자가 붙은 것은 **플러그인 버전**(= 스프린트 산출물)이다.

## 제품 사이클 컨벤션 (목표 모델)

team-ax를 적용받는 **각 제품**은 **제품 버전 단위 사이클**로 돈다 — `define → (plan → build → qa) → deploy`가 하나의 제품 `vX.Y.Z`에 대해 돌아간다.

- **`versions/vX.Y.Z/`** — 해당 제품 버전의 모든 작업 산출물(초안·작업물·임시 문서 등) 보관. (제품 리포 내)
- **`docs/specs/`** — **확정된** 스펙 문서만 이 폴더로 승격(in-place 갱신). (제품 리포 내)
- **브랜치** — 제품 버전 사이클은 전용 브랜치에서 진행 (Phase B 부트스트랩, team-ax **플러그인 v0.2 예정**).

> 본 절은 **목표 모델**이다. team-ax 플러그인 v0.1은 이 중 Phase A(분석) + Phase C(수정 사이클)만 구현하고, Phase B(폴더 승격 / 사이클 브랜치 / worktree)는 **플러그인 v0.2에서 도입**한다. 상세는 §범위 / §비범위 참고.

### 제품 버전명은 범위의 산물

제품 버전명은 **정해놓고 시작하지 않는다.** define이 범위 분석을 마친 뒤에야 제품 버전명(major/minor/patch)이 결정된다.

- **플러그인 v0.1** — 제품 버전명은 결정·기록하지만 **폴더 승격·브랜치 생성 액션은 하지 않는다**. 산출물은 `versions/undefined/`에 머물고, 작업은 실행 시점의 현재 브랜치에서 진행.
- **플러그인 v0.2** — Phase B 부트스트랩 도입. 제품 버전명 확정 즉시 `versions/vX.Y.Z/` 폴더 + `cycle/X.Y.Z` 브랜치 + worktree 생성.

### 제품 문서 구조 — BACKLOG / scope / CHANGELOG 3-문서

> 이하 BACKLOG / scope.md / CHANGELOG는 모두 **제품 리포 안의 문서**를 가리킨다 (team-ax 플러그인 자체 문서 아님).

team-product 레퍼런스(rubato)에서 BACKLOG.md ↔ ROADMAP.md가 같은 내용을 이중 유지하고, ROADMAP.md ↔ CHANGELOG.md도 과거 버전 기록이 겹쳐 삼중 동기화가 발생하는 문제가 확인됨. **ROADMAP은 제거**하고 3문서 구조로 간소화한다.

| 파일 | 책임 | 시점 |
|---|---|---|
| `BACKLOG.md` | **인박스 전용** — 버전 미배정 아이디어 (필요 시 `[next]`·`[future]` 같은 우선순위 태그) | 모든 시점 |
| `versions/vX.Y.Z/scope.md` | **버전별 SSOT** — JTBD + 태스크 + 상태(planned/in-progress/done) + plan/write/review 사이클 기록 | 사이클 진행 중 |
| `CHANGELOG.md` | **배포 완료 기록** (Keep a Changelog 포맷) — 유저·외부 대상 | 배포 후(define에서는 다루지 않음) |

> **ROADMAP 제거 근거** — define/plan/build/qa/deploy 어느 단계에서도 직접 읽지 않는 문서였고, 역할이 BACKLOG(미래 계획)와 CHANGELOG(완료 기록)로 자연 분산됨. 전략 메타(유료화 경계 등)는 상위 전략 문서(`PROJECT_BRIEF.md` 또는 `strategy/`)로 이관하고 product lifecycle 문서에서 분리.

> **CHANGELOG는 define 단계 범위 밖.** 플러그인 v0.1에서는 작성·갱신 대상이 아니며, 제품 배포(deploy) 단계 구현 시 도입 예정으로 기록만 해둔다.

#### 항목 생애 흐름

```
BACKLOG.md (inbox)
   │  ← 아이디어 캡처만. 버전 미배정.
   │
   │ define 단계에서 "이번 버전 범위"로 승격
   ▼
versions/vX.Y.Z/scope.md
   │  ← 해당 버전의 JTBD + 태스크 + 상태. build 중 상태만 in-place 갱신.
   │
   │ 배포 완료 (후속 단계)
   ▼
CHANGELOG.md
      ← 해당 버전 블록 추가 (Added/Changed/Fixed 분류). scope.md는 아카이브로 남음.
```

- **동기화 지옥 제거** — 준비된 내용은 scope.md 한 곳에만 존재.
- **아카이브** — 완료 버전의 scope.md는 `versions/vX.Y.Z/`에 그대로 남아 조회 가능.
- **CHANGELOG는 유저 시점** — Keep a Changelog 포맷으로 릴리즈 노트·GitHub Release 재활용.

### 완료 처리 타이밍 (단계별 상태 전환 규칙)

각 문서의 상태 전환이 **어느 사이클 단계에서 일어나는지** 미리 정의. `define`만 이번 스프린트 범위지만 후속 단계 구현이 이 규칙을 따르도록 여기서 합의.

| 대상 | 전환 | 타이밍 (단계) | 주체 |
|---|---|---|---|
| `BACKLOG.md` inbox 항목 | **제거** (이번 버전 범위로 채택됨) | `define` Phase C write | `analyst` |
| `docs/specs/` `⏳ planned` 마커 | **추가** | `define` Phase C write | `analyst` |
| `scope.md` §수정 로그 | **체크(`- [x]`)** | `define` Phase C write | `analyst` |
| `scope.md` §리뷰 판정 | **`APPROVE`** | `define` Phase C review | `reviewer` |
| `scope.md` 태스크 상태 | `planned → in-progress` | `build` 진입 시 | (후속 단계 정의) |
| `scope.md` 태스크 상태 | `in-progress → done` | `build` 태스크 완료 시 | (후속 단계 정의) |
| `docs/specs/` `⏳ planned` 마커 | **제거** (변경이 현재의 진실이 됨) | `deploy` (배포 성공 후) | (후속 단계 정의) |
| `CHANGELOG.md` 해당 버전 블록 | **신규 추가** (Added/Changed/Fixed/Removed/Security 분류) | `deploy` (배포 성공 후) | (후속 단계 정의) |
| `scope.md` 최종 상태 | **아카이브 처리** (읽기 전용 마커) | `deploy` (배포 성공 후) | (후속 단계 정의) |

**원칙**
- 각 문서는 **해당 단계를 벗어나기 전**에 상태 전환이 끝나야 한다.
- "배포했는데 BACKLOG/scope/CHANGELOG가 stale" 상황은 각 단계의 완료 조건에 상태 전환을 포함시켜 원천 차단.
- 플러그인 v0.1(define 스킬)은 위 표의 `define` 줄만 구현. 나머지 줄은 **규칙으로 확정**만 하고 구현은 후속 스프린트.

## ax-define 스킬 명세

### 전체 입출력

| 구분 | 내용 |
|---|---|
| **입력** | `BACKLOG.md` inbox 항목 / 기존 `docs/specs/` 전체 / 오너 인터뷰 응답 |
| **출력 (플러그인 v0.1)** | `versions/undefined/scope.md` (+ intake / interview / JTBD / Story Map / SLC) / `docs/specs/` in-place 갱신(⏳ planned 마커) / `BACKLOG.md` inbox에서 채택 항목 제거 |

> 플러그인 v0.2 도입 후 출력에 **폴더 승격(`versions/vX.Y.Z/`)**, **`cycle/X.Y.Z` 브랜치**, **worktree**가 추가된다.

### 단계별 흐름 (입력 → 산출물)

**Phase A — 범위 분석** (버전명 확정 전, 산출물은 `versions/undefined/`에 임시 저장)

| # | 단계 | 입력 | 산출물 | 저장 위치 |
|---|---|---|---|---|
| 1 | 입력 수집 | `BACKLOG.md` inbox + 기존 `docs/specs/` | 수집·분석 노트 | `versions/undefined/intake.md` |
| 2 | 오너 인터뷰 | 수집 노트 (비자명한 질문만) | 인터뷰 로그 | `versions/undefined/interview.md` |
| 3 | JTBD 정의 | 인터뷰 + 수집 노트 | JTBD 문서 | `versions/undefined/jtbd.md` |
| 4 | Story Map | JTBD | Story Map | `versions/undefined/story-map.md` |
| 5 | SLC 체크 | Story Map + 범위 후보 | SLC 검증 결과 | `versions/undefined/slc.md` |
| 6 | 버전명 결정 + scope.md 초안 | SLC 통과 범위 + `references/semver.md` + 오너 확인 | 시맨틱 버전(major/minor/patch) + `scope.md` §버전 메타 + §범위 | `versions/undefined/scope.md` |

**Phase B — 부트스트랩** (제품 버전명 확정 직후) — **플러그인 v0.2 예정 (이번 스프린트 범위 아님)**

| # | 단계 | 입력 | 산출물 | 저장 위치 |
|---|---|---|---|---|
| 7 | 폴더 승격 | `versions/undefined/` | `versions/vX.Y.Z/` | rename (또는 신규 생성 후 이동) |
| 8 | 사이클 브랜치 + worktree 생성 | 제품 버전명 | `cycle/X.Y.Z` 브랜치 + `../{repo}-X.Y.Z` worktree | git |

> 플러그인 v0.1에서는 Phase B를 **건너뛴다**. Phase A 산출물은 `versions/undefined/`에 그대로 두고, Phase C도 같은 위치의 `scope.md`에 작성한다. 현재 브랜치에서 작업.

**Phase C — plan → write → review 사이클** (문서 수정 사이클)

| # | 단계 | 입력 | 산출물 | 저장 위치 |
|---|---|---|---|---|
| 9 | **plan** — 수정 계획 | 확정 범위 + 기존 `docs/specs/` 매핑 + BACKLOG 변경점 | 파일별 변경 타입(갱신/신규/삭제/마커) + 요약 | `versions/undefined/scope.md` §수정 계획 |
| 10 | **write** — 수정 실행 | §수정 계획 | (a) `docs/specs/` in-place 갱신 (`⏳ planned` 마커) (b) `BACKLOG.md` inbox 채택 항목 제거 | 실제 파일 수정 + `scope.md` §수정 로그에 체크/커밋 ref 기록 |
| 11 | **review** — 수정 검증 | §수정 계획 vs 실제 diff | 항목별 체크 + 판정(APPROVE / REQUEST_CHANGES) + 재작업 노트 | `versions/undefined/scope.md` §리뷰 |

> `REQUEST_CHANGES` 판정 시 9번(plan)으로 되돌아가 재작업. `APPROVE`여야 define 완료 처리.

> Phase A(1~6단계) 산출물은 `versions/undefined/`에 즉시 저장해 세션 유실을 방지한다. **플러그인 v0.1은 Phase C 산출물도 `versions/undefined/`에 머문다**. 플러그인 v0.2에서 Phase B가 도입되면 제품 버전명에 따라 `versions/vX.Y.Z/`로 승격된다.

> **major/minor 분기 없음.** 스코프 크기에 따라 산출물 분량이 달라질 수는 있어도 단계 생략은 없다. minor여도 JTBD/Story Map/SLC는 반드시 작성된다 (짧게라도).

### 에이전트 + 리뷰 스킬 구성

Claude 서브에이전트 2개(작성 담당) + 범용 `ax-review` 스킬 1개(검증 담당, codex 위임).

| 구성요소 | 담당 Phase | 책임 | 툴 / 엔진 |
|---|---|---|---|
| **`product-owner`** (Claude 서브에이전트) | Phase A 전체 | BACKLOG inbox 분석 / 오너 인터뷰(비자명한 질문만) / JTBD / Story Map / SLC / 제품 버전명 결정 | `Read` / `Grep` / `Glob` / `AskUserQuestion` / `Write` / `Edit` |
| **`analyst`** (Claude 서브에이전트) | Phase C plan + write | 기존 specs/ 매핑 탐색 / §수정 계획 작성 / specs in-place 갱신 / BACKLOG inbox 정리 / §수정 로그 기록 | `Read` / `Grep` / `Glob` / `Write` / `Edit` |
| **`ax-review` 스킬** (codex 위임) | Phase C review | §수정 계획 vs 실제 diff 대조 / 강제 장치 4종 위반 탐지 / APPROVE·REQUEST_CHANGES 판정 | `codex exec -s read-only` 호출 |

**`ax-review` 스킬 (별도 스킬로 분리)**

team-ax의 모든 리뷰(문서·구현·PR)를 **codex에 위임**하는 범용 스킬. ax-define의 Phase C 외에도 향후 ax-build의 code review, ax-deploy의 PR review에서 재사용.

```
plugin/skills/ax-review/
├── SKILL.md                 # conductor — 타입 파싱 + codex 호출
└── references/
    ├── doc-checklist.md     # 문서 리뷰 기준 (v0.1 구현)
    ├── code-checklist.md    # 구현 리뷰 기준 (후속 스프린트)
    └── pr-checklist.md      # PR 리뷰 기준 (후속 스프린트)
```

**호출 형태 (타입 기반 서브커맨드)**

Codex에 위임하므로 Claude는 Bash 툴로 `codex exec`를 실행:

```bash
codex exec '$ax-review doc <대상>'    # 문서 리뷰 (v0.1 구현)
codex exec '$ax-review code <대상>'   # 구현 리뷰 (v0.1은 stub)
codex exec '$ax-review pr <번호>'     # PR 리뷰 (v0.1은 stub)
```

`codex exec` 기본 sandbox = `read-only`이므로 doc/code 리뷰는 플래그 불필요. PR 리뷰는 `gh pr diff` 호출을 위해 `--full-auto` 또는 `-s workspace-read` 필요 (후속 스프린트에서 확정).

ax-define의 Phase C review는 `codex exec '$ax-review doc versions/undefined/scope.md'` 호출로 수행.

**Codex 스킬 설치**

Codex 쪽에서 `$ax-review`를 인식하려면 플러그인 스킬을 `~/.codex/skills/ax-review/`로 복사해야 한다. KESE-KIT의 `install-local-skills.sh` 패턴 차용:

```
plugin/scripts/install-local-skills.sh
  → rsync plugin/skills/ax-review/ → ~/.codex/skills/ax-review/
  → rsync plugin/skills/ax-review/ → ~/.claude/plugins/cache/lazyyoyo/team-ax/_latest_/skills/ax-review/ (선택, Claude 플러그인 캐시 갱신)
```

참조: `/Users/sunha/hq/projects/KESE-KIT/scripts/install-local-skills.sh` + `/Users/sunha/hq/projects/KESE-KIT/AGENTS.md`.

**타입별 codex sandbox**

| 타입 | sandbox |
|---|---|
| `doc` | `read-only` |
| `code` | `read-only` (테스트 실행 필요 시 후속 스프린트에서 `workspace-read`) |
| `pr` | `workspace-read` (`gh pr diff` 등 CLI 필요) |

**SKILL.md (ax-define conductor) 담당**
- Phase 순서 제어 (A → C, 플러그인 v0.1은 Phase B 건너뜀)
- Phase C review에서 `ax-review` 스킬 호출 (`$ax-review doc ...`)
- review → REQUEST_CHANGES 루프 재진입 관리
- (플러그인 v0.2에서) Phase B 부트스트랩(폴더 승격 / 브랜치 / worktree) 결정적 작업 추가 예정

**분리 근거**
- **PO** = "무엇을 / 왜" (분석·인터뷰·JTBD). team-product에서 증명된 역할.
- **Analyst** = "어느 파일을 / 어떻게 수정" (specs 매핑·실행). 실행 디테일 담당.
- **Review 스킬 (codex)** = "제대로 됐는가" (독립 검증). 작성 엔진(Claude) ≠ 검증 엔진(codex)으로 **엔진 수준 분리**. 향후 모든 리뷰가 이 스킬로 통일 → 단일 소스 유지.

### scope.md — define의 plan→write→review 사이클 캐리어

`versions/vX.Y.Z/scope.md`는 단순 스코프 기록이 아니라 **define 단계의 살아있는 문서**다. 구현 단계의 `plan → build → review`와 동형의 사이클을 문서 수정에 적용한다.

```
plan  — 어떤 파일을 수정할 것인가 (§수정 계획)
write — 실제로 수정했는가 (§수정 로그)
review — 수정이 의도대로 됐는가 (§리뷰)
```

**scope.md 섹션 구조 (초안)**

| 섹션 | 내용 |
|---|---|
| § 버전 메타 | 제품 버전명 / 시맨틱 구분(major·minor·patch) — (플러그인 v0.2부터) `cycle/X.Y.Z` 브랜치명 / worktree 경로 |
| § JTBD | 한 문장 JTBD — "And 없는 한 문장" 통과 필수. **한 버전 = 하나의 JTBD**. |
| § Story Map | Story별 그룹핑된 태스크 (spec 링크 포함). Story 2~N개. 패치 모음 버전은 Story 없이 태스크 목록만 가능. |
| § SLC 체크 | Simple / Lovable / Complete 각각의 근거 한 줄씩 |
| § 비범위 | 이번 버전에서 의도적으로 제외한 항목 + 이유 |
| § 수정 계획 | 파일별 변경 타입(갱신/신규/삭제/마커 추가) + 변경 요약 + 대응 태스크 |
| § 수정 로그 | 각 계획 항목의 실행 여부 체크(`- [x]`) + 실제 commit/ref |
| § 리뷰 | 항목별 검증 체크리스트 + 최종 판정(APPROVE / REQUEST_CHANGES) + 재작업 노트 |

**한 제품 버전 = 하나의 JTBD 원칙**

- "And 없는 한 문장" 테스트를 **JTBD에 먼저 적용**. 두 관심사가 묶이면 제품 버전을 쪼갠다 (rubato의 제품 v1.4.1 "UX 패치 + 원서 검색" 같은 섞임을 차단).
- 통과한 JTBD 하나 아래에 **여러 Story**, 각 Story 아래 **여러 태스크** 구조.
- 패치 모음 제품 버전(예: rubato 제품 v1.5.1)도 JTBD 한 문장으로 묶일 수 있음 (예: "앱을 안정적으로 사용하고 데이터가 정확하게 표시된다"). 이 경우 Story 축소하고 태스크 목록만.

**§ JTBD / § Story Map / § SLC 예시 (rubato 제품 v1.7.0 재구성)**

```markdown
## JTBD
내 프로필과 설정을 한 곳에서 관리한다.

## Story Map
### Story 1: 프로필 보기
- 프로필 카드 컴포넌트 (spec: profile.md)
- profiles 테이블 + 트리거
- GET /api/profile

### Story 2: 테마 변경
- 테마 모달 + DB 저장 (spec: theme.md)
- PATCH /api/profile/theme

### Story 3: 비밀번호 변경
- 비밀번호 모달 + 인라인 검증 + 성공 화면 (spec: auth.md)

## SLC 체크
- Simple: 3 Story로 끝. 계정 삭제·FAQ는 out of scope.
- Lovable: 각 Story가 모달/페이지 단위로 쾌적하게 동작.
- Complete: 3 Story가 합쳐져 "마이페이지" 경험 독립 완결.
```

**왜 define에도 이 사이클이 필요한가**

- team-product define에는 "무엇을 수정할 것인가(plan)" → "수정 완료 확인(review)"이 없어 spec 파일 증식·누락이 반복됐다.
- 문서 수정도 코드 수정과 동일하게 **대상 지정 → 실행 → 검증**이 돌지 않으면 신뢰할 수 없다.
- scope.md 한 파일에 세 섹션을 누적하면 작업자/리뷰어가 diff만 봐도 "뭘 한다고 했고, 뭘 했고, 통과했는가"를 재구성할 수 있다.

## 범위 (플러그인 v0.1)

- team-product의 `product-define` 스킬을 기반으로 team-ax **플러그인 v0.1**의 `ax-define` 스킬 작성.
- **개선 1** — JTBD / Story Map / SLC 산출물을 스킬 흐름에 **명시적 단계**로 포함. 스킵되지 않도록 강제. 산출물은 `versions/vX.Y.Z/` 하위에 저장.
- **개선 2** — spec은 **in-place 갱신**. team-dev `backlog refine`의 `⏳ planned` 마커 방식 차용. 확정 스펙은 `docs/specs/`에 위치. 새 파일 남발을 막기 위한 **강제 장치 4종**:
  1. **기존 파일 매핑 탐색 의무화** — 새 요구사항을 받으면 기존 specs/ 전체를 먼저 읽고 "어느 파일에 속하는가"를 제안. 매칭 후보가 없을 때만 신규 생성 허용.
  2. **파일명 규칙** — `{기능명}.md`만 허용. `-fix` / `-patch` / `-enhance` / `-redesign` / `-v2` 같은 **시점·변경 단위 접미사 금지**.
  3. **시간 축 본문 금지** — 변경 이력은 `⏳ planned` 마커 + git log로 처리. spec 본문에 "v1.5에서 추가" 같은 누적 기록 금지.
  4. **spec vs changelog 판정 가드** — 버그 수정 / 핫픽스 / 패치는 **기존 spec 갱신** 대상이지 신규 파일 생성 대상이 아니다.
- **개선 3 — 단일 흐름(major/minor 분기 없음)** — team-product는 major/minor 동작 순서를 나눠 놓았고, 실제 작업은 minor 위주였기 때문에 JTBD/Story Map/SLC가 사실상 매번 스킵됐다. team-ax는 **하나의 흐름으로 통일**한다. 스코프 크기는 각 단계의 **깊이/결과물 분량**에만 영향을 주고, **단계 자체는 항상 수행**한다.
- **분석 산출물 영속화** — 분석 시작 시 `versions/undefined/`를 먼저 만들어 Phase A/C 산출물을 즉시 저장. 세션 유실 시 재진입 가능.
- **제품 버전명 규칙** — [Semantic Versioning 2.0](https://semver.org/) 기준. major / minor / patch 판정을 6번 단계에서 **결정·기록**까지만 수행. 폴더 승격·브랜치 생성은 플러그인 v0.2 Phase B 소관.
- 산출 위치:
  - `plugin/skills/ax-define/SKILL.md`
  - `plugin/skills/ax-define/references/` — 스킬이 참조하는 프레임워크 문서
    - `jtbd.md` — Jobs To Be Done 프레임워크
    - `story-map.md` — Story Map 그리드 작성법
    - `slc.md` — Simple / Lovable / Complete 체크 기준
    - `semver.md` — Semantic Versioning 판정 규칙
    - `spec-lifecycle.md` — in-place 갱신 + `⏳ planned` 마커 + 파일명 규칙
    - `docs-structure.md` — BACKLOG / scope / CHANGELOG 3-문서 역할 분리 (ROADMAP 제거 배경 포함)
  - `plugin/skills/ax-define/templates/` — scope.md 템플릿 등
  - `plugin/skills/ax-review/SKILL.md` — 범용 리뷰 스킬 (codex 위임)
  - `plugin/skills/ax-review/references/doc-checklist.md` — 문서 리뷰 기준 (v0.1 구현)
  - `plugin/agents/product-owner.md` + `analyst.md` — Claude 서브에이전트 2개

## 비범위 (플러그인 v0.1)

- 제품 사이클의 design / implement / qa / ship / deploy 단계 구현.
- ax-loop(자동 루프 / 게이트 / 멀티모델 / Judge 등) 관련 일체.
- 외부 프로젝트(rubato 등) 실호출 검증.
- **Phase B 부트스트랩** — `versions/undefined/` → `versions/vX.Y.Z/` 승격, `cycle/X.Y.Z` 브랜치 / worktree 생성 → 플러그인 v0.2.
- **분리 감지 및 복수 제품 버전 처리** — 여러 JTBD 발견 시 제품 버전 분리, 복수 scope.md 생성 → 플러그인 v0.2.
- **의존성 분석** — 제품 버전 간 선행·파일 중복·상호 배타 판정 + scope.md `§ 의존성` → 플러그인 v0.2.
- **병렬 실행 오케스트레이션** — worktree 기반 병렬 build / 의존성 기반 merge 순서 → 플러그인 v0.3+.

## 성공 기준

- `/ax define` 실행 시 Phase A 산출물(intake / interview / JTBD / Story Map / SLC)이 `versions/undefined/`에 **결정적으로 생성**된다 (생략 불가, 중간 중단에도 재진입 가능).
- `versions/undefined/scope.md`가 해당 버전의 **단일 SSOT**로 생성된다. BACKLOG.md inbox에서 채택 항목이 제거되고, 다른 문서로의 상세 복제는 없음 (ROADMAP은 구조에서 제거됨. CHANGELOG는 deploy 단계에서 생성).
- scope.md에 **§수정 계획 → §수정 로그 → §리뷰** 3섹션이 모두 채워지고 최종 판정이 `APPROVE`여야 define이 완료 처리된다. `REQUEST_CHANGES`면 §수정 계획으로 되돌아가 재작업.
- 기존 spec이 존재하면 **in-place로 갱신**되고 변경 예정 부분은 `⏳ planned` 마커로 병기된다. 새 파일 남발 없음.
- 제품 버전명(semver)은 Phase A에서 **결정·기록**되지만 폴더 승격·브랜치 생성 액션은 발생하지 않는다 (플러그인 v0.2 소관).
- team-ax 플러그인 `v0.1.0` 태그 생성 + 배포 완료.

## 참조

- team-product `product-define`: `/Users/sunha/hq/projects/my-agent-office/plugins/team-product/skills/product-define/`
- team-dev `backlog refine`: `/Users/sunha/hq/projects/my-agent-office/plugins/team-dev/skills/backlog/SKILL.md` — in-place 갱신 + `⏳ planned` 마커 원형
- team-dev `sprint plan`: `/Users/sunha/hq/projects/my-agent-office/plugins/team-dev/skills/sprint/SKILL.md` — 살아있는 plan 문서 패턴

## 태스크

(추가 전달사항 반영 후 확정)

## 상태

- [ ] 범위 확정
- [ ] 태스크 분해
- [ ] 구현
- [ ] 플러그인 v0.1.0 태그 + 배포
