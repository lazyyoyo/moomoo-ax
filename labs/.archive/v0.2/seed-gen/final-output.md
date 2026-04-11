## 한줄 아이디어
team moomoo(yoyo+jojo)의 IT 제품 제작 과정에서 단계별 산출물(CPS/PRD/디자인/코드) 생성 스크립트를 auto-research 루프로 자동 개선하고, 검증된 스크립트를 plugin 스킬로 승격해 다른 프로젝트에 재사용하면서 자체 진화하는 메타 자동화 엔진.

## 대상 사용자
1차 사용자는 team moomoo 멤버인 yoyo와 jojo로, 바이브 코딩으로 여러 IT 제품(rubato, rofan-world 등)을 동시에 만드는 바이브코더/프로덕트 오너다. 추정: 향후 유사한 방식으로 다수 프로젝트를 운영하는 1~2인 규모 메이커 팀으로 확장 가능.

## 핵심 불만/동기
바이브 코딩으로 빠르게 제품을 만들 수 있지만 품질 리뷰와 피드백 재작업 루프가 오너 시간을 가장 많이 잡아먹고, 프로젝트마다 CPS·PRD 작성 같은 동일한 시행착오가 반복된다. 평가 기준이 없어 "충분히 좋은가" 판단이 매번 오너의 감에 의존하는 것도 문제다.

## 관련 도메인
AI 에이전트 자동화, 프롬프트 엔지니어링/최적화(auto-research), 제품 기획(define: CPS·JTBD·PRD), 디자인 시스템, 코드 생성, 메타 학습/자기개선 파이프라인, Claude Code plugin 생태계.

## 제약 조건
- 오너는 program.md(규칙)와 rubric.yml(평가 기준)만 정의하고 루프 내부에는 개입하지 않음
- rubric은 루프 안에서 불변, 변경은 meta-loop(버전 단위)에서만
- labs/에서 실험 후 검증된 스크립트만 plugin/으로 승격
- 루프 엔진은 범용이어야 하며 실험별 차이는 program.md + rubric.yml로만 표현
- 외부 의존성 최소화(subprocess.run 기반 Claude 호출), Supabase 로그 + Vercel 대시보드 인프라 고정
- 현재 v0.2, define 파이프라인 5단계(seed→jtbd→problem-frame→scope→prd)까지 구현 완료 상태에서 출발