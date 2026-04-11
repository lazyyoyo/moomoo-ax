# PRD Generation 규칙

## 역할
seed.md + jtbd.md + problem-frame.md + scope.md를 입력받아 PRD 문서(prd.md)를 생성하는 스크립트를 작성/개선한다.

## prd.md 구조
1. Overview: 제품명 + 한줄 설명 + 이 PRD가 다루는 범위
2. Background & Problem: Core Job Statement + 선택된 HMW + 핵심 가정
3. Goals & Success Metrics: 목표 + 지표 + Non-goal
4. User Stories: AS A / I WANT / SO THAT
5. Functional Requirements: ID, 요구사항, 우선순위, 수용 기준
6. Technical Constraints: 스택, API 의존성, 성능
7. UI/UX Direction: 핵심 플로우 + 참고 레퍼런스
8. Out of Scope
9. Open Questions

## 제약
- 마크다운 형식
- 앞 단계 문서의 내용을 종합 (새로 지어내지 않음)
- 개발자/에이전트가 바로 구현 가능한 수준의 구체성
