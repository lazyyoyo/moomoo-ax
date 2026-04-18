# sprint-6 태스크

## T0. ax-paperwork SKILL.md 작성

프로젝트 문서 품질 관리 — 코드-문서 정합성 자동 탐지.

- [ ] 스킬 스캐폴딩 — `plugin/skills/ax-paperwork/SKILL.md`
- [ ] 인벤토리 단계 — spec/ARCHITECTURE/BACKLOG/CHANGELOG/flows/DESIGN_SYSTEM 전수 스캔
- [ ] 코드-문서 불일치 탐지
  - spec에 있는데 코드에 없는 심볼/파일 (미구현/누락)
  - 코드에 있는데 spec에 없는 기능 (은닉 기능)
- [ ] 중복 문서 식별 — 같은 주제 2곳 이상 기술
- [ ] 오래된 내용 플래깅 — 최근 커밋과 문서 설명 불일치
- [ ] 참조 무결성 — 링크/경로 깨짐 탐지
- [ ] `paperwork-report.md` 산출 + 오너 보고 + 수정 계획
- [ ] in-place 갱신 플로우 (오너 승인 후 에이전트/본 세션이 수정)
- [ ] references/paperwork-checklist.md — 점검 항목 체크리스트
- [ ] 가드레일 — 코드 수정은 범위 밖, 문서만 만짐

## T1. ax-clean SKILL.md 작성

프로젝트 디렉토리 점검 + 잔재 정리.

- [ ] 스킬 스캐폴딩 — `plugin/skills/ax-clean/SKILL.md`
- [ ] 불필요한 파일 탐지
  - 미사용 컴포넌트 (import grep 0건)
  - 고아 시안 / 빈 디렉토리 / 캐시 잔재
- [ ] 관리 안 되는 문서
  - 참조 없는 고아 spec
  - 오래된 flows/, 미정리 versions/, 미아카이브 레퍼런스
- [ ] QA/디자인 잔재
  - 루트 방치 Playwright 스크린샷 → `.ax/screenshots/`로 이동 또는 삭제 제안
  - `.env` 백업/임시 파일
- [ ] `clean-report.md` 산출 — 정리 전/후 비교
- [ ] 오너 승인 게이트 — 삭제 대상 확인
- [ ] 삭제는 `mv ~/.Trash/`로만 (영구삭제 금지, CLAUDE.md 규칙)
- [ ] 가드레일 — git-tracked 파일은 기본 보호, 명시 동의 필요

## T2. 환경 잡일 묶음

### T2-a. moomoo-ax 전용 statusline

- [ ] 현재 statusline 설정 확인 (my-agent-office 기준)
- [ ] moomoo-ax 전용 표시 — 현재 스프린트 / 버전 / 워크트리 여부
- [ ] `.claude/statusline.sh` 또는 settings 경로에 반영
- [ ] 허브/타 프로젝트 statusline에 영향 없도록 범위 한정

### T2-b. team-design/team-product 플러그인 충돌 해소

- [ ] 충돌 재현 — "UX"/"디자인" 키워드로 team-design/ux-reviewer 자동 트리거 확인
- [ ] 비활성화 가이드 작성 — 대상 프로젝트 `.claude/settings.json` 또는 플러그인 비활성 절차
- [ ] AGENTS.md 또는 README 해당 섹션 업데이트
- [ ] 장기 제거 예정 메모 — team-ax 완전 대체 시점 기준

## T3. 도그푸딩 1회 실측

대상: rubato 또는 rofan-world (오너 결정). define → build → qa → deploy 전 사이클.

- [ ] 대상 프로젝트 선정 + 시작 시점 기록
- [ ] define — scope 확정 / AskUserQuestion 횟수 기록
- [ ] build — iteration 수 / codex review 시간 / 오너 개입 횟수
- [ ] qa — Playwright/Visual/Viewport 실행 / 오너 게이트 통과 횟수
- [ ] deploy — PR → main → 태그 → 배포 완주
- [ ] 지표 수집 — 오너 개입 횟수, 총 iteration, 소요 시간
- [ ] 발견 버그/개선점 → 각 플러그인 BACKLOG inbox 이관
- [ ] `dogfood-report.md` 작성

## T4. 릴리즈

- [ ] plugin.json + marketplace.json 버전 bump (0.5.1 → 0.6.0)
- [ ] CHANGELOG.md 업데이트
- [ ] BACKLOG.md inbox 해소 항목 → done 이관 (sprint-6)
- [ ] 커밋 + PR + 태그 (`v0.6.0`)

## 검증 기준

### ax-paperwork

| # | 기준 | PASS 조건 |
|---|---|---|
| P1 | 인벤토리 생성 | spec/ARCHITECTURE/BACKLOG/CHANGELOG/flows/DESIGN_SYSTEM 스캔 결과 표시 |
| P2 | 불일치 탐지 | spec↔코드 누락/은닉 각 1건 이상 자동 탐지 |
| P3 | 리포트 산출 | `paperwork-report.md` 생성 + 오너 제출 |
| P4 | in-place 갱신 | 오너 승인 후 문서 수정 반영 |
| P5 | 가드레일 | 코드 수정 시도 시 차단 |

### ax-clean

| # | 기준 | PASS 조건 |
|---|---|---|
| C1 | 잔재 탐지 | 루트 방치 스크린샷/고아 컴포넌트 탐지 |
| C2 | 리포트 산출 | `clean-report.md` 생성 + 정리 전/후 비교 |
| C3 | 오너 게이트 | 삭제 전 오너 승인 대기 |
| C4 | 휴지통 이동 | 삭제는 `mv ~/.Trash/`로만 수행 |

### 환경 잡일

| # | 기준 | PASS 조건 |
|---|---|---|
| E1 | statusline 동작 | moomoo-ax 터미널에서 전용 표시 |
| E2 | 충돌 가이드 | 대상 프로젝트에서 team-design/team-product 비활성화 절차 문서화 |

### 도그푸딩

| # | 기준 | PASS 조건 |
|---|---|---|
| D1 | 전 사이클 완주 | define → build → qa → deploy 무중단 |
| D2 | 지표 리포트 | 오너 개입 / iteration / 시간 기록 |
| D3 | 피드백 이관 | 발견 항목 BACKLOG inbox에 반영 |

---

**의존 순서**: T0/T1/T2 (병렬) → T3 (도그푸딩) → T4 (릴리즈)

- T0/T1: 신규 스킬 2종 — 서로 독립, 병렬 가능
- T2: 환경 설정 — 코드 영향 작음, T0/T1과 병렬 가능
- T3: T0/T1/T2 완료 후 실측 (도그푸딩은 통합 테스트 성격)
- T4: 모든 검증 통과 후 릴리즈
