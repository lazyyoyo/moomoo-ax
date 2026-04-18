# sprint-5 plan

**목표**: team-ax 플러그인 **v0.5** 배포 — ax-deploy + ax-qa 강화 + tmux 수정 + ax-help + 빌드 속도 개선.

> define→build→qa→deploy 전체 사이클 완성 + 도그푸딩 피드백 반영.

## 범위 (5건)

### 1. ax-deploy

배포 자동화. QA 통과 후 마지막 단계.

**동작:**
1. 산출물 최종 확인
   - `⏳ planned` 마커 잔존 체크 → 남아있으면 deploy 차단
   - scope.md 섹션 완성도
   - build-plan.md 태스크 전체 완료 여부
   - DS 프리뷰 페이지 최신화
   - 미커밋 파일 없음
2. CHANGELOG 작성
3. PR 생성 (version branch → main) — 아직 안 됐으면
4. preview 서버 띄우기 (localhost 또는 Vercel preview) → 오너에게 확인 요청
5. 오너 최종 승인
6. main 머지 + 태그
6. 배포 실행 (Vercel 등 프로젝트별 배포 명령)
7. BACKLOG 정리 — 이번 버전에서 해소된 inbox 항목을 done으로 이관
8. QA/디자인 잔재 정리 (Playwright 스크린샷 등)

**워크트리 분기 작업 지원:**
- 워크트리에서도 실행 가능 (원본 repo 세션 제약 없음)
- 제품 semver과 독립된 트랙도 지원 (rubato admin 케이스)

### 2. ax-qa 강화

현재 정적 검증 + codex review만 → product-qa 수준으로.

**추가:**

| 항목 | 내용 |
|---|---|
| QA 인벤토리 | flows/ 기반 체계적 테스트 목록 작성 (인벤토리 없이 테스트 금지) |
| Functional QA | Playwright MCP로 유저 입력 시뮬레이션 |
| Visual QA | 실제 데이터 상태에서 스크린샷 — 레이아웃 깨짐, 오버플로우, 텍스트 잘림 등 시각 검증 |
| Viewport | Desktop(1600x900) + Mobile(390x844) |
| 접근성 | axe-core |
| 성능 | Lighthouse |
| off-happy-path | 에러/빈 상태/권한 없음/네트워크 끊김 필수 |
| 오너 수동 테스트 | 편향 없는 태스크 시나리오 제공 |
| 오너 게이트 | QA 판정 → 서버 띄우기 → 오너 최종 확인 → PR |

**스크린샷 경로 지정**: `.ax/screenshots/`에 저장 → `.gitignore` 추가. 루트 방치 방지.

### 3. tmux 세션 자동 생성 수정

도그푸딩에서 발견: worktree 생성 시 statusline에 표시만 되고 실제 tmux 세션이 안 뜸.

**수정:**
- `ax-build-orchestrator.sh` → 스킬 호출 연결 확인
- ax-build SKILL.md 3단계에서 orchestrator 호출이 실제로 발생하는지 검증
- tmux 세션 생성 + `.ax-brief.md` 전달 + 오너 대화 가능까지 end-to-end 확인

### 4. ax-help

플러그인 안내 스킬. `/ax-help` 또는 `/ax`로 호출.

**표시 내용:**
- team-ax 소개 (한 줄)
- 스킬 목록 + 각 역할 + 실행 순서
  ```
  ax-define → ax-build (디자인 포함) → ax-qa → ax-deploy
  ```
- 현재 프로젝트 상태 (어느 단계까지 진행됐는지)
  - `versions/` 폴더 존재 여부 → define 완료?
  - version branch 존재 여부 → build 진행 중?
  - qa-report.md 존재 여부 → QA 완료?
- build 중 안전 작업 가이드 ("코드 안 건드리는 문서 작업은 안전")

### 5. ax-build 속도 개선

도그푸딩에서 yoyo + jojo 모두 지적. codex review 1시간 30분.

**원인 분석 + 개선:**
- codex exec 호출 시 **변경 파일 경로만 전달** (전체 컨텍스트 붙이기 금지)
- code review 범위 최소화 — 전체 diff가 아니라 작업 단위 diff만
- 불필요한 재리뷰 루프 방지 — 동일 사유 2회 연속이면 오너에게 위임
- $ax-review code가 stub(v0.3 캐시)인지 확인하는 사전 체크 추가

## 비범위

- ax-paperwork / ax-clean → v0.6
- ax-review pr → v0.6
- 대시보드 연동 → v0.6+
- team-ax 자기 진화 (meta loop) → v1.0
- statusline → v0.6

## 성공 기준

- [ ] ax-deploy로 rubato에서 main 머지 + 태그 + Vercel 배포까지 완주
- [ ] ax-qa가 Playwright 동적 검증 + 오너 게이트 포함
- [ ] tmux 세션이 실제로 자동 생성되어 오너가 대화 가능
- [ ] `/ax-help`로 스킬 목록 + 현재 상태 표시
- [ ] codex review 시간이 v0.4 대비 50% 이상 단축
- [ ] 도그푸딩 1회에서 define → build → qa → deploy 전 사이클 완주

## 상태

- [x] BACKLOG 수집
- [x] 도그푸딩 피드백 반영
- [ ] 태스크 분해
- [ ] 구현
- [ ] 도그푸딩
- [ ] v0.5.0 태그 + 배포
