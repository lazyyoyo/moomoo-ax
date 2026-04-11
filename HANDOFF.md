# HANDOFF — v0.1 종료 → v0.2 시작

**작성 시점**: 2026-04-11 세션 종료 직후
**다음 작업**: v0.2 plan 작성

## 이전 세션 요약 (1줄)

v0.1에서 프로젝트 정체성을 3 레이어(meta/levelup/product)로 재정의하고, levelup loop 엔진 + `ax-qa` 스켈레톤을 돌려 **rubato:0065654 fixture로 첫 run score 0.96** 획득. Supabase + Vercel 대시보드까지 end-to-end 파이프라인 완성.

## 반드시 먼저 읽을 문서 (순서대로)

1. **`PROJECT_BRIEF.md`** — 프로젝트 정체성 SSOT. 3 레이어, 미션, 북극성, 설계 원칙 6개. 가장 먼저 이걸 읽어야 용어와 구조가 잡힘.
2. **`versions/v0.1/report.md`** — v0.1 결과 + retro + 발견된 문제 + v0.2 넘기는 것. 특히 **R5 `improve_script` 덮어쓰기 버그** 섹션 주의.
3. **`BACKLOG.md`** — inbox 에 v0.2 후보 항목 전부 정리돼 있음. ready/ 는 비어 있으니 v0.2 plan 작성 시 선별해서 이동.
4. **`CLAUDE.md`** — 파이프라인 흐름 요약, 디렉토리 규칙, Gotchas.

(선택) `docs/north-star.md` — 북극성 지표 측정 방식. `versions/v0.1/plan.md` — v0.1 완료 기준 템플릿 참고용.

## 현재 환경 상태

- **git**: main 브랜치, origin 동기. 최신 커밋 `ab52359` (v0.1 report + BACKLOG 초기화)
- **Supabase**: `levelup_runs` 1 run (rubato:0065654, score 0.96, iter+summary 2 row), `product_runs`/`feedback_backlog`/`interventions` 전부 0 row
- **Vercel**: https://moomoo-ax.vercel.app 배포 중, 6 내비 (Live/North Star/Levelup/Projects/Feedback/Tokens)
- **Python**: `.venv/bin/python` (yaml 포함). loop 실행은 항상 venv 로
- **`.env`**: `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_ROLE_KEY` 3개 세팅됨

## 주의사항 (이 세션이 배운 것)

- **R5 버그 유념**: `src/loop.py:improve_script()` 가 Claude 응답의 첫 코드 블록을 script.py 전체로 덮어씀. v0.2에서 제일 먼저 손볼 것. 재현 조건: iter 1 crash 발생 → improve 호출 → 일부 블록으로 전체 오버라이트.
- **labs fixture 경로**: `labs/{stage}/input/` 아래에 임의의 서브디렉토리를 둬도 `read_dir` 이 `rglob` 으로 재귀 탐색. 파일 구분은 `=== FILE: {rel} ===` 마커로.
- **Token 집계 의심**: `src/claude.py` 가 Claude CLI 출력을 파싱해서 `input_tokens` 를 읽는데, v0.1 첫 run 에서 input 5 / output 1230 식으로 input이 비정상 낮음. prompt caching 영향 가능성. 조사 필요 (BACKLOG inbox).
- **커밋 규칙**: 한글 커밋 메시지, 파일/폴더 삭제 금지 (`mv ~/.Trash/` 사용), 변수/함수명은 영문, 키 하드코딩 금지 (.env).
- **세션 종료 판단**: 오너 기준 **컨텍스트 ~30% 근접 시** 리셋 제안. "오늘 여기까지" 같은 시간 기반 표현 금지. (memory 에 저장됨)

## 첫 액션: v0.2 plan 작성

### 오너 인터뷰로 먼저 확정할 것

1. **v0.2 최상위 목표**: (a) R5 버그 fix + 수집 인프라 → rubato 실전 / (b) 수집 인프라 먼저, 실전은 v0.3 / (c) R5 fix만 먼저 격리 릴리즈
2. **자동 diff 캡처 방식**: post-commit hook (강제성↑) vs `/ax-diff` 수동 (간단) vs 혼합
3. **`/ax-feedback` 사용 지점**: 오너 직접 CLI 호출 vs 대시보드 폼 vs 둘 다
4. **2번째 stage 후보**: ax-implement (v0.1 retro 에 언급) vs 다른 stage — rubric 정량 축이 명확한 것부터
5. **v0.2 범위 크기**: 1일 내 가능한 축소 버전 vs 여러 날 breakdown

### 인터뷰 없이 확정된 것 (report.md / BACKLOG 기반)

- R5 버그 fix 는 반드시 포함 (critical)
- 토큰 집계 조사 포함
- `interventions` + `feedback_backlog` 첫 수집 시작
- rubato 실전 적용은 들어가는 게 자연스러움 (v0.1 에서 fixture 로만 돌렸으므로)

### plan.md 작성 패턴

v0.1 `plan.md` 를 템플릿으로 쓰되:

- 목표 1줄
- 범위 원칙 (안 하는 것 명시)
- 완료 기준 섹션별 체크박스
- Out of scope (v0.3+ 로 미루는 것)
- 확정 사항 (인터뷰 결과)
- 리스크 / 열린 질문

## 이번 세션의 Retro 한 줄

> 정체성 재정의를 코드 손대기 전에 **먼저** 완결시킨 게 가장 큰 성공 요인. v0.2 도 동일 패턴으로: **스코프 확정 → 계획 → 구현** 순서.

## 금지 사항

- v0.1 에 대해 "끝낸 느낌" 없이 이어서 작업하지 말 것. v0.1 은 종료됨. v0.2 는 새 시작.
- `/ax-feedback`, `/ax-diff` 같은 명령은 아직 존재 안 함. 구현 대상.
- `team-ax` plugin 은 skill 껍데기만 있는 상태 (plugin/skills/ax-*/.gitkeep). 사용 가능한 건 `src/loop.py` 직접 호출 + `labs/ax-qa/` 뿐.
- dashboard 코드는 수정 시 `cd dashboard && npm run build` 로 반드시 검증. Next.js 16 / Turbopack.
