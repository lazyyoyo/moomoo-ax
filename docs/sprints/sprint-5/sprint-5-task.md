# sprint-5 태스크

## T0. ax-deploy SKILL.md 작성

- [ ] 산출물 최종 확인 (⏳ planned 마커, scope.md 완성도, build-plan 태스크 완료, DS 최신화, 미커밋)
- [ ] CHANGELOG 작성 규칙
- [ ] PR 생성 (version branch → main)
- [ ] preview 서버 띄우기 → 오너 확인 요청
- [ ] 오너 최종 승인
- [ ] main 머지 + 태그
- [ ] 배포 실행 (프로젝트별 배포 명령)
- [ ] BACKLOG done 이관
- [ ] QA/디자인 잔재 정리 (스크린샷 등)
- [ ] 워크트리 분기 작업 지원 (워크트리에서 실행 가능, 독립 트랙 지원)
- [ ] 가드레일

## T1. ax-qa SKILL.md 강화

현재 정적 검증 + codex review → product-qa 수준으로.

- [ ] QA 인벤토리 (flows 기반, 인벤토리 없이 테스트 금지)
- [ ] Functional QA (Playwright 유저 시뮬레이션)
- [ ] Visual QA (실제 데이터 상태 스크린샷 — 레이아웃 깨짐/오버플로우/텍스트 잘림)
- [ ] Viewport (Desktop 1600x900 + Mobile 390x844)
- [ ] 접근성 (axe-core)
- [ ] 성능 (Lighthouse)
- [ ] off-happy-path 필수 (에러/빈 상태/권한 없음/네트워크 끊김)
- [ ] 오너 수동 사용성 테스트 (편향 없는 태스크 시나리오)
- [ ] 오너 게이트 추가 (QA 판정 → 서버 띄우기 → 오너 확인 → PR)
- [ ] 스크린샷 경로 지정 (`.ax/screenshots/` + `.gitignore`)
- [ ] qa 에이전트 작성 (team-product에서 이식)

## T2. tmux 세션 자동 생성 수정

- [ ] ax-build SKILL.md 3단계에서 orchestrator 호출 연결 확인
- [ ] `ax-build-orchestrator.sh worktree` 실행 → tmux 세션 실제 생성 검증
- [ ] `.ax-brief.md` 전달 확인
- [ ] 오너가 tmux 윈도우 전환으로 세션 대화 가능 확인
- [ ] end-to-end 테스트 (worktree 생성 → tmux 세션 → 빌드 → .ax-status)

## T3. ax-help SKILL.md 작성

- [ ] team-ax 소개 (한 줄)
- [ ] 스킬 목록 + 역할 + 실행 순서 표시
- [ ] 현재 프로젝트 상태 자동 감지 (versions/ 존재, version branch, qa-report.md 등)
- [ ] build 중 안전 작업 가이드 포함
- [ ] `/ax-help` 또는 `/ax`로 호출 가능

## T4. ax-build 속도 개선

- [ ] codex exec 호출 시 변경 파일 경로만 전달 (전체 컨텍스트 붙이기 금지) — SKILL.md/references에 명시
- [ ] code review 범위 최소화 — 전체 diff가 아니라 작업 단위 diff만
- [ ] 동일 사유 2회 연속 REQUEST_CHANGES → 오너에게 위임 (무한 루프 방지)
- [ ] $ax-review code stub 여부 사전 체크 — 캐시 버전 불일치 감지 + 경고
- [ ] ax-build SKILL.md + ax-review SKILL.md에 속도 관련 가드레일 추가

## T5. 릴리즈

- [ ] plugin.json + marketplace.json 버전 bump (0.4.0 → 0.5.0)
- [ ] BACKLOG.md inbox 해소 항목 → done 이관
- [ ] 커밋 + PR + 태그

## T6. 도그푸딩

대상: rubato. define → build → qa → deploy 전 사이클.

### 검증 기준

**ax-deploy**

| # | 기준 | PASS 조건 |
|---|---|---|
| D1 | ⏳ planned 마커 체크 | 마커 남아있으면 deploy 차단 |
| D2 | 산출물 확인 | scope.md/build-plan.md/DS 완성도 체크 실행 |
| D3 | CHANGELOG 생성 | 버전별 CHANGELOG 작성됨 |
| D4 | preview → 오너 확인 | PR 생성 후 서버 띄우고 오너에게 질문 |
| D5 | main 머지 + 태그 | 오너 승인 후 머지 + 태그 생성 |
| D6 | BACKLOG done 이관 | 해소 항목이 done으로 이동 |
| D7 | 잔재 정리 | Playwright 스크린샷 등 정리 |

**ax-qa 강화**

| # | 기준 | PASS 조건 |
|---|---|---|
| Q1 | QA 인벤토리 | flows 기반 테스트 목록 먼저 작성 |
| Q2 | Functional QA | Playwright 동적 시뮬레이션 실행 |
| Q3 | Viewport | Desktop + Mobile 둘 다 테스트 |
| Q4 | 접근성 | axe-core 실행 |
| Q5 | off-happy-path | 에러/빈 상태/권한 없음 테스트 포함 |
| Q6 | 오너 게이트 | QA 후 서버 띄우고 오너 확인 대기 |
| Q7 | 스크린샷 경로 | `.ax/screenshots/`에 저장 (루트 방치 없음) |

**tmux**

| # | 기준 | PASS 조건 |
|---|---|---|
| T1 | 세션 자동 생성 | worktree 생성 시 tmux 윈도우 자동 오픈 |
| T2 | 오너 대화 | tmux 전환 후 세션에서 대화 가능 |

**ax-help**

| # | 기준 | PASS 조건 |
|---|---|---|
| H1 | 스킬 목록 | `/ax-help` 실행 시 전체 스킬 + 순서 표시 |
| H2 | 상태 감지 | 현재 프로젝트가 어느 단계인지 자동 표시 |

**빌드 속도**

| # | 기준 | PASS 조건 |
|---|---|---|
| S1 | codex review 시간 | v0.4 대비 50% 이상 단축 |
| S2 | 무한 루프 방지 | 동일 사유 2회 → 오너 위임 발동 |

**통합**

| # | 기준 | PASS 조건 |
|---|---|---|
| I1 | 전 사이클 완주 | define → build → qa → deploy 무중단 |

---

**의존 순서**: T0/T1 (병렬) → T2 → T3/T4 (병렬) → T5 → T6
