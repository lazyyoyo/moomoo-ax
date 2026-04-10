## 한줄 아이디어
ax-loop 실행 로그(Supabase)를 Vercel 대시보드로 시각화하여 점수 추이·토큰 소비·프로젝트별 현황을 한눈에 파악한다.

## 대상 사용자
yoyo와 jojo 두 명. 각각 rubato, rofan-world, moomoo-ax 등 여러 프로젝트에서 ax-loop를 돌리며 루프 품질과 비용을 모니터링해야 하는 사람들.

## 핵심 불만/동기
로그가 Supabase에 쌓이기만 하고 시각화가 없어서, 루프가 수렴하는지·토큰을 얼마나 쓰는지·어떤 프로젝트가 병목인지 알 수 없다. 데이터는 있는데 인사이트가 없는 상태.

## 관련 도메인
LLM 자동 최적화 루프 모니터링, 실험 추적 대시보드 (MLOps/실험관리 계열)

## 제약 조건
- 데이터 소스는 Supabase (ap-northeast-2, project id: aqwhjtlpzpcizatvchfb)
- 프론트엔드는 Vercel + Next.js (moomoo-ax/dashboard/ 디렉토리)
- 유저는 yoyo / jojo 두 명으로 고정
- 추정: 인증은 별도 구현 없이 간단한 수준이면 충분할 것으로 보임 (2인 내부 도구)