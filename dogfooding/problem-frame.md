## HMW Questions (우선순위순)

1. 어떻게 하면 "충분히 좋은가" 판단을 오너의 감이 아닌 rubric 기반 자동 평가로 대체할 수 있을까?
2. 어떻게 하면 품질 리뷰와 피드백 재작업 루프에 들어가는 오너 시간을 산출물 생성 단계에서 제거할 수 있을까?
3. 어떻게 하면 프로젝트마다 반복되는 CPS·PRD 작성 시행착오를 스크립트 자체의 개선으로 흡수할 수 있을까?
4. 어떻게 하면 labs/에서 검증된 스크립트를 plugin 스킬로 안전하게 승격해 다른 프로젝트에 재사용할 수 있을까?
5. 어떻게 하면 루프 엔진을 실험 불문 범용으로 유지하면서 단계별 차이를 program.md + rubric.yml만으로 표현할 수 있을까?

## Solution Candidates

| ID | 솔루션 | HMW# | Impact | Feasibility | 판정 |
|----|--------|-------|--------|-------------|------|
| S1 | rubric.yml 기반 LLM Judge(judge.py)로 산출물 점수화 → best 갱신 시에만 keep하는 루프 엔진 | 1 | H | H | ✅ 진행 |
| S2 | 실패 항목을 script.md 수정 피드백으로 자동 주입하는 self-improvement 사이클 | 2,3 | H | H | ✅ 진행 |
| S3 | labs/{experiment}/best/의 script + 산출물 쌍을 SSOT로 저장하고 임계값 초과 시 plugin/으로 승격하는 promotion 파이프라인 | 4 | H | M | ✅ 진행 |
| S4 | 루프 엔진(loop.py)을 범용 오케스트레이터로 두고 program.md + rubric.yml만 실험별 입력으로 받는 구조 | 5 | H | H | ✅ 진행 |
| S5 | Supabase 로그 + Vercel 대시보드로 iteration별 점수/diff/best 승격 이력 시각화 | 1,2 | M | H | ✅ 진행 |
| S6 | 오너가 define 파이프라인 5단계 중 한 단계만 골라 돌리는 단계별 독립 실행 모드 | 2,3 | M | H | ⏳ 후순위 |
| S7 | rubric 자체를 개선하는 meta-loop(버전 단위)로 평가 기준을 진화시키는 2차 루프 | 1 | H | L | ⏳ 후순위 |
| S8 | 여러 script 변형을 병렬로 돌려 tournament 방식으로 best 선정 | 2 | M | L | ⏳ 후순위 |

## Selected Direction

- **핵심 솔루션**: S1 + S2 + S3 + S4 + S5 (v0.2 루프 엔진 MVP 번들)
- **이유**: JTBD의 4가지 Underserved Needs는 독립적으로 풀리지 않고 하나의 파이프라인으로 연결됨 — rubric 자동 평가(S1)가 있어야 감 의존 판단을 대체할 수 있고, self-improvement 피드백(S2)이 있어야 재작업 시간이 줄고, promotion 파이프라인(S3)이 있어야 재사용이 가능하며, 범용 엔진(S4)이 있어야 단계별 실험이 program.md + rubric.yml만으로 표현되고, 대시보드(S5)가 있어야 오너가 루프 내부에 개입하지 않고도 상태를 확인할 수 있음. v0.2 범위와 정확히 일치.
- **핵심 가정**:
  1. rubric.yml로 표현된 평가 기준이 오너의 "충분히 좋은가" 감을 ≥80% 수준으로 근사할 수 있다
  2. LLM Judge 점수가 iteration 간 비교 가능할 만큼 일관적이다 (같은 산출물에 대해 편차 작음)
  3. script.md 수정 피드백 주입만으로 단조 개선이 일어난다 (로컬 최적해에 갇히지 않음)
  4. labs → plugin 승격 기준을 점수 임계값 + 수동 리뷰로 충분히 게이트할 수 있다
  5. define 5단계 각각이 범용 루프 엔진 하나로 커버 가능하다 (단계별 특수 로직 불필요)