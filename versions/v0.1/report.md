# v0.1 Report

**기간**: 2026-04-11 (1일, 단일 세션)
**목표**: 3 레이어 골격 + levelup 1 cycle + 대시보드 관측 MVP
**결과**: 완료 기준 A/B/C/D/E 전부 통과

## 한 줄 요약

> "engine이 한 바퀴 돌고, 그 한 바퀴가 대시보드에 흘러 들어오는 것이 실제로 보인다."

첫 levelup 대상 `ax-qa`는 1 iteration 만에 score **0.96**으로 threshold 초과. Supabase + Vercel 대시보드까지 end-to-end 파이프라인 확인.

## 실측 지표 (v0.1 첫 기준점)

| 항목 | 값 |
|---|---|
| iterations | 1 |
| best score | 0.96 / 1.0 |
| 실패 항목 | 1개 (low priority, "META 변경 요약 활용 흔적") |
| verdict | keep |
| cost | $0.8994 |
| duration | 31.7초 (script 생성 + judge 평가) |
| script tokens | input 5 / output 1230 |
| judge tokens | input 6 / output 306 |
| script_version | `b5bca0c0` |

**주의**: input token이 프롬프트 크기 대비 지나치게 낮음. Claude CLI의 prompt caching 영향 가능성. v0.2에서 조사.

## 완료 기준 결과

### A. 대시보드 재설계 ✅

- 사이드바 내비 6개 전면 교체: `Live / North Star / Levelup / Projects / Feedback / Tokens`
- Supabase 스키마 재설계: 기존 `iterations` drop → `levelup_runs` / `product_runs` / `feedback_backlog` / `interventions` 4 테이블
- RLS 정책: anon SELECT only, write는 service_role 전용 (delete는 아무도 허용 안 함)
- 모든 페이지 서버 컴포넌트로 작성, api route 제거
- 구 컴포넌트(`components/cards`, `components/charts`) 제거
- 빌드 통과, Vercel 재배포 완료 → https://moomoo-ax.vercel.app/live

### B. levelup loop 엔진 + `ax-qa` 스켈레톤 ✅

- `src/loop.py` 검토 + 소폭 수정 (R1 해소)
  - `AX_VERSION` v0.2 → v0.1
  - CLI 인자 `--project` 제거, `--fixture` 추가
  - `read_dir` 재귀 탐색 + `=== FILE: {rel} ===` 마커
  - 마지막 iter improve 스킵 가드
- `src/judge.py` 검토 — 완전 범용, 수정 불필요
- `src/db.py` 전면 재작성 — 새 `levelup_runs` 스키마 + `SUPABASE_SERVICE_ROLE_KEY` 사용
- `labs/ax-qa/program.md` — 오너 규칙 (리포트 템플릿, stdin/stdout 계약)
- `labs/ax-qa/rubric.yml` — critical 4 / high 5 / medium 4 / low 2 = **15 항목**
- `labs/ax-qa/script.py` — stdin fixture → Claude CLI → QA Report stdout

### C. 고정 fixture 준비 ✅

- rubato 커밋 `0065654` (refactor: search intent 헬퍼 추출) 를 fixture 로 고정
- `before.tsx` (1317줄) + `after.tsx` (1306줄) + `diff.patch` (122줄) + `META.md`
- fixture_id: `rubato:0065654`
- **재현성 체크**는 미실행 — v0.2로 이동 (별도 workitem)

### D. 1 cycle 실행 & 검증 ✅

- 실행 커맨드: `.venv/bin/python src/loop.py ax-qa --user yoyo --fixture rubato:0065654 --max-iter 2 --threshold 0.95`
- **iter 1에서 0.96 → threshold 0.95 초과 → 조기 종료**
- `logs/001.json` + `best/{output.md, script.py, score.txt}` 생성
- Supabase `levelup_runs` 에 iteration + summary 2 row insert
- Vercel 대시보드 Live/Levelup 탭에 해당 run 실시간 노출 확인

### E. 북극성 지표 측정 방식 정의 ✅

- `docs/north-star.md` 작성
- 두 채널 분리 명시: **자동 diff = 정량 / `/ax-feedback` 백로그 = 정성**
- v0.2 수집 인프라 스케치 포함
- v0.3+ LLM severity 분류 확장 설계 포함
- **기준선은 v0.2 실전 데이터 본 뒤 정함** — v0.1에서는 측정 방식만 정의

## 주요 결정 / 변경점 (세션 중)

### 프로젝트 정체성 재정의

- **PROJECT_BRIEF.md 전면 재작성** — 기존 도구-기준 3 레이어 → 목적-기준 3 레이어(meta/levelup/product)
- 배포 제품명 확정: **team-ax** (team-product 패밀리 컨벤션)
- 레이어 2 이름: `ax loop` → `levelup loop` (ax는 최상위 개념이라 레이어명 충돌)
- 북극성 지표 확정: **오너 개입 횟수 (↓)**
- 미션 문장: "오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인"
- 6 stage 메뉴는 product loop 전용 (levelup loop는 독자 흐름)

### 디렉토리 재편

- `strategy/` → `dogfooding/` (실험결과물 ≠ 프로젝트 정의 원칙)
- `versions/v0.1.md`, `versions/v0.2/` → `versions/.archive/`
- `labs/` 구 5 stage (seed/jtbd/problem/scope/prd-gen) → `.archive/`
- `plugin/skills/ax-define` → `.archive/`, 새 7 skill 껍데기 (ax-autopilot + 6 stage)
- `plugin.json` 이름 `moomoo-ax` → `team-ax`
- 신규 `rnd/` — meta loop 코드 자리 (v1.0 이후 활성)

### 인프라

- Supabase key 분리: `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_ROLE_KEY`
- 대시보드는 anon(read), 파이썬 엔진은 service_role(write)
- `.env.example` 갱신 + `dashboard/.env.local` + Vercel env 업데이트

## 발견된 문제

### R5: `improve_script()` 덮어쓰기 버그 (critical)

**증상**: 첫 run 시도 시(read_dir 버그로 빈 입력 → crash), improve_script가 Claude 응답의 첫 python 코드 블록을 `script.py` **전체**로 write. 결과적으로 81줄짜리 script.py가 `read_dir` 함수 9줄로 오버라이트됨.

**원인**: `loop.py:improve_script()` 의 코드 추출 로직:
```python
match = re.search(r'```python\s*\n(.*?)```', result["output"], re.DOTALL)
if match:
    script_py.write_text(match.group(1).strip() + "\n")
```
Claude가 개선 의도로 일부 함수만 예시 블록에 담아도 전체 파일을 덮어씀.

**v0.2 보완안**:
1. improve 프롬프트에 "반드시 script.py 전체를 출력" 강조
2. 덮어쓰기 전 필수 구조 체크 (`main()` 또는 `if __name__` 존재 여부)
3. 덮어쓰기 전 백업 — `script.py.prev` 로 보존하고 실패 시 롤백
4. 코드 블록이 너무 짧으면(<30줄) 경고/거부

### R5 관련: read_dir 서브디렉토리 미지원 (v0.1 중 해소)

**증상**: 처음 `read_dir`이 `iterdir()`이라 `labs/ax-qa/input/fixture/` 서브디렉토리를 못 읽어 빈 입력 전달.

**조치**: `rglob("*")` + `relative_to(path)` 로 재귀 탐색 + 경로 marker 변경. 해소됨.

**교훈**: fixture 디렉토리 구조 설계를 처음부터 고려했어야 함. 다음 stage 추가 시 `input/` 레이아웃을 표준화할 것.

### Token 집계 의심

script 호출 1회에 **input 5 / output 1230** 은 실제 프롬프트 규모(fixture 전체 수천 줄)와 맞지 않음. Claude CLI가 prompt caching을 적용해 input_tokens를 캐시 miss만 카운트할 가능성. v0.2 조사 항목.

## Retro

### 잘된 것

- **정체성 재정의가 세션 초반 큰 덩어리로 선행**된 게 컸음. PROJECT_BRIEF부터 확정하고 나서 구현 들어가니까 범위/순서/리스크 판단이 일관됨. 만약 구현 먼저 시작했으면 중간에 정체성 흔들리면서 롤백이 많았을 것.
- **쪼개진 커밋 단위** — 14개 커밋이 전부 의미 단위로 분리됨. 각 단계가 독립적으로 롤백 가능한 상태로 progress. plan → 디렉토리 재편 → DDL → 엔진 → 스켈레톤 → 첫 run → 대시보드.
- **리스크 선제 식별 + 즉시 해소** — R1(loop.py 구 stage 가정) 의심 먼저 훑고 사실상 해소 처리. 불필요한 걱정 제거.
- **오너 인터뷰 구조화** — Q1~Q4 구조로 정체성 결정 받은 게 효율적. "레이어 이름 충돌" 같은 핵심 인사이트가 인터뷰에서 나옴.
- **dry run 먼저** — script.py를 loop.py 통과 없이 부분 입력으로 먼저 돌려본 게 Claude 응답 품질 미리 확인하는 데 도움됨.

### 개선할 것

- **대시보드를 데이터 없이 먼저 짓는 게 맞았나?**
  - v0.1 시점엔 데이터가 단 1 row. 대부분 탭이 empty state. 사용자 반응: "뭔 내용인지 모르겠다"
  - 대안: v0.1은 Supabase + 엔진까지만, 대시보드는 v0.2에서 data 쌓인 뒤 실제 가치가 있을 때 짓기
  - 결론: **v0.2 회고 시 "대시보드 v2"를 할 것인가 vs 지금 것 유지"** 판단 필요. 유지 비용 낮으니 그대로 가다가 v0.3쯤 재설계가 현실적
- **improve_script 버그는 더 일찍 잡을 수 있었나?**
  - 기존 `src/loop.py` 훑을 때 improve 로직을 깊이 안 봤음. "범용이니까 OK"로 퉁쳤는데, 실제로는 코드 추출 로직 자체가 취약.
  - 교훈: "검토"에 "범용성"뿐 아니라 "에러 경로/실패 복구"도 포함시킬 것
- **fixture 디렉토리 구조를 처음부터 표준화하지 않음**
  - `labs/ax-qa/input/fixture/` 라는 2단 depth가 read_dir의 iterdir 제약과 부딪힘. 경로 설계 실패.
  - v0.2에서 labs/{stage}/input/ 구조를 문서화할 것
- **컨텍스트 30% 기준 피드백**이 중간에 나옴. 그 전에 사용자가 몇 번 "여기까지 할까?" 를 받았을 수 있음. 다음 세션부터는 컨텍스트 사용률 기반 제시 규칙을 철저히 (memory 저장됨)
- **재현성 체크를 v0.1 안에 넣은 건 오버스펙이었음**. v0.1은 "engine 1 cycle" 목표인데 재현성은 "여러 cycle 간 편차"라서 사실상 v0.2 질문. 처음부터 v0.2로 분리했어야 함

### 다음에 적용할 것 (다른 프로젝트 포함)

- **큰 리팩토링 세션은 "정체성 먼저" 패턴을 기본값으로**. 코드 손대기 전에 PROJECT_BRIEF를 오너와 확정.
- **dry run → 부분 검증 → full cycle** 3단계 smoke test가 기본값.
- **대시보드/관측 계층은 데이터가 최소 수십 row 쌓인 뒤 짓기** (v0.1은 예외였음, 엔진 검증용 뼈대 목적)

## 지표 스냅샷

### 세션 결과물

- 커밋: 14개
- 작성/수정 파일: ~50개
- 신규 문서: PROJECT_BRIEF.md, docs/north-star.md, labs/ax-qa/* 3 파일, dogfooding/README.md, rnd/README.md, versions/v0.1/plan.md + report.md
- 삭제/아카이브: 구 strategy/, versions/v0.1.md, versions/v0.2/, labs/{seed,jtbd,problem,scope,prd}-gen/, plugin/skills/ax-define/, dashboard 구 6 파일
- Supabase 스키마 변경: 1 테이블 drop + 4 테이블 create + 4 RLS policy

### 비용

- levelup loop 1 run: $0.8994
- (dry run 별도: $0.52 부분 입력)
- 세션 총 Claude 호출 비용은 별도 계산 (주로 대화형 호출)

## v0.2로 넘기는 것 (BACKLOG)

### 엔진/버그
- **R5: `improve_script()` 덮어쓰기 버그 fix** (critical)
  - 덮어쓰기 전 구조 체크 + 백업 + 프롬프트 강화
- **`src/claude.py` token 집계 정확도 확인** — input_tokens가 prompt caching 때문에 낮게 잡히는지 조사

### 기준선 / 데이터
- **재현성 체크**: 같은 fixture로 `ax-qa` 3회 돌려 score 편차 관측
- **다른 fixture 추가**: rubato 다른 커밋(버그 픽스 / 기능 추가) 로 rubric 일반성 확인
- **북극성 지표 기준선 첫 설정**: 실전 데이터 2~3건 확보 후 목표치 제안

### 수집 인프라
- **자동 diff 캡처**: `/ax-diff` 또는 post-commit hook → `interventions` row insert
- **`/ax-feedback`**: 자유 서술 수집 CLI → `feedback_backlog` row insert
- **`product_runs` 수집**: team-ax 플러그인 호출 시 자동 row insert

### 실전 적용
- **rubato 실제 진행 브랜치에 ax-qa 첫 적용** (v0.2 core)
- **ax-implement 스켈레톤 작성**: v0.2의 2번째 stage

### 대시보드
- Live 탭 30초 poll로 격상 (v0.1은 수동 refresh)
- Levelup 탭에 score 추이 차트 (iter별 점수 추이) — data 2건 이상 쌓이면 의미
- Feedback 탭 insert UI (직접 입력 폼, anon write policy 추가 or 별도 API)

### 문서/구조
- **labs/{stage}/input/ 디렉토리 구조 표준화 문서화**
- `src/loop.py` improve 경로에 대한 error handling 정리
