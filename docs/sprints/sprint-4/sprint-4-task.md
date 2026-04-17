# sprint-4 태스크

## T0. ax-define에서 Phase B 제거

ax-define은 scope 확정까지만. 브랜치/워크트리는 ax-build 소관.

- [ ] `ax-define/SKILL.md` — Phase B 섹션 제거 → "scope 확정 후 ax-build로 넘기기"로 축소
- [ ] `ax-define/SKILL.md` — Phase 순서 제어 다이어그램에서 Phase B 제거
- [ ] `ax-define/SKILL.md` — 가드레일에서 Phase B 관련 항목 제거
- [ ] `ax-define/SKILL.md` — 출력 섹션에서 Phase B 산출물(브랜치/워크트리) 제거

## T1. ax-build SKILL.md 작성

7단계 빌드 플로우 정의.

- [ ] 1단계: plan — 구현 계획 (공통 기반 식별 + 작업 분해 + 실행 전략 결정)
- [ ] 2단계: 공통 기반 — version branch에서 순차 (DB→API→타입→DS)
- [ ] 3단계: 실행 — 순차(version branch) / 병렬(tmux+워크트리) 분기
- [ ] 4단계: 오너 확인 — 서버 띄우기 → .ax-status 전이 → merge-ready
- [ ] 5단계: 머지 — version branch에 순차 머지
- [ ] 6단계: 오너 최종 확인 — 통합 상태 확인
- [ ] 7단계: QA 넘기기 — ax-qa 호출
- [ ] .ax-brief.md 스펙 — 작업 지시서 포맷 정의
- [ ] .ax-status 스펙 — 상태 전이 (building→review-ready→needs-fix→merge-ready)
- [ ] 디자인 중 스펙 변경 처리 프로토콜
- [ ] 가드레일 10개
- [ ] 에이전트/스킬 호출 관계 명시

## T2. ax-design SKILL.md 수정

ax-build에서 호출 가능하도록 5개 항목 변경.

- [ ] 가드레일 1번: "version branch에서만" → "version branch 또는 ax-build 호출 워크트리"
- [ ] 사전 점검: 브랜치 체크 → `.ax-brief.md` 존재 확인으로 대체 (ax-build 호출 시)
- [ ] DS 수정 규칙: 워크트리에서 DS 수정 필요 시 메인에 보고 + version branch 위임
- [ ] 실행 위치 설명: 독립 실행(version branch) / ax-build 호출(워크트리) 분기 명시
- [ ] 입력: `.ax-brief.md`에서 경로 읽는 방식 추가

## T3. orchestrator 스크립트

`ax-build-orchestrator.sh` — plan 결과에 따라 실행 환경 자동 구성.

- [ ] version branch 생성 (main에서 분기, 없으면)
- [ ] 워크트리 생성 (build-plan의 실행 전략에 따라, 병렬 필요 시에만)
- [ ] `.ax-brief.md` 자동 생성 (워크트리별 작업 지시서)
- [ ] tmux 세션 자동 생성 (`tmux new-window`)
- [ ] 포트 할당 (기본 포트 + 10 + 작업 번호)
- [ ] `.ax-status` 폴링 → 전체 merge-ready 감지
- [ ] version branch 머지 (순차)
- [ ] `phase-b-setup.sh` 통합 또는 호출 구조 결정

## T4. 에이전트 작성

- [ ] `agents/planner.md` — gap 분석 + 실행 전략 결정 (team-product에서 이식 + 워크트리 전략 추가)
- [ ] `agents/executor.md` — BE/FE 구현 (TDD + backpressure) (team-product에서 이식)

## T5. references + templates

- [ ] `references/backpressure-pattern.md` — team-product에서 이식
- [ ] `references/preflight-checklist.md` — team-product에서 이식 + DS/i18n 체크 포함
- [ ] `references/security-rules.md` — team-product에서 이식
- [ ] `templates/build-plan.md` — 공통 기반 + 작업 단위 + 실행 전략 + 포트 할당
- [ ] `templates/ax-brief.md` — 워크트리 작업 지시서

## T6. ax-qa 최소 구현

- [ ] `plugin/skills/ax-qa/SKILL.md` — 통합 테스트 흐름 (lint/typecheck/test + Codex code review + UX 플로우 테스트)
- [ ] QA 통과 → PR 생성 → 오너 승인 → main 머지 + 태그 흐름
- [ ] QA 실패 → 오너 피드백 루프

## T7. ax-review code 타입 구현

- [ ] `ax-review/SKILL.md` — code 타입 stub → 실제 구현
- [ ] `ax-review/references/code-checklist.md` — spec 정합 / DS 준수 / silent failure / 보안 / 텍스트 하드코딩 / 반복 패턴

## T8. 릴리즈

- [ ] plugin.json + marketplace.json 버전 bump (0.3.2 → 0.4.0)
- [ ] BACKLOG.md inbox 항목 8건 → done 이관
- [ ] BACKLOG.md 장기 후보에서 ax-build/ax-qa 관련 항목 정리
- [ ] 커밋 + PR + 태그

## T9. 도그푸딩

대상: rubato. define → build → QA → main 머지 전 구간.

### 검증 기준

**plan (1단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| P1 | 공통 기반 식별 | build-plan.md에 공통 DB/API/타입/DS 항목 존재 |
| P2 | 실행 전략 결정 | 순차/병렬/워크트리 여부가 명시됨 |
| P3 | 오너 승인 | build-plan.md 오너 확인 라운드트립 발생 |

**공통 기반 (2단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| C1 | 공통 기반 먼저 | 워크트리 생성 전에 공통 작업 커밋 완료 |
| C2 | DB→API→타입→DS 순서 | 하위 레이어부터 구축 |

**실행 (3단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| E1 | 워크트리 자동 생성 | orchestrator가 tmux 세션 + 워크트리 생성 (병렬 시) |
| E2 | .ax-brief.md 전달 | 각 워크트리에 작업 지시서 존재 |
| E3 | backpressure | lint/typecheck/unit/build 통과 전 다음 태스크 미진행 |
| E4 | code review Codex 위임 | `codex exec '$ax-review code'` 호출 발생 |
| E5 | 워크트리 불필요 판단 | 작업이 작으면 version branch에서 직접 실행 |
| E6 | 디자인 자동 분기 | 디자인 필요 작업에서 ax-design 자동 호출 |

**오너 확인 (4단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| O1 | 서버 자동 띄우기 | 빌드 완료 후 할당 포트로 dev server 실행 |
| O2 | 포트 충돌 없음 | 병렬 작업 간 포트 겹치지 않음 |
| O3 | tmux 대화 | 오너가 tmux 윈도우 전환으로 세션과 대화 가능 |
| O4 | merge-ready 전이 | 오너 OK → .ax-status가 merge-ready로 전환 |

**통합 (5~7단계)**

| # | 기준 | PASS 조건 |
|---|---|---|
| I1 | 순차 머지 | version branch에 충돌 없이 머지 (또는 충돌 시 해소) |
| I2 | 오너 최종 확인 | 통합 상태에서 전체 흐름 동작 확인 |
| I3 | QA 통과 | lint/typecheck/test 전체 통과 |
| I4 | main 머지 | PR → 오너 승인 → main 머지 + 태그 |

---

**의존 순서**: T0 → T1/T2 (병렬) → T3 → T4/T5 (병렬) → T6/T7 (병렬) → T8 → T9
