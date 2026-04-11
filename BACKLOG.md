# BACKLOG

moomoo-ax 프로젝트 백로그.

- **inbox**: 새로 들어온 항목 (아직 분류/정제 전)
- **ready**: 다음 버전에서 구현 가능한 상태 (spec/의존성 정리됨)
- **done**: 완료 (버전 태그 포함)

각 항목은 `[버전-접두] 제목 — 요약`.
항목 source: retro, 실전 사용 피드백, 외부 이슈, 설계 논의.

---

## inbox

### 🪲 버그 / 기술부채
- **R5: `improve_script()` 덮어쓰기 버그 (critical)** — Claude가 부분 코드 블록만 출력해도 `script.py` 전체가 덮어씌워짐. 프롬프트 강화 + 덮어쓰기 전 구조 체크 + 백업 + 롤백 필요. `src/loop.py:improve_script()`. v0.1 retro 참조.
- **token 집계 정확도 조사** — `src/claude.py` 에서 input_tokens가 실제 프롬프트 크기보다 한참 낮게 잡힘 (v0.1 첫 run에서 script input 5 / judge input 6). Claude CLI의 prompt caching 영향 추정. 대시보드 Tokens 탭 정확도에 직결.
- **`labs/{stage}/input/` 디렉토리 구조 표준 문서화** — v0.1 시 fixture를 input/fixture/ 로 넣었다가 read_dir iterdir 때문에 빈 입력 받음. 경로 설계 실패. 앞으로 모든 stage가 따를 입력 레이아웃을 정할 것.

### 🧪 재현성 / 지표
- **재현성 체크**: 같은 fixture(`rubato:0065654`) 로 `ax-qa` 를 3회 돌려 score 편차 관측. 크면 script 프롬프트 deterministic 보정 또는 rubric 오차 허용.
- **다른 fixture 확장**: rubato 의 다른 커밋(버그 픽스 / 기능 추가) 으로 rubric 일반성 확인. refactor 외 케이스에서도 0.9+ 나오는가.
- **북극성 지표 기준선 첫 설정** — 실전 데이터 2~3건 쌓인 뒤 "한 stage당 평균 diff hunks ≤ N" 식의 목표치 제안. `docs/north-star.md` 참조.

### 🚰 수집 인프라 (v0.2 핵심)
- **자동 diff 캡처** — plugin 산출물과 오너 최종 커밋의 diff 를 `interventions` 테이블에 자동 insert. 방식: `/ax-diff` 명령 or post-commit hook or 혼합. 결정 필요.
- **`/ax-feedback`** — 자유 서술 피드백 수집 CLI. 프로젝트/stage 컨텍스트 자동 추출, priority 명시/추정, `feedback_backlog` row insert.
- **`product_runs` 수집** — team-ax 플러그인 호출 시 자동 row insert. started_at/finished_at/status 전이 기록.

### 🎯 실전 적용 (v0.2 core)
- **rubato 실제 진행 브랜치에 `ax-qa` 첫 적용** — 고정 fixture 탈피, 실제 개발 중인 코드에 qa 돌려 오너 개입량 측정.
- **`ax-implement` 스켈레톤** — v0.2의 2번째 stage. rubric은 "테스트 통과율 + 타입 에러 0 + lint 0" 같은 정량 축 중심.

### 📊 대시보드 개선
- **Live 탭 30초 poll** (v0.1 는 수동 refresh)
- **Levelup 탭 score 추이 차트** — iter 별 점수 변화. 데이터 2건 이상 쌓이면 의미.
- **Feedback 탭 직접 입력 폼** — 대시보드에서 피드백 추가 (anon write policy 또는 별도 API)
- **대시보드 v2 필요 여부 판단** — v0.1 시점 "뭔 내용인지 모르겠다"는 반응. v0.2~0.3 데이터 누적 후 유지/재설계 판단.

---

## ready

(비어 있음 — v0.2 plan 작성 시 inbox 에서 선별해 ready로 이동)

---

## done

### v0.1 (2026-04-11)

- [x] **3 레이어 재정의** (meta/levelup/product) — PROJECT_BRIEF.md 전면 재작성
- [x] **배포 제품명 확정**: team-ax
- [x] **디렉토리 재편**: strategy→dogfooding, labs/ax-*, plugin/skills/ax-*, rnd/
- [x] **Supabase 스키마 재설계**: iterations drop + 4 테이블 생성 + RLS 분리
- [x] **src/db.py, src/loop.py 리팩토링**: 새 스키마 + user_name/fixture_id
- [x] **labs/ax-qa 스켈레톤**: program.md + rubric.yml + script.py + fixture
- [x] **첫 levelup run 성공**: rubato:0065654, 1 iter score 0.96, cost $0.90
- [x] **dashboard v0.1 재설계**: 6 내비 + 서버 컴포넌트 + Vercel 재배포
- [x] **docs/north-star.md**: 북극성 지표 측정 방식 정의
