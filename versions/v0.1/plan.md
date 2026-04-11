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
- [x] 사이드바 내비 6개로 교체: `Live / North Star / Levelup / Projects / Feedback / Tokens`
- [x] 페이지 타이틀/설명을 새 3 레이어 컨셉에 맞게 갱신
- [x] Supabase 스키마 재설계 (기존 `iterations` 테이블 drop)
  - 새 테이블 4개 DDL 적용 완료: `levelup_runs`, `product_runs`, `feedback_backlog`, `interventions`
  - RLS: anon SELECT only, write는 service_role 전용
  - smoke test: `src/db.py`로 iteration/summary row insert → delete 검증 완료
- [x] 각 내비 페이지 최소 상태 구현 (6 페이지 전부 skeleton 완료):
  - **Live**: 최근 30분 levelup iter + 진행 중 product runs
  - **North Star**: intervention/feedback 카드 + 측정 방식 설명
  - **Levelup**: levelup_runs 테이블 (summary + iterations)
  - **Projects**: yoyo/jojo 프로젝트 카드 + product_runs 집계
  - **Feedback**: 상태별 카운트 + /ax-feedback 사용법
  - **Tokens**: stage별 토큰/비용 집계
- [x] 빈 상태 UI 에러가 아니라 대기 중 느낌 (border-dashed + 안내 메시지)
- [x] `next build` 통과, TypeScript 에러 없음, 7 routes 정상 컴파일
- [ ] Vercel 재배포 후 https://moomoo-ax.vercel.app 에서 6 내비 확인 (push 직후, 1-2분 대기)

### B. levelup loop 엔진 + `ax-qa` 스켈레톤
- [x] `src/loop.py` 검토 — 이미 범용 구조. AX_VERSION v0.1 업데이트, CLI 인자 `--project` 제거 / `--fixture` 추가, `read_dir` 에 `=== FILE: {name} ===` 마커 추가, 마지막 iter improve 스킵 가드 추가
- [x] `src/judge.py` 검토 — 완전 범용, 수정 불필요
- [x] `src/db.py` 재작성 — 새 `levelup_runs` 스키마 대응, `SUPABASE_SERVICE_ROLE_KEY` 사용
- [x] `labs/ax-qa/program.md` 작성 — 오너 규칙, 입력/출력 계약, 불변/가변 영역 구분
- [x] `labs/ax-qa/rubric.yml` 작성 — critical 4 / high 5 / medium 4 / low 2 = 15 항목
  - "Owner Expectation" 평가 항목 critical+high 로 포함
- [x] `labs/ax-qa/script.py` v1 작성 — stdin fixture → Claude CLI → QA Report stdout
- [x] script.py dry run 검증 — 부분 입력 기준 정상 동작, 7 섹션 리포트 생성 확인

### C. 고정 fixture 준비
- [x] rubato 커밋 `0065654` (refactor: search intent 헬퍼 추출) 를 fixture로 고정
- [x] `before.tsx` (1317줄), `after.tsx` (1306줄), `diff.patch` (122줄) 추출
- [x] `labs/ax-qa/input/fixture/META.md` 작성 — 커밋 해시, 변경 요약, 선택 이유, fixture_id 규약
- [ ] 재현성 체크 — 별도 작업으로 v0.1 후반에 (지금 cycle 실행 결과 본 뒤 필요 시)

### D. 1 cycle 실행 & 검증
- [x] `python src/loop.py ax-qa --user yoyo --fixture rubato:0065654 --max-iter 2 --threshold 0.95` 실행, **1 iter만에 score 0.96 → threshold 초과 → 조기 종료**
- [x] `labs/ax-qa/logs/001.json` 기록 확인 (score 0.96, failed low 1건, tokens/cost 포함)
- [x] `labs/ax-qa/best/` 갱신 확인 — output.md + script.py + score.txt
- [x] Supabase `levelup_runs` 테이블에 레코드 insert 확인 (iteration + summary 2건)
- [x] 대시보드 **Levelup** 탭에서 이 run이 보이는지 확인 (Live 탭에서도 동일 데이터 확인됨)
- [x] 대시보드 **Live** 탭에서 실행 중 상태가 뜨는지 — Vercel 배포 확인 완료
  - URL: https://moomoo-ax.vercel.app/live
  - 수동 refresh DB 조회 방식 (v0.2에서 30초 poll, v0.3에서 realtime)

### E. 북극성 지표 측정 방식 정의 (문서만, 수집은 v0.2)
- [x] `docs/north-star.md` 작성 — 오너 개입 횟수 정의 완료
  - 1차 지표 (자동 diff) + 2차 채널 (/ax-feedback) 역할 분리
  - v0.2 수집 인프라 스케치 + v0.3+ LLM severity 확장 포함
  - 기준선은 v0.2 실전 데이터 본 뒤 정한다고 명시

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

- **R1**: ~~`src/loop.py`가 구 5 stage 가정~~ → **해소**. loop.py는 이미 범용, AX_VERSION/CLI 인자 소폭 수정만으로 충분
- **R2**: 대시보드 Supabase 스키마 변경은 마이그레이션 필요 — 기존 테이블 drop/rename 시점에 dashboard 코드가 깨질 수 있음. 스키마 변경 → dashboard 코드 수정 → 배포 순서 엄수
- **R3**: fixture 재현성이 의심되는 경우(같은 입력에 다른 출력) script.py 프롬프트를 deterministic하게 잡기 어려울 수 있음. 이 경우 rubric에서 "범위 오차" 허용
- **R4**: v0.1 완료 시점에 "이 엔진이 진짜 뭔가 개선하고 있는가?"를 판단할 수 없음 — 2 iteration 이상 돌려봐야 비교 가능. v0.1은 "1 cycle 작동"만 목표로 하고, "개선이 실제로 일어나는가"는 v0.2 완료 기준에 넣을 것
- **R5** (**v0.1 첫 run에서 발견**): `improve_script()` 가 script.py를 파편적으로 덮어쓰는 버그 — Claude가 개선 의도로 일부 함수만 코드 블록에 담아도 loop.py가 그걸 script.py **전체**로 write.
  - 현 로직: `re.search(r'```python\s*\n(.*?)```', ...)` 이 뽑은 첫 블록을 통째로 덮어씀
  - 보완안: (1) "전체 script를 다 출력하라" 프롬프트 명시 강화, (2) 덮어쓰기 전 `main()`/`if __name__` 존재 여부 체크, (3) 실패 시 원본 유지
  - **v0.2 작업 목록에 추가 필요**. v0.1은 증상만 기록하고 회피 (max-iter 2에서 iter 1이 실패 안 하도록 fixture 제대로 준비)
