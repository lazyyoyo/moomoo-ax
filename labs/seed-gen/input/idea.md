moomoo-ax는 team moomoo(yoyo + jojo)의 IT 제품 제작 자동화 엔진이다.

핵심 아이디어:
- auto-research 패턴 기반 루프로 단계별 산출물(CPS, PRD, 디자인, 코드) 품질을 자동 개선
- define → design → implement 단계별로 "산출물을 잘 만드는 스크립트"를 최적화해서 plugin 스킬로 만들고, 다른 프로젝트(rubato, rofan-world 등)에서 재사용
- 오너는 program.md(규칙)와 rubric.yml(평가 기준)만 정의, 나머지는 루프가 자율 실행
- labs/에서 실험 → 검증된 것만 plugin/으로 승격하는 구조

중요한 특성:
- 이 제품은 자체적으로 개선하는 사이클(meta-loop)을 내장하고 있다. 다른 프로젝트에 적용하면서 발견된 문제가 labs로 피드백되어 script.py/rubric이 진화한다.
- 즉, 쓸수록 더 좋아지는 도구. 사용과 개선이 분리되지 않는다.
- yoyo와 jojo의 프로젝트가 늘어날수록 plugin의 품질이 올라가고, 새 프로젝트에서 오너 개입이 줄어든다.

현재 상태:
- v0.2에서 define 파이프라인 5단계(seed→jtbd→problem-frame→scope→prd) 구현 완료
- 루프 엔진(loop.py), judge(priority 가중치), Supabase 로그, Vercel 대시보드 껍데기까지 완료
- 다음은 이 define 파이프라인을 plugin 스킬로 만들어 다른 프로젝트에 적용, 피드백으로 자체 개선

해결하고 싶은 문제:
- 바이브 코딩으로 빠르게 만들 수 있지만, 품질은 오너가 직접 리뷰해야 함
- 리뷰 → 피드백 → 재작업 루프가 오너 시간을 가장 많이 잡아먹음
- 프로젝트마다 같은 시행착오(CPS 쓰는 법, PRD 구조 등) 반복
- 평가 기준이 없어서 "이게 충분히 좋은 건가?" 판단이 매번 감에 의존
