# PRD: moomoo-ax 대시보드 v1

## 1. Overview

- **제품명**: moomoo-ax Dashboard
- **한줄 설명**: ax-loop 실행 로그(Supabase)를 Vercel 대시보드로 시각화하여 점수 추이·토큰 소비·프로젝트별 현황을 한눈에 파악한다.
- **범위**: v1 — Supabase 연결 + 점수 추이 차트 + 토큰 소비 차트 + 프로젝트별 카드 요약 + 필터링 UI

## 2. Background & Problem

**Core Job Statement**
> 로그가 Supabase에 쌓이기만 하고 시각화가 없어서, 루프가 수렴하는지·토큰을 얼마나 쓰는지·어떤 프로젝트가 병목인지 알 수 없을 때, ax-loop 실행 로그를 대시보드로 시각화하여 점수 추이·토큰 소비·프로젝트별 현황을 한눈에 파악하고 싶다.

**선택된 HMW**
1. Supabase에 쌓인 로그 데이터를 시각화하여 즉시 인사이트를 얻는다
2. 루프의 점수 추이를 보고 수렴 여부를 빠르게 판단한다
3. 토큰 소비량을 모니터링하여 비용 감각을 확보한다
4. 프로젝트별 현황을 비교하여 병목 프로젝트를 즉시 식별한다

**핵심 가정**
- Supabase `iterations` 테이블에 `project`, `detail.score`, `detail.tokens`, `detail.iteration` 등 시각화에 필요한 필드가 이미 존재한다 → **확인됨**
- `detail` JSONB 필드에 `type` ("iteration" / "summary"), `score`, `tokens` (script/judge/improve), `cost_usd`, `verdict`, `failed_items` 등이 포함됨
- 2인 내부 도구이므로 인증은 후순위로 미뤄도 운영에 문제없다

## 3. Goals & Success Metrics

| 목표 | 지표 |
|------|------|
| 루프 수렴 여부를 시각적으로 판단할 수 있다 | 프로젝트별 점수 추이 라인차트에서 수렴/정체/발산 패턴을 즉시 식별 가능 |
| 토큰 소비량과 비용 감각을 확보한다 | iteration별 토큰 사용량(script/judge/improve)을 바차트로 확인 가능 |
| 프로젝트 간 비교로 병목을 식별한다 | 프로젝트별 카드에서 최근 점수·총 토큰·iteration 수를 한눈에 비교 가능 |
| 데이터 → 인사이트 전환 시간을 줄인다 | 대시보드 접속 후 10초 내 전체 현황 파악 가능 |

**Non-goals**
- 토큰 비용의 정확한 금액 산출 (v2 — 모델별 단가 적용)
- 수렴 자동 감지 및 뱃지 표시 (v2)
- 실험별 rubric 항목 분해 드릴다운 (v2)
- 유저별 접근 제어 (v3)

## 4. User Stories

| ID | User Story |
|----|-----------|
| US-01 | AS A ax-loop 유저(yoyo/jojo), I WANT 대시보드에 접속하면 프로젝트별 카드 요약을 보고 싶다, SO THAT 전체 프로젝트 현황(최근 점수, 총 토큰, iteration 수)을 한눈에 파악할 수 있다 |
| US-02 | AS A ax-loop 유저, I WANT 특정 프로젝트의 점수 추이 라인차트를 보고 싶다, SO THAT 루프가 수렴하는지 정체하는지 판단할 수 있다 |
| US-03 | AS A ax-loop 유저, I WANT iteration별 토큰 소비 바차트를 보고 싶다, SO THAT 어떤 단계(script/judge/improve)에서 토큰이 많이 쓰이는지 파악할 수 있다 |
| US-04 | AS A ax-loop 유저, I WANT 프로젝트/실험을 필터링하고 싶다, SO THAT 관심 있는 프로젝트만 집중해서 볼 수 있다 |
| US-05 | AS A ax-loop 유저, I WANT 프로젝트 카드를 클릭하면 상세 차트로 이동하고 싶다, SO THAT 병목 프로젝트를 발견하면 바로 깊이 들어갈 수 있다 |

## 5. Functional Requirements

| ID | 요구사항 | 우선순위 | 수용 기준 |
|----|----------|----------|----------|
| FR-01 | Supabase `iterations` 테이블에서 데이터를 페칭하는 API 레이어 | Must | `/api/iterations`에서 project, user, experiment, type 파라미터로 필터링 가능. `detail` JSONB에서 score, tokens, cost_usd, verdict 등을 파싱하여 반환 |
| FR-02 | `/api/summary`에서 type="summary" 레코드를 반환 | Must | project별 final_score, total_iterations, total_cost_usd 포함 |
| FR-03 | Overview 페이지 — 프로젝트별 카드 요약 | Must | 각 카드에 프로젝트명, 실험명, final_score, total_iterations, total_cost_usd 표시. 카드 클릭 시 해당 프로젝트 상세로 이동 |
| FR-04 | Experiments 페이지 — 점수 추이 라인차트 | Must | X축: iteration 번호, Y축: score (0.0~1.0). 실험별 탭으로 전환. Recharts LineChart 사용 |
| FR-05 | Experiments 페이지 — 토큰 소비 바차트 | Must | X축: iteration 번호, Y축: 토큰 수. script/judge/improve 3가지 스택 구분. Recharts BarChart 사용 |
| FR-06 | Experiments 페이지 — iteration 테이블 | Must | 컬럼: iteration #, score, verdict (뱃지), cost_usd, duration_sec, timestamp. verdict별 색상 구분 (keep=green, discard=red, crash=gray) |
| FR-07 | Projects 페이지 — 프로젝트별 집계 뷰 | Must | project 필드 기준 그룹핑. 프로젝트당 실행 횟수, 평균 점수, 총 비용 표시 |
| FR-08 | Tokens 페이지 — 전체 토큰 사용 통계 | Must | 총 토큰, script/judge/improve별 합계, 총 비용. iteration별 토큰 분포 차트 |
| FR-09 | 프로젝트/유저 필터링 UI | Must | 드롭다운 또는 탭으로 project, user 필터 선택. 선택 시 모든 차트/테이블에 반영 |

## 6. Technical Constraints

| 항목 | 상세 |
|------|------|
| 프론트엔드 | Next.js 16 + React 19 + TypeScript + Tailwind CSS |
| 차트 라이브러리 | Recharts |
| 데이터 소스 | Supabase (ap-northeast-2, project id: `aqwhjtlpzpcizatvchfb`) |
| DB 테이블 | `iterations` — 컬럼: id, created_at, ax_version, user, project, detail(JSONB) |
| detail JSONB 스키마 | type, experiment, iteration, score, verdict, failed_items, tokens({script,judge,improve}×{input,output}), cost_usd, duration_sec, script_version. summary 타입은 final_score, total_iterations, total_cost_usd 포함 |
| Supabase 클라이언트 | `@supabase/supabase-js` (환경 변수: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) |
| 배포 | Vercel, 루트: `dashboard/` |
| 유저 | yoyo / jojo 2명 고정 |
| 인증 | v1에서는 미구현. 환경 변수로 Supabase anon key 사용 |

## 7. UI/UX Direction

**핵심 플로우**

1. **전체 현황 파악** (Overview)
   - 대시보드 접속 → 프로젝트별 ExperimentCard 나열
   - 각 카드: 프로젝트명, 실험명, final_score (큰 숫자), total_iterations, total_cost_usd
   - 카드 클릭 → Experiments 페이지 (해당 프로젝트/실험 필터 적용)

2. **수렴 판단** (Experiments → ScoreChart)
   - 점수 추이 라인차트에서 우상향/정체/진동 패턴 시각적 판단
   - 실험별 탭 전환으로 비교

3. **토큰 비용 감각** (Experiments → TokenChart)
   - 스택 바차트로 script/judge/improve 비중 파악
   - iteration별 변화 추이 확인

4. **병목 식별** (Projects)
   - 프로젝트별 평균 점수, 총 비용 비교
   - 비용 대비 점수가 낮은 프로젝트 = 병목

**레이아웃**
- 사이드바 네비게이션: Overview / Experiments / Projects / Tokens
- 데스크톱 전용 (모바일 반응형 미지원)
- 폰트: Pretendard

## 8. Out of Scope

- 외부 사용자 대응 (인증/권한 체계, 회원가입 플로우)
- 알림/노티피케이션 (Slack, 이메일 등)
- 루프 실행 제어 (대시보드에서 루프 시작/중지)
- 로그 데이터 편집/삭제 기능
- 모바일 반응형
- 토큰 비용의 정확한 금액 산출 (모델별 단가 적용) — v2
- 수렴 감지 자동화 (뱃지) — v2
- 실험별 rubric 항목 분해 드릴다운 — v2
- Supabase RLS + 유저별 접근 제어 — v3

## 9. Open Questions

| # | 질문 | 영향 범위 | 현재 가정 |
|---|------|----------|----------|
| 1 | `iterations` 테이블에 데이터가 충분히 쌓여 있는가? 차트가 의미 있으려면 최소 몇 iteration 필요? | 차트 UX | 실험당 최소 3~5 iteration이면 추이 파악 가능 |
| 2 | `user` 필드가 모든 레코드에 일관되게 기록되는가? (yoyo/jojo) | 필터링 | loop.py에서 `--user` 플래그로 전달. 누락 시 필터링 불가 |
| 3 | improve 단계의 토큰이 별도로 기록되는가? (script 개선 시에만 발생) | TokenChart | improve 토큰은 실패→개선 시에만 존재. 없으면 0으로 처리 |
| 4 | 대시보드 초기 로딩 성능 — 데이터가 많아지면 페이지네이션 필요한가? | API 설계 | v1은 전체 로드. 데이터량이 수백 건 수준이면 문제없음 |
