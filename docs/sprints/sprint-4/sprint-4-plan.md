# sprint-4 plan

**목표**: team-ax 플러그인 **v0.4** 배포 — `ax-build` 스킬 + `ax-qa` 최소 구현.

> ax-define = PM ("무엇을 만들지")
> ax-build = 개발팀 ("어떻게 만들지" — plan부터 구현/리뷰/오너확인까지)
> ax-qa = QA ("제대로 됐는지")

## 역할 경계 변경

**Phase B(브랜치/워크트리 생성)를 ax-define에서 ax-build로 이동.**

| 변경 전 | 변경 후 |
|---|---|
| ax-define: scope 확정 + Phase B(브랜치/워크트리) | ax-define: scope 확정만 (PM 역할 종료) |
| ax-build: 워크트리 받아서 구현 | ax-build: plan → 실행 전략(워크트리 여부 결정) → 공통 기반 → 구현 → 리뷰 → 오너확인 |

**이유**: 워크트리를 어떻게 나눌지는 구현 계획의 결과물이지, 기획의 결과물이 아니다.

## 해결할 문제 (BACKLOG inbox 전부)

| # | 문제 | 해결 |
|---|---|---|
| 1 | 워크트리 세션을 오너가 수동으로 열어야 함 | tmux로 메인 세션이 자동 생성 |
| 2 | 오너가 워크트리 세션과 대화 불가 | tmux 윈도우 전환으로 직접 대화 |
| 3 | ax-design이 독립 스킬이라 수동 실행 필요 | ax-build plan에서 디자인 포함 여부 자동 판단 |
| 4 | 디자인 중 스펙 변경 시 전파 방법 없음 | version branch 경유 전파 프로토콜 |
| 5 | Story=worktree 1:1 가정 (UX 흐름 의존성) | build plan이 실행 전략 결정 (워크트리 불필요할 수도) |
| 6 | DS 병렬 수정 시 충돌 | 공통 기반에서 순차 처리 |
| 7 | worktree별 포트 충돌 | 작업 단위별 포트 자동 할당 |
| 8 | 빌드→QA 전체 흐름 미정의 | build → 오너 확인 → 머지 → QA → main |

## 전제

- sprint-3 (v0.3) 완료 — ax-design 스킬, 게이트 스크립트, hooks 존재
- rubato v1.9.0 도그푸딩 교훈 반영

## ax-build 전체 흐름

```
입력: versions/vX.Y.Z/scope.md (ax-define 산출물)
실행 위치: 메인 세션 (제품 리포 루트)

1. plan ──────────── 구현 계획 수립
    │                  - 공통 기반 식별 (DB/API/타입/DS)
    │                  - 작업 단위 분해 (Story 단위가 아닌 구현 단위)
    │                  - 의존 관계 분석
    │                  - 실행 전략 결정 (순차/병렬/워크트리 여부)
    │
2. 공통 기반 ──────── version branch에서 순차 구축
    │                  DB → API → 타입 → DS (하위 레이어부터)
    │
3. 실행 ────────────── 전략에 따라
    │  ├── 워크트리 불필요 → version branch에서 순차 구현
    │  ├── 병렬 가능 → tmux로 워크트리 세션 자동 생성 → 병렬 구현
    │  └── 의존 관계 → 순서대로 실행
    │
4. 오너 확인 ──────── 각 작업 단위 완료 → 서버 띄우기 → 오너 확인 → merge-ready
    │
5. 머지 ────────────── 전체 merge-ready → version branch에 순차 머지
    │
6. 오너 최종 확인 ─── 전체 머지 상태에서 통합 동작 확인
    │
7. QA 넘기기 ──────── ax-qa 실행
```

### 1. plan (구현 계획 수립)

메인 세션에서 planner가 실행. **전체 버전의 구현 계획을 세운다.**

**입력:**
- `versions/vX.Y.Z/scope.md` (§Story Map, §수정 계획)
- `flows/` (UX 플로우)
- `docs/specs/` (기존 스펙)
- 기존 코드 gap 분석 (subagent로 탐색 — "구현되어있다고 가정하지 말고 확인")
- `DESIGN_SYSTEM.md` (기존 DS)

**산출물: `versions/vX.Y.Z/build-plan.md`**

```markdown
# build-plan — {제품 이름} v1.9.0

## 공통 기반 (version branch에서 순차)
- [ ] DB: pins 테이블 스키마 변경 + 마이그레이션
- [ ] API: /api/auth/pin 엔드포인트 신규
- [ ] 타입: PinGate, AuthSession 타입 정의
- [ ] DS: PinInput 컴포넌트 확정 (ax-design 호출)

## 작업 단위

### 작업 A: PIN 게이트 구현 (디자인 필요)
- 디자인: ax-design (PinInput 컴포넌트 + 게이트 화면)
- 태스크:
  - [ ] PIN 입력 화면 구현
  - [ ] PIN 검증 로직
  - [ ] 세션 관리
- 검증: PIN 입력 → 인증 → 메인 화면 접근 확인

### 작업 B: 배포 파이프라인 정리 (디자인 불필요)
- 태스크:
  - [ ] Vercel 설정 갱신
  - [ ] 환경 변수 정리
- 검증: vercel deploy --preview 성공

## 실행 전략
- 공통 기반: version branch에서 순차
- 작업 A, B: 독립 → 병렬 가능
  - 워크트리 나눌 만큼 큰가? → A는 화면+로직 있어서 O, B는 설정만이라 X
  - A: worktree에서 실행
  - B: version branch에서 직접 (워크트리 불필요)
- 의존 관계: 없음

## 포트 할당 (워크트리 사용 시)
- 작업 A: 3011
```

**실행 전략 결정 기준:**

| 조건 | 전략 |
|---|---|
| 작업이 1~2개이고 작음 | 워크트리 없이 version branch에서 순차 |
| 독립 작업이 2개 이상 + 각각 규모 있음 | 워크트리 분리 → 병렬 |
| 연결된 UX 흐름 | 같은 워크트리에서 함께 |
| 작업 B가 작업 A에 의존 | A 완료 후 B 시작 |

**오너 확인**: build-plan.md를 오너에게 보여주고 승인. 승인 후 2단계로.

### 2. 공통 기반 구축 (version branch에서 순차)

여러 작업이 공유하는 기반을 먼저 깔아놓는다.

| 영역 | 내용 |
|---|---|
| DB | 공통 테이블/컬럼 마이그레이션 |
| API | 여러 작업이 쓰는 공통 엔드포인트 |
| 타입 | 공통 타입/인터페이스 정의 |
| DS | 신규 컴포넌트 (ax-design 호출 → 오너 확정 → DS 등록) |

**순서**: DB → API → 타입 → DS (하위 레이어부터).
**공통 기반 없으면 워크트리 생성 금지.**

build-plan.md에 공통 기반 항목이 없으면 이 단계 스킵.

### 3. 실행

build-plan.md의 실행 전략에 따라 진행.

**3-a. 워크트리 없이 (version branch에서 순차)**

메인 세션에서 직접 구현:
- 태스크 1개씩 선택 → 구현 → backpressure (lint/typecheck/unit/build 통과) → 커밋 → 다음
- code review: Codex 위임 (`codex exec '$ax-review code {파일}'`)
- 완료 → 서버 띄우기 → 오너 확인

**3-b. 워크트리 병렬**

메인 세션이 다음을 수행:

1. **version branch 생성** (main에서 분기, 없으면)
2. **워크트리 생성** (작업 단위별)
3. **`.ax-brief.md` 작성** (작업 지시서를 워크트리에 저장)

```markdown
# .ax-brief.md — 작업 A

## 작업 내용
PIN 게이트 구현

## 디자인
필요 — ax-design 실행 (PinInput 컴포넌트 + 게이트 화면)

## 입력 파일
- versions/v1.9.0/scope.md
- versions/v1.9.0/build-plan.md
- flows/pin-gate.md
- docs/specs/access-gate.md
- DESIGN_SYSTEM.md

## 태스크
- [ ] PIN 입력 화면 구현
- [ ] PIN 검증 로직
- [ ] 세션 관리

## 검증
PIN 입력 → 인증 → 메인 화면 접근 확인

## 포트
3011

## 완료 조건
- lint/test 통과
- codex code review APPROVE
- 커밋 완료
- dev server 띄우기 (포트 3011)
- echo '{"status":"review-ready","port":3011}' > .ax-status
```

4. **tmux 세션 자동 생성**

```bash
tmux new-window -n "work-a" "cd .claude/worktrees/work-a && claude -p 'Read .ax-brief.md and follow the instructions.'"
```

5. 각 세션에서 자율 실행:
   - 디자인 필요 → ax-design 실행 → 구현
   - 디자인 불필요 → 바로 구현
   - 태스크별: 구현 → backpressure → 커밋
   - 전체 완료 → Codex code review → 서버 띄우기 → `review-ready`

**backpressure (각 세션 공통):**
- lint + typecheck + unit + build 통과 전 다음 태스크 금지
- 태스크 완료 = 커밋 + plan 갱신 (둘 다 안 하면 완료 아님)
- placeholder/stub 금지

**code review (Codex 위임):**
- 작업 전체 완료 시 Codex에게 위임 (`codex exec '$ax-review code'`)
- spec 정합 / DS 준수 / silent failure / 보안 / 텍스트 하드코딩 검증
- APPROVE → review-ready. REQUEST_CHANGES → 수정 후 재리뷰

**오너 대화**: 빌드 중 오너가 tmux 윈도우 전환으로 해당 세션에 직접 대화 가능.

### 4. 오너 확인

빌드 완료된 작업 단위는 dev server가 떠 있는 상태.

**`.ax-status` 상태 전이:**

| 상태 | 의미 |
|---|---|
| `building` | 빌드 진행 중 |
| `review-ready` | 빌드 + code review 완료, 서버 실행 중, 오너 확인 대기 |
| `needs-fix` | 오너 피드백 → 수정 중 |
| `merge-ready` | 오너 OK → 머지 대기 |

**오너 흐름:**
1. tmux 윈도우 전환 → 해당 세션
2. localhost:{포트} 접속 → 동작 확인
3. OK → `merge-ready`
4. 수정 필요 → 세션에서 피드백 → 수정 → 재확인

### 5. 머지

전체 `merge-ready` 후 메인 세션에서 version branch에 순차 머지.

```bash
git merge version/vX.Y.Z-work-a
git merge version/vX.Y.Z-work-b
# 충돌 시 → 오너에게 보고 + 해소 방법 제안
```

워크트리 없이 진행한 경우 이미 version branch에 있으므로 이 단계 스킵.

### 6. 오너 최종 확인

전체 머지 상태에서 통합 동작 확인.

- version branch에서 dev server 실행 (기본 포트)
- **전체 그림 확인** — 개별 작업이 아니라 통합 상태
- 오너 피드백 → 메인 세션에서 직접 수정
- 확인 완료 → ax-qa로 넘기기

### 7. QA 넘기기 (ax-qa)

**"이 버전의 모든 수정사항이 반영된 상태에서 정상 동작하는가"** 검증.

- version branch에서 통합 테스트 실행
- lint/typecheck/test 전체 통과 확인
- 주요 UX 플로우 테스트
- Codex 통합 code review

QA 통과 → PR 생성 (version/vX.Y.Z → main) → 오너 최종 승인 → 머지 + 태그.
QA 실패 → 6단계(오너 확인)에서 수정 후 재QA.

## 디자인 중 스펙 변경 처리

빌드 중 디자인 피드백에서 스펙 변경이 발생할 수 있음.

**프로토콜:**
1. 스펙 변경이 **해당 작업 내부에서만 영향** → 워크트리에서 직접 수정
2. 스펙 변경이 **다른 작업에도 영향** → version branch에서 수정 후 영향받는 워크트리에 merge 전파
3. 스펙 변경이 **scope 자체를 바꿈** → 메인 세션에서 scope.md 갱신 → build-plan 재조정

## 가드레일

1. **build-plan 오너 승인 필수** — plan 없이 구현 착수 금지
2. **공통 기반 없으면 워크트리 금지** — DB/API/타입/DS 공통 작업이 안 깔렸으면 분리 금지
3. **backpressure** — lint/typecheck/unit/build 통과 전 다음 태스크 금지
4. **태스크 완료 = 커밋** — 커밋 없이 다음 태스크 금지
5. **placeholder/stub 금지** — 모든 기능 완전 구현
6. **텍스트 하드코딩 금지** — i18n/copy 경유
7. **보안 하드코딩 금지** — 키/토큰은 환경 변수
8. **code review는 Codex 위임** — 작성 엔진 ≠ 검증 엔진
9. **발견한 버그** → 해결하거나 plan에 기록 (무시 금지)
10. **스펙 불일치** → 메인 세션에 보고

## 범위

### 구현

| 산출물 | 설명 |
|---|---|
| `plugin/skills/ax-build/SKILL.md` | 7단계 빌드 플로우 |
| `plugin/scripts/ax-build-orchestrator.sh` | version branch 생성 + 워크트리 + tmux 세션 + 완료 수집 + 머지 |
| `plugin/agents/planner.md` | 구현 계획 (gap 분석 + 실행 전략 결정) |
| `plugin/agents/executor.md` | 구현 (TDD + backpressure) |
| `plugin/skills/ax-build/references/` | backpressure 패턴, preflight 체크리스트, 보안 규칙 |
| `plugin/skills/ax-build/templates/` | build-plan.md, .ax-brief.md 템플릿 |
| ax-define SKILL.md 수정 | Phase B 제거 (scope 확정에서 끝) |
| ax-design SKILL.md 수정 | ax-build에서 호출 가능하도록 가드레일 변경 |
| `plugin/skills/ax-qa/SKILL.md` | 최소 QA 스킬 (통합 테스트 + code review) |
| `plugin/scripts/phase-b-setup.sh` 수정 | ax-build orchestrator로 통합 또는 호출 구조 변경 |

### ax-define 변경

Phase B 관련 내용 제거:
- SKILL.md에서 Phase B 섹션 → "scope 확정 후 ax-build로 넘기기"로 축소
- `phase-b-setup.sh`는 ax-build orchestrator가 호출하는 구조로 변경

### ax-design SKILL.md 수정 상세

ax-design을 삭제하지 않고 ax-build가 호출하는 구조. 다음 항목을 수정:

| 수정 위치 | 현재 | 변경 |
|---|---|---|
| 가드레일 1번 | "version branch에서만 실행" | "version branch 또는 ax-build에서 호출된 워크트리에서 실행 가능" |
| 사전 점검 | `version/vX.Y.Z` 브랜치 체크 → 아니면 중단 | ax-build 호출 시 워크트리도 허용 (`.ax-brief.md` 존재 확인으로 대체) |
| DS 수정 규칙 | version branch에서 순차 | 워크트리에서 호출됐을 때 DS 수정 필요 시 → "DS 수정은 version branch에서 처리 필요" 메시지 출력 + 메인 세션에 보고. 워크트리에서 DS 직접 수정 금지 유지. |
| 실행 위치 설명 | "version/vX.Y.Z 브랜치" 고정 | "version branch (독립 실행 시) 또는 워크트리 (ax-build 호출 시)" |
| 입력 | scope.md 경로 고정 | `.ax-brief.md`에서 scope/flows/specs 경로를 읽는 방식 추가 |

## 비범위

- ax-deploy (main 머지 후 배포 자동화) → v0.5
- Gemini 비전 리뷰어 → v0.5
- 자동 재작업 루프 (keep/discard) → v0.5
- 멀티모델 워커 → v0.5

## 성공 기준

- [ ] build-plan에서 실행 전략(워크트리 여부)을 자동 결정
- [ ] 공통 기반(DB/API/타입/DS) 구축 후 병렬 구현 진행
- [ ] tmux 세션 자동 생성 + 오너 대화 가능
- [ ] 각 작업 완료 → 서버 띄우기 → 오너 확인 → merge-ready
- [ ] 전체 머지 후 통합 확인 → QA → main 머지
- [ ] 도그푸딩 1회 (rubato)에서 define → build → QA → main 전 구간 완주

## 상태

- [x] BACKLOG inbox 수집
- [x] rubato v1.9.0 실전 교훈 반영
- [x] 역할 경계 재정의 (Phase B → ax-build 이동)
- [ ] 태스크 분해
- [ ] 구현
- [ ] 도그푸딩
- [ ] v0.4.0 태그 + 배포
