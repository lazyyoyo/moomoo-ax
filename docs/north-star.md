# 북극성 지표 — 오너 개입 횟수

## 한 줄

**moomoo-ax의 성공은 오너가 team-ax 산출물을 얼마나 덜 뜯어고치는가로 측정한다.**

- 개입이 0 → 산출물이 기대치에 맞음 → product loop 성공
- 개입이 많음 → 기대치와 gap 있음 → levelup loop가 개선해야 함

모든 보조 지표(루브릭 점수, iteration 수, 토큰 소비)는 이 북극성을 설명하기 위한 선(line)이다.

## 두 채널의 역할 분리

북극성은 **두 채널로 동시에 수집**되지만, 각 채널의 역할은 완전히 다르다.

### 1. 자동 diff — 정량 채널 (1차 지표)

- **무엇**: team-ax가 생성한 산출물(파일)과 오너가 최종 커밋한 결과물의 diff
- **단위**: hunks 수 (line 수는 보조)
- **수집 방식**: 자동 (오너가 별도로 기록할 것 없음)
- **답하는 질문**: "얼마나 고쳤나?" — 정량적
- **해석**:
  - 0 hunks → 산출물 그대로 수용 (이상적)
  - 1-3 hunks → 소폭 손봄
  - 4+ hunks → 상당 수정, 개선 신호
- **한계**:
  - "왜 고쳤는지"는 모름
  - 코드 스타일 자동 포맷(prettier 등)도 hunks로 잡힐 수 있어 false positive
  - v0.3+에서 LLM 요약(`interventions.diff_summary`)으로 severity 판정

### 2. `/ax-feedback` 백로그 — 정성 채널 (개선 큐)

- **무엇**: 오너가 아무 때나 호출하는 자유 서술 피드백
- **단위**: 백로그 항목 (카운트가 아님)
- **수집 방식**: 오너가 명시적으로 입력 (`/ax-feedback`)
- **답하는 질문**: "뭘 고쳐야 하나?" — 정성적
- **해석**:
  - 항목 1개 = 개선 의뢰 1건
  - priority(high/medium/low) 태그로 처리 우선순위
  - status(open → in_progress → resolved)로 라이프사이클
- **한계**:
  - 오너가 귀찮으면 남기지 않음 → 기록 누락
  - diff로 잡히는 수치와 직접 연동 안 됨 (의도적 분리)

## 왜 두 채널로 분리하는가

- **diff만 쓰면**: "왜" 고쳤는지 모름 → 개선 방향 감 잡기 어려움
- **feedback만 쓰면**: 오너가 기록 안 한 개입은 사라짐 → 수치 신뢰 낮음
- **둘을 합치면**: diff로 "얼마나"를 객관 측정 + feedback으로 "왜/무엇"을 직접 받음

두 채널은 **대시보드에서 나란히 보이되, 같은 수치로 합산하지 않는다.**

## v0.1 상태

**이 문서는 측정 방식 정의만 포함한다.** 실제 수집은 **v0.2부터**.

- v0.1:
  - `interventions` 테이블 스키마만 생성 (row 0)
  - `feedback_backlog` 테이블 스키마만 생성 (row 0)
  - 대시보드 North Star 탭은 empty state + 이 문서 링크

## v0.2 수집 인프라 스케치

### 자동 diff 수집

```
team-ax 산출물 생성
  → product_runs.output_path 에 원본 저장
  → 오너가 수정 후 git commit
  → post-commit hook 또는 수동 /ax-diff 명령
  → git diff {output_path} HEAD 실행
  → interventions row insert
      (hunks_added, hunks_deleted, lines_added/deleted, files_changed)
```

**결정 포인트**:
- (a) post-commit hook 자동 — 강제성 높음, 설치 필요
- (b) 수동 `/ax-diff` — 설치 간단, 누락 가능
- (c) 혼합 — hook + 수동 복구 명령
- → v0.2 plan 작성 시 결정

### 피드백 수집 (`/ax-feedback`)

```
/ax-feedback "design 단계에서 색상 선택이 너무 어두웠다"
  → 현재 프로젝트/stage 컨텍스트 자동 추출
  → priority 추정 (명시 안 했으면 medium)
  → feedback_backlog row insert
```

**결정 포인트**:
- priority를 오너가 명시할지, LLM이 자동 추정할지
- resolve 시점에 해결된 levelup 버전 기록 방식

## v0.3+ 확장

### LLM 기반 diff 요약 (interventions.diff_summary)

단순 hunks 수로는 "중요한 변경"과 "포맷 정리"를 구분 못 함. 대안:

- `diff.patch` 내용을 LLM에 넣고 3 카테고리 분류
  - `minor`: 포맷/타이포/주석
  - `moderate`: 로직 보정, 엣지 케이스
  - `major`: 설계 재구성, 중요 버그 수정
- severity 분포를 대시보드에 시각화

이 분류가 stable해지면 **북극성 지표를 "major intervention 수"로 좁힐 수도 있음** (v0.4+ 논의).

### feedback backlog → levelup loop 연결

현재는 feedback이 그냥 큐. 루프와 수동 연결. 향상:

- `feedback_backlog.status=open AND priority=high` 항목이 일정 수 이상 쌓이면
- meta loop가 자동으로 관련 stage의 levelup loop를 트리거
- 해결된 feedback의 `resolved_by_version` 자동 기록

## 언제 기준선을 정할 것인가

**v0.2 실전 적용 후**. rubato 실제 작업을 몇 번 돌려본 뒤:

1. iter별 diff 수치 분포 확인
2. 대시보드에서 "이 정도면 수용 가능/불가능" 감 잡기
3. 숫자 하나로 **"이번 버전의 북극성 목표치"** 설정 (예: "한 stage당 평균 diff hunks ≤ 3")
4. 이후 버전마다 이 목표치를 낮춰가는 게 roadmap

**v0.1에서는 기준선을 정하지 않는다**. 데이터 없이 정하면 자의적.

## 관련 파일

- `PROJECT_BRIEF.md` — 북극성 지표 정의 (간략)
- `versions/v0.1/supabase-schema.sql` — `interventions`, `feedback_backlog` 테이블 DDL
- `versions/v0.1/plan.md` — v0.1 완료 기준 E에 이 문서 작성 태스크
