---
name: ax-implement
description: "구현. plan → build → review → simplify → test. Use when: /ax-implement, 구현, 빌드, 개발"
---

<!--
[ax-implement seed v0 — team-ax 포팅 노트]

이 문서는 team-product/skills/product-implement 의 seed 포팅본이다.
v0.2 원칙 (plan R12): **복사 후 불필요한 것 주석만**. 본격 재구성은 levelup loop 가 담당.

moomoo-ax 실행 환경 차이:
- src/loop.py 가 Claude CLI 를 single call 로 호출 (subagent 오케스트레이션 없음)
- conductor 메인세션 / planner·executor·reviewer·qa subagent 계층 없음
- .phase 파일, phase-usage-logger.sh, Codex Adversarial 은 v0.2 범위 밖
- references/* 파일 내용은 이 single call 에서 로드되지 않음 (경로만 유지)

→ 해당 구간은 `[ax-note]` 주석으로 표시. 로직은 건드리지 않음.
→ levelup loop 가 이 SKILL.md 를 iteration 간 개선. deterministic 규칙은 script 추출 후보.
-->

# /ax-implement

구현. plan → build → review → simplify → test.

<!-- [ax-note] 아래 "에이전트" 계층은 moomoo-ax 에선 존재하지 않음. single call 안에서 mental 수행. -->

## 에이전트

planner → executor + design-engineer → reviewer → qa

## 입력

SPEC.md, META.md, base/ (fixture 디렉토리). v0.2 ax-implement 에서는 fixture stdin 으로 받음.

## 출력

구현 코드 (파일별 전체). program.md 출력 계약 준수.

<!-- [ax-note] 브랜치 / phase 파일 / 토큰 스냅샷은 harness 가 담당. script 추출 후보. -->

## 브랜치

design에서 이미 `vX.Y/{설명}` 브랜치가 있으면 그대로 사용. 없으면 생성.

## 동작 순서

### Step 0. phase 상태 갱신

<!-- [ax-note] .phase 파일은 v0.2 out of scope. loop.py 가 run 메타를 DB 에 기록. script 추출 후보. -->

프로젝트 루트 `.phase` 파일을 갱신한다:

```bash
cat > .phase << 'PHASE_EOF'
{"team":"product","version":"<version>","phase":"implement","updated":"<ISO8601>"}
PHASE_EOF
```

- `<version>`: 현재 작업 버전 (BACKLOG.md 또는 plan.md 참조)
- `<ISO8601>`: `date -u +"%Y-%m-%dT%H:%M:%SZ"` 출력값

### Step 0a. 토큰 사용량 스냅샷

<!-- [ax-note] harness 가 매 iter tokens/cost 를 levelup_runs 에 기록. script 추출 후보. -->

```bash
bash plugins/team-plugin/scripts/phase-usage-logger.sh 2>/dev/null || true
```

### [plan]

<!-- [ax-note] planner subagent 없음. single call 이 plan 을 mental 수행하고 바로 build 로. -->

**에이전트: planner**

plan.md 작성 전 `git status --porcelain`으로 working tree 클린 상태 확인:
- 미커밋 변경이 있으면 → 오너에게 목록 표시 + commit/stash 제안 → 오너 확인 후 진행
- 클린 상태면 → 즉시 진행

1. design 산출물 + 기존 코드 gap 분석
   - subagent로 코드 탐색 ("구현되어있다고 가정하지 말고 확인")
2. versions/vX.Y/plan.md 생성 — **phase 단위로 분할**
3. 오너 확인

**phase 분할 원칙:**
- 각 phase는 독립적으로 동작 검증 가능한 단위
- phase 간 의존 관계 명시 (예: Phase 1 DB/API → Phase 2 FE 연결)
- phase별 검증 기준 포함 (예: "API route 응답 확인", "화면 렌더링 확인")

```markdown
# plan.md 구조 예시
## Phase 1: DB + API 기반
- [ ] DB 마이그레이션
- [ ] API route 구현
- [ ] Swagger 테스트 통과
→ 검증: API 엔드포인트 응답 확인

## Phase 2: FE 연결
- [ ] 목업 → 실제 코드 전환
- [ ] API 연결
→ 검증: 화면에서 데이터 표시 확인

## Phase 3: 상태 + 인터랙션
- [ ] loading/error/empty 상태
- [ ] 모션/인터랙션
→ 검증: 전체 플로우 동작 확인
```

### [preflight]

<!-- [ax-note] preflight 일부는 script 추출 후보 (git status / CLI 탐색 / ARCHITECTURE.md 검증).
     현재 single call 에선 fixture base/ 가 SSOT 이므로 대부분 skip. -->

build 시작 전 체크리스트 (`references/preflight-checklist.md`):

4. **아키텍처 스택 확인:**
   - [ ] ARCHITECTURE.md 기술 스택 읽기 — 이번 태스크에서 활용할 라이브러리 목록 파악
   - [ ] 라이브러리 설치 확인 — 사용할 라이브러리가 package.json에 설치되어 있는지 확인. 미설치 시 설치 후 진행
   - [ ] 신규 의존성 기록 — 신규 라이브러리 도입 시 ARCHITECTURE.md에 먼저 기록 후 설치

5. **CLI preflight**: 외부 서비스 CLI 접근 가능 여부 자동 탐색:
   ```bash
   which supabase && supabase projects list 2>/dev/null
   which vercel && vercel whoami 2>/dev/null
   which gh && gh auth status 2>/dev/null
   which bun || which node
   ```
   - CLI 있고 인증됨 → 에이전트가 직접 수행 (DB 마이그레이션, Storage 설정 등)
   - CLI 없거나 인증 실패 → 해당 작업만 오너에게 요청 (전체 block 아님)
   - preflight 결과를 plan.md에 기록 (접근 가능 CLI 목록 + 오너 위임 필요 항목)

6. **디자인 시스템 확인:**
   - [ ] DESIGN_SYSTEM.md 컴포넌트 목록 참조 — 목록에 없는 커스텀은 사유 기록 필수
   - [ ] 목업 안착(Anchor) 먼저 → 기능(데이터/상태/이벤트) 나중
   - [ ] token-only 스타일링 (DESIGN_SYSTEM.md 토큰만, 하드코딩 없음)
   - [ ] i18n 리소스 경유 (텍스트 하드코딩 없음)

7. **QA 인프라 (선택)**:
   - [ ] AGENTS.md에 "QA 인프라" 섹션 존재 여부
   - [ ] .env.local에 ENABLE_QA_AUTH=true 설정 여부
   - [ ] /auth/qa-login 라우트 존재 여부
   - 미존재 시: 경고 출력 ("인증 뒤 기능은 수동 검증 필요"), 블로킹 아님

8. preflight 결과를 plan.md에 기록

### [build] — phase별 반복

<!-- [ax-note] subagent 루프 없음. single call 안에서 mental 순회. -->

**에이전트: executor (BE) + design-engineer (FE)**

plan.md는 살아있는 문서 — build 중 상태/이슈/버그가 업데이트된다.

phase 단위로 build → 검증을 반복한다. 한 phase의 검증이 통과해야 다음 phase로 진행.

#### 매 이터레이션 흐름

9. plan.md에서 현재 phase의 미완료 태스크(`- [ ]`) 확인. phase 내 전부 완료면 phase 검증으로
10. 최상단 미완료 태스크 1개 선택 (BE → FE 순서)
11. executor (BE) 또는 design-engineer (FE) subagent 호출 — 태스크 1개 구현
    - spec의 완료기준 확인, lint + typecheck + unit + build 통과, **태스크 단위 커밋**까지 (커밋 없이 다음 태스크 진행 금지)
12. reviewer subagent 호출 — spec 기준 코드 리뷰
    - `APPROVE`: 다음 스텝으로
    - `REQUEST_CHANGES`: 단순 이슈 → executor/design-engineer 직접 수정, 계획 변경 필요 시 planner가 plan.md 업데이트 후 재구현
13. 태스크 완료 → plan.md 체크박스 갱신 (`- [ ]` → `- [x]`)
14. 다음 미완료 태스크로 → 10번 반복

#### phase 검증

15. phase 내 전체 태스크 완료 시 — plan.md에 정의된 검증 기준 실행 (동작 확인)
16. 검증 통과 → plan.md phase 상태 갱신 (⏳→✅) + AGENTS.md 운영 학습 사항 업데이트
16a. 검증 실패 → 해당 phase 내에서 수정 → 재검증
17. 다음 phase의 9번으로

#### 기록 규칙

- plan.md: 발견된 버그, 미구현 사항, 진행 상황 기록 (작업 목록 + 이슈 트래커)
- conductor 메인세션: 이터레이션 번호 + 완료 태스크명 + 결과 요약만

### [review-architecture] — 아키텍처 컴플라이언스 검증

**에이전트: reviewer**

build 완료 후, 코드 리뷰 직전에 아키텍처 결정 준수를 검증한다. aporia tech-spec compliance incident(v0.8~v0.9.1)에서 ARCHITECTURE.md에 명시된 라이브러리가 미설치/미사용된 채 손코딩으로 대체된 사례 기반.

18. 아키텍처 컴플라이언스 체크리스트:
    1. **의존성 정합성**
       - ARCHITECTURE.md에 명시된 라이브러리가 package.json에 설치되어 있는가
       - 설치된 라이브러리가 실제 코드에서 import/사용되고 있는가
       - 사용하기로 결정한 라이브러리 대신 손코딩한 부분이 있는가
    2. **기술 결정 준수**
       - specs/에 명시된 기술 스택이 코드에 반영되었는가
       - 기존 결정을 변경한 경우, ARCHITECTURE.md에 변경 사유가 기록되었는가
    3. **문서-코드 동기화**
       - ARCHITECTURE.md 기술 스택 섹션이 실제 package.json과 일치하는가
19. 판정:
    - 위반 발견 → 코드 수정(라이브러리 실제 사용) 또는 ARCHITECTURE.md 업데이트(결정 변경 사유 기록) 후 review로 진행
    - 위반 없음 → review로 진행

### [review] — 최종 리뷰

**에이전트: reviewer**

태스크별 리뷰는 build 이터레이션에서 수행. 여기서는 전체 변경사항의 크로스커팅 이슈를 점검한다.

<!-- [ax-note] Codex Adversarial 은 v0.2 out of scope (v0.4+ 에서 검토). -->

### Codex Adversarial 리뷰 (필수 — codex 플러그인 활성 시)

[review] 단계 시작 시 실행. codex 플러그인 미활성 시 스킵.

1. `/codex:adversarial-review --background` 실행 — 리뷰어 검증과 병렬로 이종 모델 교차 검토
2. Claude reviewer는 기존 리뷰 프로세스 병행
3. `/codex:result`로 결과 수신 → 유효한 피드백이 있으면 최종 판정에 반영

실패 시: 에러 로그 출력 + 스킵. reviewer는 Claude 단독으로 검증 완료.

20. 전체 변경사항 크로스커팅 리뷰
    - 토큰/컴포넌트 반복 패턴 감지 (3회 이상 → 오너 보고)
    - 타입 설계 일관성
    - 테스트 커버리지 갭
    - 보안 검출 (하드코딩 키/토큰, 민감정보 로그)
    - 텍스트 하드코딩 검출 (i18n/copy 미경유)
    - **아키텍처 컴플라이언스** (review-checklist.md 8번 항목 참조)
21. APPROVE / REQUEST_CHANGES
    - 단순 이슈 → executor/design-engineer 직접 수정
    - 계획 변경 → planner가 plan 업데이트 → build 재실행

### [simplify]

22. APPROVE 후 code-simplifier: 기능 보존하며 복잡성 정리

### [test]

**에이전트: qa**

23. lint → typecheck → unit → build → E2E 전체 실행

- [verify]
  23a. **브라우저 검증**: simplify 완료 후, test 전 실행. dev server 시작 확인 (이미 실행 중이면 스킵) → agent-browser-verify:
     - 페이지 로드 (HTTP 200)
     - 콘솔 에러 0개
     - 주요 UI 렌더링 (구현된 기능 화면)
     - 명백한 레이아웃 깨짐 확인
     - 이슈 발견 → design-engineer 수정 후 재확인
     - 이슈 없으면 → test 단계 진행
     - **QA 인프라 감지 시 (선택적 추가 검증)**:
       - AGENTS.md에서 "## QA 인프라" 또는 "/auth/qa-login" 감지
       - 감지됨: `/auth/qa-login?role=onboarded`로 인증 → 보호 라우트 접근 → HTTP 200 확인 + 키 UI 렌더링 확인
       - 미감지: 기존 방식 유지 (변경 없음)
       - 이 단계는 선택적 — 실패해도 블로킹하지 않고 경고만 출력

24. revise 흐름: 오너 피드백 → 수정 → 수렴까지 반복
    - **URL 전달 전 서버 검증 필수**: 오너에게 localhost URL을 안내하기 전에 (1) dev server 프로세스 존재 확인 (2) HTTP 200 응답 확인을 필수 수행. 서버 미실행 시 URL 전달 금지 (B-QASERVE)

<!-- [ax-note] /product-qa GATE 는 v0.3+ (ax-qa 포팅 후). 현재는 loop.py rubric 이 GATE 역할. -->

## GATE

테스트 전체 통과 + 오너 revise 확인 → /product-qa

## 가드레일

- DESIGN_SYSTEM.md 컴포넌트 목록 참조 — 목록에 없는 커스텀은 사유 기록
- 목업 안착(Anchor) 먼저 → 기능(데이터/상태/이벤트) 나중
- token-only 스타일링
- **텍스트 하드코딩 절대 금지** — 모든 UI 텍스트는 i18n/copy 시스템 경유
- **보안 하드코딩 절대 금지** — 키/토큰/시크릿/쿠키값은 환경 변수로만
- **민감정보 로그 출력 금지**
- **env 파일 읽기 금지** — .env 파일은 cat/read 하지 않는다. 변수명만 확인
- 보안 자동 스캔 권장 (Gitleaks 등)
- placeholder/stub 금지
- 태스크 완료 = 커밋 + plan 갱신, 둘 다 안 하면 완료 아님

### plan.md 갱신 규칙

<!-- [ax-note] 병렬 subagent 없음. plan.md 직접 갱신 규칙 moot. -->

- **순차 실행 (기본)**: executor/design-engineer가 태스크 완료 시 직접 plan.md 체크박스 갱신
- **병렬 실행 시**: subagent는 plan.md를 직접 수정하지 않는다
  - subagent는 완료 결과를 conductor에게 보고만
  - conductor가 병렬 완료 후 일괄 plan.md 갱신
  - 이유: 동시 Edit 시 파일 경합으로 갱신 누락 발생 (v0.26.0 회고)
- 테스트 통과 전 다음 태스크 금지 (backpressure)
- AGENTS.md는 운영 전용 — 진행 상태/진척도 넣지 마라 (컨텍스트 오염)
- 발견한 버그는 해결하거나 plan에 기록 (무시 금지)
- 스펙 불일치 발견 시 analyst에게 보고

## 참조

- `references/preflight-checklist.md` — build 시작 전 체크리스트
- `references/backpressure-pattern.md` — Ralph backpressure + fresh context
- `references/review-checklist.md` — pr-review-toolkit 기반 리뷰 항목
- `references/security-rules.md` — 보안 하드코딩/로그/env 규칙
