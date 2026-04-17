# sprint-3 plan

**목표**: team-ax 플러그인 **v0.3** 배포 — `ax-design` 스킬 신규 구현.

> 핵심 전환: "시안 만들고 피드백 받기"가 아니라 **"컴포넌트 단위 확정 → 조합"**으로 개입 지점을 앞당긴다. DS는 디자인에서 나온다 — 미리 완성하는 게 아니라 새 컴포넌트가 발견될 때 오너 확정 후 등록.

## 해결할 문제 (5가지)

| # | 문제 | 원인 | 해결 방향 |
|---|---|---|---|
| 1 | 디자인 품질 낮음 | 전체 시안 리뷰에서야 문제 발견 | 컴포넌트 단위 오너 확정 → 조합 (문제를 앞에서 잡음) |
| 2 | 브랜드/톤 무시 | 브랜드 토큰이 강제 안 됨 | hooks로 DS 자동 주입 + 정적 린트 |
| 3 | 레퍼런스 부분 매핑 안 됨 | 사이트 단위 참조만 | 오너 인터뷰에서 부분 태깅 + Story 매핑 |
| 4 | DS 있어도 안 지켜짐 | CSS→토큰→컴포넌트 연결 단절 | DS 준수 게이트 + CheckEval 동적 체크리스트 |
| 5 | DS 생성 자체가 부실 | 한 번에 완성하려 함 | 디자인에서 나온 컴포넌트를 점진적으로 DS에 등록 |

## 전제

- sprint-2 (v0.2) 완료 — Phase B worktree 인프라 가동 중
- 기존 team-design/team-product의 slop 방지, 안티패턴, 상태 변형 등은 가져감
- jojo의 sasasa DS 프리뷰 페이지가 "최소 기대 수준"의 기준점
- 브랜드 톤 유지가 기본 (리뉴얼은 오너가 명시적으로 요청할 때만)

## ax-design 플로우

```
실행 위치: version/vX.Y.Z 브랜치 (Phase B 산출물)

1. DS 토큰 확인 ──── 브랜드 기반 토큰 있는지 확인. 없으면 확립.
       │
2. 오너 인터뷰 ───── 레퍼런스 결정 + 접근 방식 확인
       │
3. UX 플로우 설계 ── Story별 화면/상태 확정 + 컴포넌트 필요 목록 산출
       │
4. Story별 디자인 분기 ── 각 Story의 디자인 필요성을 개별 판단
       │
       ├── Story A (디자인 불필요) → 바로 story-A worktree에서 ax-build 가능
       ├── Story B (DS 조합 충분)  → 조합 → 오너 프리뷰 → story-B worktree에서 ax-build
       └── Story C (새 디자인 필요) → 5~8단계 진행 (이 동안 Story A는 병렬 빌드 중)
                │
5. 컴포넌트 개발 ─── 새 컴포넌트 식별 → 개별 오너 확정 → DS 등록
       │
6. 전체 구성 ─────── 확정된 컴포넌트로 화면 조합
       │
7. 게이트 ──────── 자동 필터링 (린트→스크린샷→Judge)
       │
8. 오너 프리뷰 ───── 항상 실행 (조합이든 새 시안이든)
```

**병렬성**: 디자인 불필요 Story는 ax-design 완료를 기다리지 않고 worktree에서 바로 ax-build 진입 가능. 디자인 필요 Story만 version branch에서 5~8단계를 거친 뒤 worktree로 이동.

### 1. DS 토큰 확인

프로젝트에 기본 토큰이 있는지 확인. **없으면 브랜드에서 추출하여 확립.**

| 카테고리 | 필수 항목 |
|---|---|
| 색상 토큰 | 배경 스케일, 전경, 브랜드, 시맨틱(success/warning/error/info) |
| 공간 토큰 | spacing 스케일 (4px 기반) |
| 타이포 토큰 | 폰트 패밀리, 사이즈 스케일, 웨이트, 행간 |
| 기본 컴포넌트 | Button, Input, Badge, Toast (범용) |

이미 있으면 스킵. brand/ 가이드라인이 있으면 거기서 추출. **브랜드 톤 유지가 기본.**

### 2. 오너 인터뷰

구체적이고 실행 가능한 결정만 묻는다. 주관적 질문("느낌/무드", "피하고 싶은 스타일") 금지.

**인터뷰 항목:**

1. **레퍼런스 확인:**
   - 기존 library/에 저장된 레퍼런스를 보여주고 → "이 중에 참고할 것이 있는가?"
   - "새로 참고할 사이트/이미지가 있는가?"
   - 있다면 → "어느 부분을 참고할지?" (footer, card, 색감 등 부분 태깅)
   - **없으면 레퍼런스 없이 진행**

2. **접근 방식 확인:**
   - "이번 기능은 기존 컴포넌트로 조합 가능할 것 같은데, 새 디자인이 필요한가?"
   - "새 컴포넌트가 나오면 하나씩 확정하면서 갈지, 전체 시안을 먼저 볼지?"
   - 기능 우선순위 (Story 중 디자인 비중이 높은 것)

**레퍼런스 있을 때만 README.md 작성:**
```markdown
## 참고할 포인트
- footer: 3컬럼 구성 + 뉴스레터 폼 배치
- card: 이미지 비율 + hover 시 elevation 변화

## Story 매핑
- Story 1 (프로필): card
- Story 2 (메인): footer
```

### 3. UX 플로우 설계

team-product의 ux-designer 에이전트를 이식.

- specs/ 기반 화면 플로우 설계
- **모든 화면에 상태 변형 필수** (loading/error/empty/권한없음)
- flows/ 마크다운 출력
- 엣지 케이스 포함
- UX에서 필요한 컴포넌트 목록 산출 (→ 4단계 판단 입력)

### 4. Story별 디자인 분기

3단계에서 산출된 **Story별** 컴포넌트 목록 vs 기존 DS를 비교하여 **각 Story의 디자인 필요성을 개별 판단**.

| 판정 | 조건 | 다음 단계 | 병렬성 |
|---|---|---|---|
| **디자인 불필요** | UI 변경 없음 (백엔드, API 등) | story worktree에서 바로 ax-build | 즉시 병렬 가능 |
| **조합으로 충분** | 기존 DS 컴포넌트로 구성 가능 | 조합 → 오너 프리뷰 → ax-build | 프리뷰 후 병렬 가능 |
| **신규 디자인 필요** | 신규 컴포넌트/레이아웃 필요 | 5~8단계 진행 (version branch) | 디자인 확정까지 대기 |

**억지 새 디자인 금지**: 기존 컴포넌트로 조합 가능하면 그게 정답.

**판정 결과를 scope.md §Story Map에 기록:**
```markdown
### Story 1: 프로필 페이지
- 디자인: 신규 (ProfileCard 컴포넌트 필요)

### Story 2: API 리팩터링
- 디자인: 불필요

### Story 3: 설정 페이지
- 디자인: DS 조합 (기존 Form + Toggle로 구성 가능)
```

**핵심**: Story 2는 디자인을 기다리지 않고 바로 빌드 착수 가능.

### 5. 컴포넌트 개발 + 오너 확정 + DS 등록

**DS는 디자인에서 나온다.** 새 컴포넌트가 필요할 때:

```
신규 컴포넌트 식별
  → 컴포넌트 단독 구현 (DS 프리뷰 페이지에 추가)
  → 오너 확정 ("이 카드 컴포넌트 이대로 갈까요?")
  → 확정 → DESIGN_SYSTEM.md + DS 프리뷰 페이지에 등록
  → 다음 컴포넌트로
  → 모든 신규 컴포넌트 확정 후 6단계로
```

**컴포넌트 확정 시 오너가 보는 것:**
- DS 프리뷰 페이지에서 해당 컴포넌트의 실물 렌더링
- variant 전체 (size, color, state)
- 레퍼런스 매핑이 있으면 참고 포인트 대비

**이 단계에서 "이건 아닌데"가 나오면 여기서 잡힌다** — 전체 시안 리뷰까지 가지 않음.

### 6. 전체 구성

확정된 컴포넌트(기존 + 신규)로 전체 화면을 조합.

- UX 플로우(3단계)에 따라 화면 구성
- **확정된 컴포넌트만 사용** — 이 단계에서 새 컴포넌트 만들지 않음
- 공통 규칙 (header/max-width/spacing) 준수
- 격리 세션 빌드 (시안 다양성이 필요하면 복수 세션)

### 7. 게이트

오너 프리뷰 전 자동 필터링. 비용 순서대로 계층화.

| # | 게이트 | 유형 | 검증 내용 |
|---|---|---|---|
| ① | DS 준수 린트 | 코드 | 하드코딩된 색상/간격/폰트 탐지, 토큰만 사용 확인 |
| ② | 레이아웃 규칙 | 코드 | max-width, header, container padding 준수 |
| ③ | Playwright 스크린샷 | 코드 | desktop/mobile 캡처, 빈 화면/깨진 레이아웃 탐지 |
| ④ | Judge 체크리스트 | AI | 동적 체크리스트 (CheckEval — UX 기반 Yes/No 항목 자동 생성) |

**①② 통과 못 하면 ③④ 실행 안 함** (비용 절약).

**게이트 실패 → 재작업 자동 생성** (딥리서치 반영):
- No 항목 → 수정 지시서 자동 변환 → 재빌드
- 오너가 "이거 고쳐"라고 말할 필요 없음
- keep/discard: 점수 개선 시에만 유지

**hooks로 DS 강제 주입** (딥리서치 반영):
- `UserPromptSubmit` 훅에서 DS 토큰/규칙을 자동 주입
- 프롬프트에 의존하지 않고 실행 환경에서 강제

### 8. 오너 프리뷰

게이트 전체 통과한 결과물을 오너에게 전달. **조합이든 새 시안이든 새 화면이면 항상 실행.**

피드백 분류:
- 승인 → 완료
- 컴포넌트 수정 → 5단계 (해당 컴포넌트만 재확정)
- 레이아웃 변경 → 6단계 재구성
- 플로우 변경 → 3단계 UX 재설계

최대 3회 루프. 수렴 안 되면 오너 최종 결정.

## 오너 리젝 시 재작업 프로토콜

오너가 "다시해"라고 하는 지점은 두 곳: **5단계(컴포넌트 확정)** 와 **8단계(오너 프리뷰)**.

### 5단계 리젝 — 컴포넌트 단위

```
오너: "이 카드 컴포넌트 아닌데"
  │
  ├─ 구체적 피드백 있음 ("이미지 비율이...", "여백이...")
  │     → 피드백 기반 수정 → 같은 컴포넌트 재제출
  │
  ├─ 레퍼런스 지목 ("이 사이트 카드처럼 해줘")
  │     → 레퍼런스 부분 태깅 추가 → 재빌드
  │
  └─ 방향 자체가 다름 ("카드가 아니라 리스트로 가자")
        → UX 플로우(3단계) 해당 화면 재설계 → 컴포넌트 재식별
```

**컴포넌트당 최대 2회 리젝.** 2회 초과 시:
- 현재까지의 시도 이력(스크린샷 포함) 정리해서 오너에게 제시
- "A안 vs B안 중 선택" 또는 오너가 직접 방향 지정

### 8단계 리젝 — 전체 구성

```
오너: "전체적으로 다시"
  │
  ├─ 컴포넌트는 OK, 배치가 문제
  │     → 6단계(전체 구성)만 재실행
  │
  ├─ 특정 컴포넌트가 문제
  │     → 5단계에서 해당 컴포넌트만 재확정 → 6단계 재구성
  │
  ├─ 플로우 자체가 문제 ("이 화면 필요 없었는데")
  │     → 3단계(UX) 재설계 → 4단계부터 재진행
  │
  └─ 전부 다 문제
        → 2단계(오너 인터뷰)부터 재진행 — 접근 방식 자체를 재논의
```

**8단계 최대 3회 루프.** 수렴 안 되면:
- 전체 시도 이력 정리
- 오너 최종 결정 강제 ("현재 A/B/C 중 선택 또는 구체적 방향 제시")

### 컨텍스트 보존

재작업 시 이전 결정이 날아가는 문제 방지:
- **5단계**: 확정된 컴포넌트는 DS에 즉시 등록 → 리젝된 컴포넌트와 무관하게 유지
- **8단계**: 전체 구성만 재실행, 확정된 컴포넌트 자체는 건드리지 않음 (컴포넌트 문제면 명시적으로 5단계로 돌아감)
- 매 단계 완료 시 커밋 → 어느 시점으로든 돌아갈 수 있음

## 산출물과 저장 위치

### 단계별 산출물

| 단계 | 산출물 | 저장 위치 | 실행 위치 |
|---|---|---|---|
| 1. DS 토큰 | CSS 변수 + DESIGN_SYSTEM.md 토큰 섹션 | 프로젝트 루트 | version branch |
| 2. 오너 인터뷰 | design-brief.md | `versions/vX.Y.Z/design-brief.md` | version branch |
| 2. 레퍼런스 | README.md + screenshots/ | `reference/library/` 또는 `reference/vX.Y.Z-{기능}/` | version branch |
| 3. UX 플로우 | Story별 플로우 문서 | `flows/{기능명}.md` | version branch |
| 4. Story 분기 | scope.md §Story Map에 디자인 판정 기록 | `versions/vX.Y.Z/scope.md` | version branch |
| 5. 신규 컴포넌트 | 컴포넌트 코드 + DS 프리뷰 등록 | `src/components/` + DS 프리뷰 페이지 | version branch |
| 5. DS 갱신 | DESIGN_SYSTEM.md 컴포넌트/조합/레이아웃 섹션 | 프로젝트 루트 | version branch |
| 6. 전체 구성 | 시안 페이지 | `src/app/(mockup)/vX.Y-{기능}-{variant}/` | version branch |
| 7. 게이트 결과 | 체크리스트 + 스크린샷 | `versions/vX.Y.Z/design-review.md` | version branch |

> 모든 디자인 작업은 **version/vX.Y.Z 브랜치**에서 실행. Story worktree는 ax-build(구현) 단계에서 사용. 디자인 불필요 Story는 worktree에서 바로 빌드 가능.

### 디렉토리 구조 (제품 리포 × version branch)

```
{product}/ (version/vX.Y.Z 브랜치 체크아웃 상태)
├── DESIGN_SYSTEM.md                # DS 문서 (토큰 + 컴포넌트 + 레이아웃) — 프로젝트 SSOT
├── src/
│   ├── app/(mockup)/               # 시안 페이지
│   │   ├── system/                  # DS 프리뷰 페이지 (실물 렌더링)
│   │   ├── vX.Y-profile-a/         # 시안 A
│   │   └── vX.Y-profile-b/         # 시안 B
│   └── components/                 # 확정된 컴포넌트
├── flows/                          # UX 플로우 (Story별)
├── reference/
│   ├── library/                    # 상시 수집 레퍼런스
│   ├── vX.Y.Z-{기능}/              # 작업용 레퍼런스
│   └── archive/                    # 완료된 작업 레퍼런스
├── versions/
│   └── vX.Y.Z/
│       ├── scope.md                # define 산출물 (§Story Map에 디자인 판정 포함)
│       ├── design-brief.md         # 오너 인터뷰 결과
│       └── design-review.md        # 게이트 결과 + 오너 피드백 이력
│
├── .claude/worktrees/              # Phase B에서 생성된 Story worktree
│   ├── story-1/                    # (디자인 필요 → 확정 후 빌드)
│   ├── story-2/                    # (디자인 불필요 → 바로 빌드 가능)
│   └── story-3/                    # (DS 조합 → 프리뷰 후 빌드)
```

### 산출물 라이프사이클

| 산출물 | 생성 | 갱신 | 완료 시 |
|---|---|---|---|
| DESIGN_SYSTEM.md | 1단계(토큰) → 5단계(컴포넌트) | 점진적 추가 | 유지 (프로젝트 SSOT). version branch → main 머지 시 전파 |
| design-brief.md | 2단계 | 재인터뷰 시 덮어쓰기 | versions/에 보존 |
| flows/*.md | 3단계 | 플로우 변경 시 in-place | 유지 (implement 입력). version branch → Story worktree로 전파 |
| 신규 컴포넌트 | 5단계 | 리젝 시 수정 | 확정 후 components/에 상주. version branch → Story worktree로 전파 |
| (mockup)/ 시안 | 6단계 | 리젝 시 재빌드 | 채택 시안만 유지, 미채택은 잔류 |
| design-review.md | 7단계 | 재작업 시 append | versions/에 보존 |
| DS 프리뷰 페이지 | 1단계 | 5단계에서 컴포넌트 추가 시 갱신 | 유지 (살아있는 문서) |
| reference/vX.Y.Z-*/ | 2단계 | 작업 중 추가 가능 | 완료 후 archive/로 이동 |

### version branch → Story worktree 전파

디자인 확정 후 Story worktree에서 빌드를 시작하려면, version branch의 DS/컴포넌트가 worktree에 반영되어야 함.

```bash
# version branch에서 디자인 확정 커밋 후
cd .claude/worktrees/story-1/
git merge version/vX.Y.Z    # DS + 컴포넌트 + flows 최신화
# → 이제 확정된 DS 위에서 ax-build 실행
```

### 커밋 규칙

각 오너 확정 시점에서 커밋 — 세션 끊김에 대비.

| 시점 | 커밋 메시지 패턴 |
|---|---|
| DS 토큰 확립 | `style(ds): 토큰 초기화` |
| UX 플로우 작성 | `docs(flows): {기능명} 플로우 설계` |
| 컴포넌트 오너 확정 | `feat(ds): {컴포넌트명} 확정 + DS 등록` |
| 전체 구성 완료 | `feat(mockup): vX.Y {기능명} 구성` |
| 게이트 통과 | `docs(design): vX.Y 게이트 결과 기록` |
| 오너 프리뷰 승인 | `style(design): vX.Y {기능명} 확정` |

## 범위

### 구현

| 산출물 | 설명 |
|---|---|
| `plugin/skills/ax-design/SKILL.md` | 스킬 정의 (8단계 플로우) |
| `plugin/agents/ux-designer.md` | UX 플로우 설계 에이전트 |
| `plugin/agents/design-builder.md` | 컴포넌트 개발 + 전체 구성 에이전트 |
| `plugin/scripts/ds-completeness-check.sh` | DS 토큰 확인 게이트 |
| `plugin/scripts/design-gate.sh` | DS 준수 린트 + 레이아웃 규칙 체크 |
| `plugin/skills/ax-design/references/` | 게이트 체크리스트, 레퍼런스 매핑 규칙, slop 방지 등 |
| `plugin/skills/ax-design/templates/` | DS 프리뷰 페이지 템플릿 |
| `plugin/hooks/` | UserPromptSubmit DS 자동 주입 훅 |

### 기존 자산 이식

| 가져올 것 | 소스 | 개선점 |
|---|---|---|
| slop 방지 + 안티패턴 | team-design/design-principles.md | 그대로 |
| 폰트 카탈로그 | team-design/font-*.md | 그대로 |
| 트렌드 | team-design/trends-2026.md | 그대로 |
| 도메인 체크리스트 | team-design/domain-checklists.md | CheckEval 동적 생성 입력으로 활용 |
| 레이아웃 패턴 | team-design/layout-patterns.md | 그대로 |
| 모션 레시피 | team-design/animation-recipes.md | 그대로 |
| UX 플로우 설계 | team-product/ux-designer.md | 컴포넌트 목록 산출 추가 |
| 레퍼런스 시스템 | team-product/product-design | 부분 태깅 + 오너 인터뷰 연동 |

### 딥리서치 반영

| 인사이트 | 반영 위치 |
|---|---|
| CheckEval 동적 체크리스트 (Yes/No) | 7단계 게이트 ④ |
| 실패→재작업 프롬프트 자동 생성 | 7단계 게이트 실패 처리 |
| hooks로 DS 자동 주입 | UserPromptSubmit 훅 |
| keep/discard 루프 | 7단계 게이트 반복 |
| ARIA 스냅샷 비교 | v0.4 (비범위) |
| 멀티모델 워커 (Gemini 비전) | v0.4 (비범위) |

## 비범위

- Gemini 비전 리뷰어 연동 → v0.4
- ARIA 스냅샷 구조 회귀 → v0.4
- DB_SCHEMA / API_SPEC 생성 → v0.4
- 디자인 빌드 자동 오케스트레이션 → v0.4
- 기존 team-design/team-product 수정 (건드리지 않음)

## 성공 기준

- [ ] 컴포넌트 단위 오너 확정이 작동 — 전체 시안 리뷰 전에 빌딩블록이 확정됨
- [ ] DS 준수 게이트가 하드코딩된 색상/간격을 탐지하고 차단
- [ ] 기존 DS 컴포넌트로 충분할 때 새 시안 없이 조합만으로 진행 가능
- [ ] 레퍼런스 부분 매핑이 오너 인터뷰에서 자연스럽게 수집됨
- [ ] 도그푸딩 1회에서 오너 "이건 아닌데" 횟수가 기존 대비 감소

## 상태

- [x] 페인포인트 수집 (yoyo + jojo)
- [x] 기존 자산 조사 (team-design + team-product + 딥리서치)
- [ ] 태스크 분해
- [ ] 구현
- [ ] 도그푸딩
- [ ] v0.3.0 태그 + 배포
