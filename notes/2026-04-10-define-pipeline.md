# Define 파이프라인 정의

2026-04-10

## 파이프라인

```
러프 아이디어 → Stage 1~3 자동 → [PO 게이트] → Stage 4~5 자동 → PRD
```

### Stage 1: Seed Capture (씨앗 수집)
- input: 러프 아이디어 (한두 줄)
- output: seed.md (한줄 아이디어, 대상 사용자, 핵심 불만/동기, 도메인, 제약)
- 자동화 난이도: 쉬움

### Stage 2: JTBD Discovery (동기 분석)
- input: seed.md
- output: jtbd.md (Core Job Statement, Job Map, Competing Solutions, Underserved Needs)
- 에이전트: 웹서치로 경쟁 대안 조사 포함

### Stage 3: Problem Framing (문제 정의)
- input: seed.md + jtbd.md
- output: problem-frame.md (HMW 질문 3~5개, 솔루션 후보 Impact×Feasibility, Selected Direction)
- **PO 게이트**: 솔루션 선택 확정. 가장 중요한 판단 지점.

### Stage 4: Scope Definition (SLC 필터)
- input: problem-frame.md
- output: scope.md (SLC 체크, v1 스코프, Out of Scope, 핵심 사용자 플로우)

### Stage 5: PRD Generation (실행 문서)
- input: seed.md + jtbd.md + problem-frame.md + scope.md
- output: prd.md (Overview, Background, Goals, User Stories, Requirements, Tech Constraints, UI Direction, Out of Scope, Open Questions)

## 설계 포인트

- 각 stage의 산출물이 다음 stage의 input
- PO 게이트는 Stage 3 후 1개만 (솔루션 선택)
- Stage 1, 5가 자동화 가장 쉬움
- 컨텍스트 누적: 파일 기반 (이전 산출물을 다음 에이전트가 읽음)
- 각 stage가 labs/ 실험 1개 = script.py 1개

## auto-research 매핑

각 stage의 script.py가 train.py 역할. rubric은 산출물 구조에서 도출.
루프로 script.py를 개선하면 → 해당 stage의 산출물 품질이 올라감.
