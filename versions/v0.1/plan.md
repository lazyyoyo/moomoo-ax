# v0.1 — 3 레이어 골격 + levelup 1 cycle + 대시보드 재설계

## 목표

> **"engine이 한 바퀴 돌고, 대시보드에서 그 한 바퀴가 보인다."**

새 3 레이어(meta/levelup/product) 기준으로 moomoo-ax를 재시작한다. 실전 프로젝트(rubato) 접목은 v0.2에서, v0.1은 **엔진 + 뼈대의 smoke test**에 집중한다.

첫 levelup 대상은 **`ax-qa`**. 이유:
- rubric 신호가 정량적 (테스트 통과율, lint/type 에러 수, coverage)
- LLM Judge 주관 편차가 작음 → 엔진 검증에 유리
- team-product에서 "implement 자잘한 버그" 병목이 사실상 qa 품질 문제와 직결

## 범위 원칙

- **통제 가능한 대상**으로 1 cycle 돌린다. 시시각각 변하는 rubato 진행 브랜치는 v0.2로 미룸.
- **새 인프라는 최소화**. 기존 Next.js + Supabase + Vercel 배포를 그대로 살리고, 내용만 재설계.
- **"자동이되, 보인다"** 원칙의 실시간 관찰 기능이 대시보드에 최소 형태로라도 들어간다.

## 완료 기준

### A. 대시보드 재설계
- [ ] 사이드바 내비 6개로 교체: `Live / North Star / Levelup / Projects / Feedback / Tokens`
- [ ] 페이지 타이틀/설명을 새 3 레이어 컨셉에 맞게 갱신
- [ ] Supabase 스키마 재설계 (기존 `iterations` 테이블은 아카이브)
  - 새 테이블 후보: `levelup_runs`, `product_runs`, `feedback_backlog`, `interventions` (이름 확정은 아래 "결정 필요" 참조)
- [ ] 각 내비 페이지 최소 상태 구현:
  - **Live**: 지금 돌고 있는 loop 목록 (levelup/product), 각각 현재 stage + 산출물 링크
  - **North Star**: "오너 개입 횟수" 측정 방식 설명 페이지 (수집 전이라 빈 차트 + 방법론)
  - **Levelup**: levelup 실험 로그 테이블 (v0.1 첫 cycle 결과가 여기 뜸)
  - **Projects**: yoyo/jojo 프로젝트 목록 (빈 카드 OK)
  - **Feedback**: 피드백 백로그 empty state + `/ax-feedback` 사용법 안내
  - **Tokens**: 단계별 토큰 소비 empty state
- [ ] 빈 상태(empty state) UI가 "에러" 아니라 "대기 중" 느낌으로 보이기
- [ ] Vercel 재배포 성공, https://moomoo-ax.vercel.app 에서 6 내비 확인

### B. levelup loop 엔진 + `ax-qa` 스켈레톤
- [ ] `src/loop.py` 검토 — 구 5 stage 전제가 박혀 있으면 6 stage 범용으로 수정
- [ ] `src/judge.py` 검토 — rubric.yml 스키마 변경 필요한지 확인
- [ ] `labs/ax-qa/program.md` 작성 — ax-qa의 오너 규칙
  - 목적, 입력/출력 계약, 실패 판정 기준
- [ ] `labs/ax-qa/rubric.yml` 작성 — "오너 기대치" 평가 항목 포함
  - 정량 축: lint 에러 0, type 에러 0, 테스트 통과율, coverage
  - 정성 축: "오너가 이 QA 리포트를 보고 추가 작업 없이 넘어갈 수 있는가"
- [ ] `labs/ax-qa/script.py` v1 작성 — Claude CLI로 qa 돌리는 최소 프롬프트
- [ ] `labs/ax-qa/input/fixture/` 준비 — 아래 "고정 fixture" 참조

### C. 고정 fixture 준비
- [ ] rubato 커밋 `0065654` (refactor: search intent 헬퍼 추출) 를 fixture로 고정
- [ ] `dev/src/app/(protected)/search/page.tsx` 의 before/after 두 버전을 `labs/ax-qa/input/fixture/` 에 복사
  - `before.tsx` — 커밋 직전 상태
  - `after.tsx` — 커밋 후 상태 (qa 대상)
- [ ] `labs/ax-qa/input/fixture/META.md` 작성 — 커밋 해시, 원본 경로, 선택 이유, before/after 의미
- [ ] 재현성 체크: 같은 fixture에 script.py 2번 돌려 결과 편차 확인 (크면 script 프롬프트 deterministic하게 보정)

### D. 1 cycle 실행 & 검증
- [ ] `python src/loop.py ax-qa` 실행, 1 iteration 완주
- [ ] `labs/ax-qa/logs/001.json` 기록 확인
- [ ] `labs/ax-qa/best/` 갱신 확인 (첫 cycle이므로 무조건 best)
- [ ] Supabase `levelup_runs` 테이블에 레코드 insert 확인
- [ ] 대시보드 **Levelup** 탭에서 이 run이 보이는지 확인
- [ ] 대시보드 **Live** 탭에서 실행 중 상태가 뜨는지 (실시간 아니어도 poll 기반 OK)

### E. 북극성 지표 측정 방식 정의 (문서만, 수집은 v0.2)
- [ ] `docs/north-star.md` 작성 — 오너 개입 횟수 정의
  - **1차 지표**: plugin 산출물과 최종 커밋 간 **자동 diff hunks 수** (v0.2에서 자동 수집)
  - **2차 채널**: `/ax-feedback` **백로그** — 자유 서술, 개선 우선순위 입력 (카운트 아님)
  - 두 채널의 역할 분리 명시: diff는 "얼마나 고쳤나" 정량, 피드백은 "뭘 고쳐야 하나" 정성
- [ ] `docs/north-star.md` 에 v0.2 수집 인프라 설계 스케치 포함

## Out of scope (v0.2 이상)

- rubato 실제 진행 브랜치 대상 qa 실전 적용 → **v0.2**
- 자동 diff 캡처 인프라 구축 → **v0.2**
- `/ax-feedback` 백로그 실제 수집 CLI → **v0.2**
- `ax-define`, `ax-design`, `ax-implement`, `ax-init`, `ax-deploy` labs 스켈레톤 → **v0.2~0.5**
- `ax-autopilot` 오케스트레이터 → **v0.4**
- 하네스 진화 (rnd/) → **v1.x**

## 확정 사항

1. **Supabase 새 테이블**: `levelup_runs` / `product_runs` / `feedback_backlog` / `interventions` (풀네임)
2. **기존 `iterations` 테이블**: **drop** (히스토리 아카이브 불필요)
3. **fixture**: `rubato` 커밋 **`0065654`** — "refactor: search intent — task 생성 로직 헬퍼 추출 (buildTaskBody, intentSuccessToast)"
   - 1 파일 (`dev/src/app/(protected)/search/page.tsx`), +19/-30
   - **리팩토링** 성격이라 qa의 classical 평가 축(기존 동작 보존 / 가독성 / 타입 안전성 / 테스트 통과)이 모두 걸림
   - 너무 작지도 크지도 않음, 첫 cycle에 적합
4. **대시보드 "Live" 탭 업데이트 방식**: v0.1은 **수동 refresh DB 조회**, v0.2에 30초 poll, v0.3에 Supabase realtime

## 리스크 / 열린 질문

- **R1**: `src/loop.py`가 구 5 stage 가정으로 짜여 있으면 리팩토링 범위가 예상보다 클 수 있음 → 먼저 코드 훑고, 변경 범위 크면 stage 범용화를 v0.1 안에서 할지 v0.2로 미룰지 결정
- **R2**: 대시보드 Supabase 스키마 변경은 마이그레이션 필요 — 기존 테이블 drop/rename 시점에 dashboard 코드가 깨질 수 있음. 스키마 변경 → dashboard 코드 수정 → 배포 순서 엄수
- **R3**: fixture 재현성이 의심되는 경우(같은 입력에 다른 출력) script.py 프롬프트를 deterministic하게 잡기 어려울 수 있음. 이 경우 rubric에서 "범위 오차" 허용
- **R4**: v0.1 완료 시점에 "이 엔진이 진짜 뭔가 개선하고 있는가?"를 판단할 수 없음 — 2 iteration 이상 돌려봐야 비교 가능. v0.1은 "1 cycle 작동"만 목표로 하고, "개선이 실제로 일어나는가"는 v0.2 완료 기준에 넣을 것
