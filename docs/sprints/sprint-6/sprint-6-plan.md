# sprint-6 plan

**목표**: team-ax 플러그인 **v0.6** 배포 — 문서/디렉토리 품질 관리 + 환경 정리 + 실측 도그푸딩.

> sprint-5에서 define→build→qa→deploy 전 사이클이 완성됐으니, v0.6은 **사이클 외곽 품질 보강 + 실측**에 집중한다.

## 범위 (4건)

### 1. ax-paperwork 스킬

프로젝트 문서 품질 관리. 코드와 문서 간 정합성 점검 + 최적화.

**동작:**
1. 인벤토리 작성 — spec / ARCHITECTURE / BACKLOG / CHANGELOG / flows / DESIGN_SYSTEM 전수 스캔
2. 코드-문서 불일치 탐지
   - spec에 있는데 코드에 없는 것 (미구현 또는 누락)
   - 코드에 있는데 spec에 없는 것 (은닉 기능)
3. 중복 문서 식별 — 같은 주제 2곳 이상 기술
4. 오래된 내용 플래깅 — 최근 코드 변경과 다른 설명
5. 참조 무결성 — 링크/경로 깨짐
6. 오너 보고 + 수정 계획 제안 (in-place 갱신)

**산출물:** `paperwork-report.md` (발견 사항 + 수정 제안)

### 2. ax-clean 스킬

프로젝트 디렉토리 점검 + 최적화. QA/디자인 잔재 정리.

**동작:**
1. 불필요한 파일
   - 미사용 컴포넌트, 고아 시안
   - 빈 디렉토리, 캐시 잔재
2. 관리 안 되는 문서
   - 참조 없는 고아 spec
   - 오래된 flows/, 미정리 versions/, 미아카이브 레퍼런스
3. QA/디자인 잔재
   - Playwright 스크린샷이 루트에 방치 → `.ax/screenshots/`로 이동 (또는 삭제)
   - `.env` 백업/임시 파일
4. 오너 확인 후 `mv ~/.Trash/` (영구삭제 금지)

**산출물:** `clean-report.md` (정리 전/후 비교)

### 3. 환경 잡일 묶음

작은 정비 항목 2개를 하나의 태스크로 처리.

**3-1. moomoo-ax 전용 statusline**
- 현재 my-agent-office 기준 statusline 사용 중
- moomoo-ax 프로젝트 맥락에 맞는 표시로 교체 (현재 스프린트 / 버전 / 워크트리 여부 등)

**3-2. team-design/team-product 플러그인 충돌**
- ax-design 실행 시 "UX", "디자인" 키워드가 team-design의 ux-reviewer를 트리거
- team-product의 product-design도 동일 문제
- 대상 프로젝트에서 team-design/team-product 비활성화 가이드 문서화 (AGENTS.md 또는 README)
- 장기적으로 team-ax가 완전 대체 후 제거 예정 — 일단 공존 절차만

### 4. 도그푸딩 1회 (실측)

sprint-5에서 완성된 전 사이클(define→build→qa→deploy)을 **rubato 또는 rofan-world**에서 1회 완주하며 실측.

**수집 지표:**
- 오너 개입 횟수 (AskUserQuestion + 승인 게이트 + 수동 개입)
- 총 iteration 수 (ax-build 재작업 루프)
- 소요 시간 (스킬별)
- 발견된 버그/개선점 → BACKLOG inbox로 이관

**산출물:** `dogfood-report.md` — 지표 + 개선 제안.

## 비범위

- `ax-review pr` 타입 구현 → v0.7 (ax-deploy 정착 후 볼륨 큰 작업)
- Hook 기반 자동 강제 (PreToolUse) → v0.7+
- 대시보드 연동 → v0.7+
- team-ax 자기 진화 (meta loop) → v1.0
- 의존성 그래프 기반 머지 순서 자동화 → v0.7+

## 성공 기준

- [ ] `/ax-paperwork`로 실제 프로젝트(rubato 등)에서 불일치 1건 이상 자동 탐지
- [ ] `/ax-clean`으로 잔재 정리 리포트 생성 + 오너 승인 후 휴지통 이동
- [ ] moomoo-ax 터미널에서 statusline이 프로젝트 전용 표시로 동작
- [ ] 대상 프로젝트에서 team-design/team-product 충돌 해소 절차 문서화
- [ ] 도그푸딩 1회 완주 + 지표 리포트 생성 + BACKLOG 피드백 반영

## 상태

- [x] BACKLOG 수집
- [x] sprint-5 피드백 반영
- [ ] 태스크 분해 (sprint-6-task.md)
- [ ] 구현
- [ ] 도그푸딩
- [ ] v0.6.0 태그 + 배포
