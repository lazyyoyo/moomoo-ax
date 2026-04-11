# BACKLOG

moomoo-ax 프로젝트 백로그.

- **inbox**: 새로 들어온 항목 (아직 분류/정제 전)
- **ready**: 다음 버전에서 구현 가능한 상태 (spec/의존성 정리됨)
- **done**: 완료 (버전 태그 포함)

각 항목은 `[버전-접두] 제목 — 요약`.
항목 source: retro, 실전 사용 피드백, 외부 이슈, 설계 논의.

---

## inbox

### 🔄 stage 포팅 / (C') 확산 (v0.3+)
- **ax-qa 포팅** — v0.1 `labs/ax-qa` 는 동결. team-product/skills/product-qa → `plugin/skills/ax-qa/` 시딩 + labs 래퍼 재설계. v0.2 에서 정립한 (C') 패턴 2번째 적용. → v0.3
- **ax-define / ax-design / ax-init / ax-deploy 순차 포팅** — 각 stage 별 team-product 시딩 + labs 래퍼. → v0.3~0.5
- **자연어 규칙 → script 자동 추출** — v0.2 E5 에서 식별한 "script 후보" 를 실제로 `plugin/skills/ax-*/scripts/` 로 분리하는 자동 경로. 토큰 효율 rubric 축 기반 판정. → v0.3+

### 🧪 재현성 / 지표
- **재현성 체크**: 같은 fixture 로 3회 돌려 score 편차 관측 → v0.3
- **다른 fixture 확장**: refactor 외 케이스에서도 일반성 확인 → v0.3
- **북극성 지표 기준선 첫 설정** — 실전 데이터 2~3건 쌓인 뒤 목표치 제안 → v0.3

### 🚰 수집 인프라 (v0.3+)
- **`/ax-diff` 수동 명령** — post-commit hook 누락 보조용. ad-hoc 비교/리플레이. → v0.3
- **`product_runs` 수집** — team-ax 플러그인 호출 시 자동 row insert. → v0.3

### 📊 대시보드 개선
- **Levelup 탭 score 추이 차트** — iter 별 점수 변화. → v0.3
- **Feedback 탭 직접 입력 폼** — 대시보드 입력. v0.2 는 CLI 만. → v0.3
- **대시보드 v2 필요 여부 판단** — v0.2~0.3 데이터 누적 후 유지/재설계 판단. → v0.3

### 🧹 문서/구조
- **`labs/{stage}/input/` 디렉토리 구조 표준 문서화** — 모든 stage 가 따를 입력 레이아웃. → v0.3
- **`program.md` 스키마 문서화** — `improve_target` 필드 등 v0.2 에서 추가된 구조를 명문화. → v0.3

---

## ready (v0.2)

### 🪲 엔진 / 안정성
- **A. R5 `improve_script()` fix + `improve_target` 추상화** (critical) — 프롬프트 강화 + 언어별 구조 체크(python/markdown) + 백업 + 최소 줄수 가드 + 실패 기록. `improve_target` 필드로 덮어쓰기 대상을 stage 별 선언. 회귀 테스트 포함. `src/loop.py`.
- **B. Token 집계 조사 (rubric 입력 격상)** — `src/claude.py` prompt caching 필드 확인. 결정 (a)/(b)/(c) + **rubric 토큰 효율 축 설계**. `notes/v0.2-token-investigation.md`.

### 🚰 수집 인프라
- **C. 자동 diff post-commit hook** — `scripts/install-ax-diff-hook.sh` + `scripts/ax_post_commit.py`. `.ax-generated` 매니페스트 기반. `interventions` 자동 insert.
- **D. `/ax-feedback` CLI** — `plugin/skills/ax-feedback/SKILL.md` + `scripts/ax_feedback.py`. priority 옵션, `feedback_backlog` insert.

### 🎯 stage / 실전
- **E. `ax-implement` (C') 패턴 정립** — (E1) team-product/skills/product-implement 포팅, (E2) labs 래퍼 (program.md + rubric.yml + script.py), (E3) **haru** 작은 feature fixture (`haru:{short_sha}`), (E4) 첫 cycle, (E5) improve 경로로 SKILL.md 덮어쓰기 검증 + script 추출 후보 식별.
- **F. haru 실전 첫 적용 (v0.1 labs/ax-qa 버전)** — haru 실제 브랜치에 적용, interventions 자동 수집 확인, `first-contact.md` 체감 리포트. C 완료 후. private 제품이라 실험 자유.

### 📊 대시보드
- **G. Live 탭 30초 auto-poll** — setInterval + revalidate. 다른 탭은 수정 없음.

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
