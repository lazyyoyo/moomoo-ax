---
name: ax-design
description: "team-ax 디자인 스킬. 컴포넌트 단위 오너 확정 → 조합으로 디자인 품질 보장. DS 위에서만 작업. Use when: /ax-design, 디자인, 시안, 컴포넌트 디자인, UX 플로우."
argument-hint: "<대상 제품 리포 경로>"
---

# /ax-design

team-ax의 디자인 스킬. **"시안 만들고 피드백 받기"가 아니라 "컴포넌트 단위 확정 → 조합"**으로 오너 개입을 앞당겨 품질을 보장한다.

> **실행 위치**: `version/vX.Y.Z` 브랜치. v0.8부터 worktree 폐기 — 독립 실행이든 ax-build 호출이든 **단일 브랜치에서 동작**.

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | `versions/vX.Y.Z/scope.md` (§Story Map), 기존 `DESIGN_SYSTEM.md`, `brand/`, `reference/library/` |
| **출력** | UX 플로우(`flows/`), 확정 컴포넌트(DS 등록), 시안 페이지(`(mockup)/`), 게이트 결과(`design-review.md`) |

## 에이전트 구성

| 에이전트 | 담당 | 책임 |
|---|---|---|
| `ux-designer` | 3단계 | specs/ 기반 화면 플로우 + 상태 변형 + 컴포넌트 목록 산출 |
| `design-builder` | 5·6단계 | DS 위에서 컴포넌트 개발 + 전체 구성. 확정된 컴포넌트만 사용. |

## 동작 순서

### 사전 점검

1. **실행 위치 판단** (v0.8):
   - `version/vX.Y.Z` 브랜치에 있으면 → 독립 실행 모드 또는 ax-build 2단계(공통 기반) 호출 모드
   - main에서 실행 중이면 → 중단
2. scope.md 존재 확인 (`versions/vX.Y.Z/scope.md`).
3. ax-build에서 호출된 경우 DS 갱신은 **공통 기반 단계에서만** 수행됨 (워커가 개별적으로 DS 수정 금지 — ax-execute whitelist 가드).

### 1단계 — DS 토큰 확인

프로젝트에 기본 토큰이 있는지 확인. 없으면 브랜드에서 추출하여 확립.

**체크 항목:**

| 카테고리 | 필수 항목 |
|---|---|
| 색상 토큰 | 배경 스케일, 전경, 브랜드, 시맨틱(success/warning/error/info) |
| 공간 토큰 | spacing 스케일 (4px 기반) |
| 타이포 토큰 | 폰트 패밀리, 사이즈 스케일, 웨이트, 행간 |
| 기본 컴포넌트 | Button, Input, Badge, Toast (범용) |

- 이미 있으면 스킵.
- `brand/` 가이드라인이 있으면 거기서 추출.
- **브랜드 톤 유지가 기본.** 리뉴얼은 오너가 명시적으로 요청할 때만.

검증: `bash plugin/scripts/ds-completeness-check.sh`

### 2단계 — 오너 인터뷰

구체적이고 실행 가능한 결정만 묻는다. **주관적 질문("느낌/무드", "피하고 싶은 스타일") 금지.**

**인터뷰 항목:**

1. **레퍼런스 확인:**
   - 기존 `reference/library/`를 보여주고 → "이 중에 참고할 것이 있는가?"
   - "새로 참고할 사이트/이미지가 있는가?"
   - 있다면 → "어느 부분을 참고할지?" (footer, card, 색감 등 부분 태깅)
   - **없으면 레퍼런스 없이 진행** (기존 DS 조합으로 충분할 수 있음)

2. **접근 방식 확인:**
   - "이번 기능은 기존 컴포넌트로 조합 가능할 것 같은데, 새 디자인이 필요한가?"
   - "새 컴포넌트가 나오면 하나씩 확정하면서 갈지, 전체 시안을 먼저 볼지?"
   - 기능 우선순위 (Story 중 디자인 비중이 높은 것)

레퍼런스 있을 때만 `reference/vX.Y.Z-{기능}/` 하위에 `references/reference-readme-template.md` 포맷으로 README.md 작성.

**산출물**: `versions/vX.Y.Z/design-brief.md` → 커밋.

### 3단계 — UX 플로우 설계 (`ux-designer` 호출)

`ux-designer` 에이전트에게 Story별 UX 플로우를 설계시킨다.

- 입력: `versions/vX.Y.Z/scope.md` §Story Map + `docs/specs/`
- **모든 화면에 상태 변형 필수** (loading/error/empty/권한없음)
- 엣지 케이스 포함
- **컴포넌트 필요 목록 산출** — 각 Story에서 필요한 컴포넌트 식별
- 출력: `flows/{기능명}.md` (Story별)

→ **커밋** (`docs(flows): {기능명} 플로우 설계`)

### 4단계 — Story별 디자인 분기

3단계에서 산출된 **Story별 컴포넌트 필요 목록 vs 기존 DS**를 비교하여 각 Story의 디자인 필요성을 개별 판단.

| 판정 | 조건 | 다음 단계 | 병렬성 |
|---|---|---|---|
| **디자인 불필요** | UI 변경 없음 (백엔드, API 등) | ax-build 병렬 라운드에 즉시 투입 | 즉시 병렬 가능 |
| **조합으로 충분** | 기존 DS 컴포넌트로 구성 가능 | 기존 DS로 조합 → 8단계 오너 프리뷰 | 프리뷰 후 병렬 가능 |
| **신규 디자인 필요** | 신규 컴포넌트/레이아웃 필요 | 5~8단계 진행 (version branch, 공통 기반) | 디자인 확정까지 대기 |

**억지 새 디자인 금지**: 기존 컴포넌트로 조합 가능하면 그게 정답.

판정 결과를 scope.md §Story Map에 기록:
```markdown
### Story 1: 프로필 페이지
- 디자인: 신규 (ProfileCard 컴포넌트 필요)

### Story 2: API 리팩터링
- 디자인: 불필요

### Story 3: 설정 페이지
- 디자인: DS 조합 (기존 Form + Toggle로 구성 가능)
```

**디자인 불필요 Story는 ax-build 병렬 라운드에 즉시 투입 가능** (v0.8: 파일 whitelist 기반).

→ **커밋** (`docs(scope): Story별 디자인 분기 판정`)

### 5단계 — 컴포넌트 개발 + 오너 확정 + DS 등록 (`design-builder` 호출)

**"신규 디자인 필요" 판정된 Story만 대상.** DS는 디자인에서 나온다.

```
신규 컴포넌트 식별
  → design-builder가 컴포넌트 단독 구현 (DS 프리뷰 페이지에 추가)
  → 메인 세션이 AskUserQuestion으로 오너 확정 ("이 카드 컴포넌트 이대로 갈까요?")
  → 확정 → DESIGN_SYSTEM.md + DS 프리뷰 페이지에 등록 → 커밋
  → 리젝 → 피드백 반영 수정 → 재제출 (컴포넌트당 최대 2회)
  → 다음 컴포넌트로
  → 모든 신규 컴포넌트 확정 후 6단계로
```

**오너가 보는 것:**
- DS 프리뷰 페이지에서 해당 컴포넌트의 실물 렌더링
- variant 전체 (size, color, state)
- 레퍼런스 매핑이 있으면 참고 포인트 대비

→ 컴포넌트 확정마다 **커밋** (`feat(ds): {컴포넌트명} 확정 + DS 등록`)

### 6단계 — 전체 구성 (`design-builder` 호출)

확정된 컴포넌트(기존 + 신규)로 전체 화면을 조합.

- UX 플로우(3단계)에 따라 화면 구성
- **확정된 컴포넌트만 사용** — 이 단계에서 새 컴포넌트 만들지 않음
- 공통 규칙 (header/max-width/spacing 등 레이아웃 토큰) 준수
- 격리 세션 빌드 (시안 다양성이 필요하면 복수 세션)
- 출력: `src/app/(mockup)/vX.Y-{기능}-{variant}/`

→ **커밋** (`feat(mockup): vX.Y {기능명} 구성`)

### 7단계 — 게이트

오너 프리뷰 전 자동 필터링. 비용 순서대로 계층화.

| # | 게이트 | 유형 | 검증 내용 |
|---|---|---|---|
| ① | DS 준수 린트 | 코드 | 하드코딩된 색상/간격/폰트 탐지, 토큰만 사용 확인 |
| ② | 레이아웃 규칙 | 코드 | max-width, header, container padding 준수 |
| ③ | Playwright 스크린샷 | 코드 | desktop/mobile 캡처, 빈 화면/깨진 레이아웃 탐지 |
| ④ | Judge 체크리스트 | AI | 동적 체크리스트 (CheckEval — UX 기반 Yes/No 항목 자동 생성) |

**①② 통과 못 하면 ③④ 실행 안 함** (비용 절약).

검증: `bash plugin/scripts/design-gate.sh`

**게이트 실패 시:**
- No 항목 → 수정 지시서 자동 변환 → design-builder에 재지시 → 재빌드
- keep/discard: 점수 개선 시에만 유지, 아니면 이전 best로 롤백
- 오너 개입 없이 자동 재작업. 게이트 루프 최대 3회.

→ **커밋** (`docs(design): vX.Y 게이트 결과 기록`)

### 8단계 — 오너 프리뷰

게이트 전체 통과한 결과물을 오너에게 전달. **조합이든 새 시안이든 새 화면이면 항상 실행.**

프리뷰 방법: localhost 또는 Vercel preview.

피드백 분류:
- 승인 → 완료
- 컴포넌트 수정 → 5단계 (해당 컴포넌트만 재확정)
- 레이아웃 변경 → 6단계 재구성
- 플로우 변경 → 3단계 UX 재설계

**8단계 최대 3회 루프.** 수렴 안 되면 전체 시도 이력 정리 + 오너 최종 결정 강제.

→ **커밋** (`style(design): vX.Y {기능명} 확정`)

### 완료 처리

- 오너 프리뷰 승인 확인
- 오너에게 완료 보고
- **독립 실행 시**: 다음 단계 `/ax-build` 안내
- **ax-build 호출 시**: ax-build로 제어 반환 (구현 단계로 이어짐)

## 오너 리젝 시 재작업 프로토콜

### 5단계 리젝 (컴포넌트 단위)

| 피드백 유형 | 대응 |
|---|---|
| 구체적 피드백 ("이미지 비율이...", "여백이...") | 피드백 기반 수정 → 같은 컴포넌트 재제출 |
| 레퍼런스 지목 ("이 사이트 카드처럼") | 레퍼런스 부분 태깅 추가 → 재빌드 |
| 방향 자체가 다름 ("카드가 아니라 리스트로") | UX 플로우(3단계) 해당 화면 재설계 → 컴포넌트 재식별 |

컴포넌트당 최대 2회. 초과 시 시도 이력(스크린샷 포함) 정리 → "A안 vs B안" 선택 요청.

### 8단계 리젝 (전체 구성)

| 피드백 유형 | 대응 |
|---|---|
| 배치가 문제 | 6단계(전체 구성)만 재실행 |
| 특정 컴포넌트가 문제 | 5단계에서 해당 컴포넌트만 재확정 → 6단계 재구성 |
| 플로우 자체가 문제 | 3단계(UX) 재설계 → 4단계부터 재진행 |
| 전부 다 문제 | 2단계(오너 인터뷰)부터 재진행 |

### 컨텍스트 보존

- 확정된 컴포넌트는 DS에 즉시 등록 → 리젝된 다른 컴포넌트와 무관하게 유지
- 매 단계 완료 시 커밋 → 어느 시점으로든 돌아갈 수 있음
- 전체 구성 리젝 시 확정된 컴포넌트 자체는 건드리지 않음

## 가드레일

1. **실행 위치** — version branch에서 실행 (독립이든 ax-build 호출이든 동일). main에서 직접 실행 금지. **v0.8부터 worktree 폐기** — DS 수정은 항상 version branch에서 직접 수행하며, 개별 워커(ax-execute)는 whitelist 가드로 DS 파일 편집이 차단된다.
2. **브랜드 톤 유지** — 오너가 명시적으로 리뉴얼 요청하지 않는 한 기존 brand/ 톤 유지.
3. **주관적 인터뷰 금지** — "느낌/무드", "피하고 싶은 스타일" 같은 질문 금지. 구체적 결정만.
4. **억지 새 디자인 금지** — 기존 DS 컴포넌트로 조합 가능하면 새 시안 만들지 않음.
5. **확정 컴포넌트만 사용** — 6단계(전체 구성)에서 미확정 컴포넌트 생성 금지.
6. **DS 토큰만 사용** — 하드코딩된 색상/간격/폰트 금지. 게이트 ①에서 차단.
7. **오너 프리뷰 항상 실행** — 조합이든 새 시안이든 새 화면이면 반드시 오너 확인.
8. **slop 방지** — `references/design-principles.md` 안티패턴 준수.
9. **상태 변형 필수** — 모든 화면에 loading/error/empty 상태.
10. **review는 codex 위임만** — 작성 엔진 ≠ 검증 엔진 분리 (ax-review와 동일 원칙).

## 참조

- `references/design-principles.md` — slop 방지 + 안티패턴
- `references/font-catalog.md` / `korean-fonts.md` / `font-pairing-kr.md` — 폰트
- `references/trends-2026.md` — 디자인 트렌드
- `references/domain-checklists.md` — 도메인별 UI/UX 체크리스트
- `references/layout-patterns.md` — 레이아웃 패턴
- `references/animation-recipes.md` — 모션 코드 레시피
- `references/reference-readme-template.md` — 레퍼런스 README 포맷 (부분 태깅 + Story 매핑)
- `plugin/agents/ux-designer.md` — UX 플로우 설계 에이전트
- `plugin/agents/design-builder.md` — 컴포넌트 개발 + 전체 구성 에이전트
- `plugin/scripts/ds-completeness-check.sh` — DS 토큰 확인 게이트
- `plugin/scripts/design-gate.sh` — DS 준수 린트 + 레이아웃 규칙 체크
