## 1. Overview

- **제품명**: moomoo-ax — auto-research 루프로 단계별 산출물 생성 스크립트를 자체 개선하는 메타 자동화 엔진
- **한줄 설명**: team moomoo(yoyo+jojo)의 IT 제품 제작 단계별 산출물(CPS/PRD/디자인/코드) 생성 스크립트를 auto-research 루프로 자동 개선하고, 검증된 스크립트를 plugin 스킬로 승격해 재사용하는 자체 진화 엔진
- **이 PRD가 다루는 범위 (v1 = v0.2)**:
  - 범용 루프 엔진(loop.py) + LLM Judge(judge.py) + Supabase 로그(db.py)
  - labs/{experiment} 실험 디렉토리 구조 + best/ 갱신 + self-improvement 피드백
  - Vercel 대시보드 실험 상세 뷰 (iteration별 점수 추이 + best 승격 이력)
  - labs → plugin 승격 파이프라인 (수동 승인 게이트 포함)
  - labs/cps-writing 실험 1개로 end-to-end 검증

## 2. Background & Problem

**Core Job Statement**
When 바이브 코딩으로 빠르게 제품을 만들 수 있지만 품질 리뷰와 피드백 재작업 루프가 오너 시간을 가장 많이 잡아먹고, 프로젝트마다 CPS·PRD 작성 같은 동일한 시행착오가 반복될 때, I want to 평가 기준이 없어 "충분히 좋은가" 판단이 매번 오너의 감에 의존하는 문제를 해결하고 싶다, so I can 단계별 산출물 생성 스크립트를 auto-research 루프로 자동 개선하고 검증된 스크립트를 plugin 스킬로 승격해 재사용하는 자체 진화 엔진을 갖출 수 있다.

**선택된 HMW (우선순위순)**
1. 어떻게 하면 "충분히 좋은가" 판단을 오너의 감이 아닌 rubric 기반 자동 평가로 대체할 수 있을까?
2. 어떻게 하면 품질 리뷰와 피드백 재작업 루프에 들어가는 오너 시간을 산출물 생성 단계에서 제거할 수 있을까?
3. 어떻게 하면 프로젝트마다 반복되는 CPS·PRD 작성 시행착오를 스크립트 자체의 개선으로 흡수할 수 있을까?
4. 어떻게 하면 labs/에서 검증된 스크립트를 plugin 스킬로 안전하게 승격해 다른 프로젝트에 재사용할 수 있을까?
5. 어떻게 하면 루프 엔진을 실험 불문 범용으로 유지하면서 단계별 차이를 program.md + rubric.yml만으로 표현할 수 있을까?

**핵심 가정**
1. rubric.yml로 표현된 평가 기준이 오너의 "충분히 좋은가" 감을 ≥80% 수준으로 근사할 수 있다
2. LLM Judge 점수가 iteration 간 비교 가능할 만큼 일관적이다 (같은 산출물에 대해 편차 작음)
3. script.md 수정 피드백 주입만으로 단조 개선이 일어난다 (로컬 최적해에 갇히지 않음)
4. labs → plugin 승격 기준을 점수 임계값 + 수동 리뷰로 충분히 게이트할 수 있다
5. define 5단계 각각이 범용 루프 엔진 하나로 커버 가능하다 (단계별 특수 로직 불필요)

## 3. Goals & Success Metrics

- **목표 1**: 오너 감 의존 판단을 rubric 자동 평가로 대체
  → 지표: labs/cps-writing 실험에서 rubric 총점과 오너 수동 평가의 상관계수 ≥ 0.8
- **목표 2**: 산출물 생성 단계 재작업 시간 제거
  → 지표: 오너가 루프 실행 중 개입 횟수 = 0 (시작/종료 시점 제외)
- **목표 3**: 스크립트 자체 개선이 단조 증가
  → 지표: cps-writing 실험에서 10 iteration 내 best 점수가 초기 대비 ≥ 20% 상승
- **목표 4**: 범용 엔진 유지 (단계별 특수 로직 무)
  → 지표: loop.py / judge.py 코드가 실험 종류에 의존하는 분기 = 0
- **목표 5**: 검증된 스크립트 재사용 가능
  → 지표: cps-writing script가 plugin/.claude-plugin/ 으로 승격되고 다른 프로젝트에서 1회 이상 호출

**Non-goals**
- rubric.yml 자체의 자동 개선 (meta-loop은 v3)
- 여러 script 변형 병렬 탐색 (tournament는 v3)
- 정체 감지 / 재시작 로직 (가정 3 검증 후 판단)
- 실시간 루프 제어 UI (대시보드는 read-only)

## 4. User Stories

- **AS** 오너(yoyo), **I WANT** program.md와 rubric.yml만 작성하고 `python src/loop.py labs/{experiment}` 한 줄로 루프를 돌릴 수 있다, **SO THAT** 루프 내부에 개입하지 않고도 산출물이 자동으로 개선된다.
- **AS** 오너(yoyo), **I WANT** 루프가 iteration마다 rubric 점수를 기록하고 best를 자동 갱신한다, **SO THAT** "충분히 좋은가"를 내 감이 아니라 점수로 판단할 수 있다.
- **AS** 오너(yoyo), **I WANT** 실패 항목이 다음 iteration의 script.md 수정 피드백으로 자동 주입된다, **SO THAT** 내가 수동으로 피드백을 쓰지 않아도 스크립트가 스스로 개선된다.
- **AS** 오너(yoyo), **I WANT** Vercel 대시보드에서 실험별 점수 추이 / best 승격 이력 / 현재 script diff를 볼 수 있다, **SO THAT** 루프를 안 보고도 상태를 파악할 수 있다.
- **AS** 오너(yoyo), **I WANT** best 점수가 임계값을 넘으면 `promote.py` 한 줄로 plugin 스킬로 승격할 수 있다, **SO THAT** 검증된 스크립트를 다른 프로젝트(rubato, rofan-world 등)에서 재사용할 수 있다.
- **AS** 오너(jojo), **I WANT** 동일한 엔진에 다른 실험(design, implement 등)을 program.md + rubric.yml 교체만으로 붙일 수 있다, **SO THAT** 실험마다 엔진 코드를 고치지 않아도 된다.

## 5. Functional Requirements

| ID | 요구사항 | 우선순위 | 수용 기준 |
|----|----------|----------|----------|
| FR-01 | 루프 오케스트레이터 (src/loop.py): `python src/loop.py labs/{experiment}` 한 줄로 실험 디렉토리를 받아 end-to-end 루프 실행 | Must | program.md + rubric.yml + script.md + input/ 로드 → iteration 루프 진입 → 종료 시 best/ 에 최종 산출물 + script 저장 |
| FR-02 | 산출물 생성: 현재 script.md를 subprocess.run으로 Claude에 전달하고 input/ 기반 산출물 1개 생성 | Must | 각 iteration마다 임시 산출물 파일 생성 / 외부 의존성은 subprocess.run + Claude CLI만 사용 |
| FR-03 | LLM Judge (src/judge.py): rubric.yml의 항목별 점수화 + 총점 계산 + 실패 항목 리스트 반환 | Must | 입력: 산출물 파일 + rubric.yml → 출력: `{total_score, per_item_scores, failed_items[]}` JSON |
| FR-04 | best 갱신 로직: 총점 > 현재 best면 labs/{experiment}/best/ 에 script + 산출물 쌍 저장, 아니면 discard | Must | best/ 에는 항상 최고점 iteration의 script.md + 산출물 + score.json 보관 |
| FR-05 | Self-improvement 피드백 주입: judge가 반환한 failed_items를 다음 iteration의 script.md 수정 지시로 자동 주입 | Must | 실패 항목 → script.md 개선 프롬프트 → Claude 호출 → 수정된 script.md 로 다음 iteration 진입 |
| FR-06 | 종료 조건: `총점 ≥ rubric.threshold` OR `iteration ≥ rubric.max_iteration` 중 하나라도 만족하면 루프 자동 종료 | Must | 종료 시 stdout에 최종 best 점수 + 총 iteration 수 + 사유 출력 |
| FR-07 | 범용 엔진 구조: loop.py / judge.py / db.py 코드가 실험 종류(cps/prd/design/...)에 의존하는 분기를 포함하지 않음 | Must | grep으로 "cps" "prd" "design" 등 실험 이름 검색 시 엔진 코드에 매치 0건 |
| FR-08 | Supabase 로그 (src/db.py): 각 iteration마다 `{experiment, iteration, total_score, per_item_scores, kept, script_diff, timestamp}` 기록 | Must | Supabase project aqwhjtlpzpcizatvchfb 의 iterations 테이블에 insert / 루프 종료 후 dashboard에서 조회 가능 |
| FR-09 | 대시보드 실험 상세 뷰: /experiments/{name} 페이지에서 iteration별 점수 추이 라인 차트 + best 승격 이력 + 최종 script diff 표시 | Must | Vercel 대시보드 https://moomoo-ax.vercel.app 에서 cps-writing 실험 상세 페이지 정상 렌더 |
| FR-10 | Promotion 파이프라인 (src/promote.py): `python src/promote.py labs/{experiment}` 실행 시 best 점수가 임계값 초과 검증 → 오너 승인 프롬프트 → plugin/.claude-plugin/skills/{experiment}/ 로 script + 메타데이터 복사 | Must | 임계값 미달 시 거부, 초과 시 y/n 프롬프트, y 입력 시 plugin 디렉토리에 복사 완료 및 stdout 경로 출력 |
| FR-11 | labs/cps-writing 실험 1개로 end-to-end 검증: program.md + rubric.yml + 초기 script.md 작성 후 루프 10 iteration 이상 실행 + best 점수 초기 대비 ≥ 20% 상승 확인 + 대시보드 상세 뷰 렌더 확인 + plugin 승격 1회 성공 | Must | labs/cps-writing/best/score.json 의 total_score가 초기 iteration 대비 ≥ 20% 상승 / plugin/.claude-plugin/skills/cps-writing/ 디렉토리 존재 |
| FR-12 | 루프 엔진은 실험별 입력을 program.md + rubric.yml + input/ + 초기 script.md 4가지로만 받음 (추가 CLI 플래그 없음) | Must | loop.py는 positional argument 1개 (실험 디렉토리 경로)만 받음 |

## 6. Technical Constraints

**스택**
- **언어**: Python 3 (엔진), Next.js (대시보드)
- **Claude 호출**: subprocess.run으로 Claude CLI 호출 (SDK 의존성 회피)
- **DB**: Supabase (project: moomoo-ax, id: aqwhjtlpzpcizatvchfb, region: ap-northeast-2)
- **대시보드**: Vercel + Next.js, root: dashboard/, URL: https://moomoo-ax.vercel.app
- **저장소**: https://github.com/lazyyoyo/moomoo-ax

**디렉토리 규약**
```
moomoo-ax/
├── src/
│   ├── loop.py      # 범용 오케스트레이터
│   ├── judge.py     # rubric → LLM Judge → 점수
│   ├── db.py        # Supabase 로그 래퍼
│   └── promote.py   # labs → plugin 승격
├── labs/{experiment}/
│   ├── program.md   # 오너 규칙 (불변)
│   ├── script.md    # AI가 개선하는 스크립트
│   ├── rubric.yml   # 평가 기준 (루프 안 불변)
│   ├── input/       # 입력 파일
│   ├── best/        # 최적 script + 산출물 + score.json
│   └── logs/        # iteration 로그
├── plugin/.claude-plugin/skills/{experiment}/   # 승격 대상
└── dashboard/       # Vercel Next.js
```

**API 의존성**
- Claude CLI (subprocess.run 기반) — 외부 SDK 금지
- Supabase REST API (db.py 래퍼 경유)
- 키/토큰은 환경 변수로만 (하드코딩 금지)

**불변 제약**
- rubric.yml은 루프 안에서 불변 (변경은 오너가 버전 단위로만)
- 루프 엔진은 실험 종류에 의존하는 분기 금지
- 실험별 차이는 program.md + rubric.yml로만 표현

## 7. UI/UX Direction

**핵심 플로우 (v1)**

1. 오너가 `labs/{experiment}/` 에 `program.md`(규칙) + `rubric.yml`(평가 항목 + 임계값 + max iteration) + `input/`(입력) + 초기 `script.md` 작성
2. `python src/loop.py labs/{experiment}` 실행 → 루프 시작 (오너는 이후 개입 안 함)
3. 루프 자동 진행:
   - script.md로 산출물 생성 (subprocess.run → Claude)
   - judge.py가 rubric 항목별 점수 매김 → 총점 + 실패 항목 반환
   - 총점 > best → `best/` 갱신 (script + 산출물 + score.json) / 아니면 discard
   - iteration 로그 Supabase 저장
   - 실패 항목을 script.md 수정 피드백으로 주입 → 다음 iteration 진입
4. 종료 조건 도달 (점수 ≥ 임계값 OR max iteration) → 루프 자동 종료, stdout 요약 출력
5. 오너가 https://moomoo-ax.vercel.app/experiments/{name} 열람 → iteration별 점수 추이 / best 승격 이력 / 최종 script diff 확인
6. best 점수가 promotion 임계값 초과 시 `python src/promote.py labs/{experiment}` → 승인 프롬프트 → `plugin/.claude-plugin/skills/{experiment}/` 로 복사 → 다른 프로젝트에서 스킬로 호출 가능

**대시보드 뷰**
- 실험 상세 뷰 (read-only):
  - 상단: 실험 이름 / 현재 best 총점 / 총 iteration 수 / 종료 사유
  - 중단: iteration별 총점 라인 차트 (x: iteration, y: total_score, best 갱신 지점 마커)
  - 하단: best 승격 이력 테이블 + 최종 script diff (초기 대비)

## 8. Out of Scope

- **평가 기준 자동 개선**: rubric.yml은 루프 안에서 불변. 변경은 오너가 버전 단위(meta-loop)로만. → v3
- **병렬 변형 탐색**: 한 iteration에 한 script만. tournament / beam search 없음. → v3
- **자동 승격**: promotion은 점수 임계값 + 오너 수동 승인 2단계. 완전 자동화 없음. → v2
- **단계별 특수 로직**: define / design / implement 단계별로 엔진 코드가 달라지지 않음. 모든 차이는 program.md + rubric.yml로 표현.
- **실시간 개입 UI**: 대시보드는 read-only 관측용. 루프 중단 / 파라미터 조정은 CLI로만.
- **다중 실험 동시 실행**: v1은 직렬 1개 실험. 병렬 실행은 v2 이후.
- **로컬 최적해 탈출 메커니즘**: 단조 개선 가정(가정 3)에 의존. 정체 감지 시 재시작 로직 없음.
- **단계별 독립 실행 모드**: define 5단계 중 1단계만 실행하는 모드는 v2.
- **대시보드 실험 비교 뷰**: 여러 실험 가로 비교는 v2.

## 9. Open Questions

1. **LLM Judge 일관성 (가정 2)**: 같은 산출물에 대해 judge.py가 반환하는 점수의 편차가 허용 범위 내인가? 검증 방법은? (동일 산출물 5회 judge 호출 후 분산 확인)
2. **단조 개선 가정 (가정 3)**: self-improvement 피드백 주입만으로 실제로 점수가 단조 증가하는가? cps-writing 실험에서 10 iteration 내 ≥ 20% 상승이 달성되지 않으면 로컬 최적해 탈출 메커니즘 도입 시점은?
3. **rubric 임계값 설정 기준**: 각 실험의 점수 임계값(종료 조건)과 승격 임계값을 오너가 어떻게 정할 것인가? 초기값 → 조정 사이클은?
4. **script.md 수정 피드백 포맷**: failed_items를 어떤 프롬프트 구조로 주입해야 Claude가 script.md를 "의도대로" 개선하는가? 프롬프트 템플릿 자체가 루프 엔진에 하드코딩되면 범용성 제약 위반 아닌가?
5. **plugin 승격 후 재사용 인터페이스**: 승격된 스킬을 다른 프로젝트(rubato 등)에서 호출할 때의 API/CLI 계약은? (.claude-plugin/ 표준 형식 준수 범위)
6. **Supabase 스키마 버전 관리**: iterations 테이블 스키마 변경 시 기존 로그와의 호환성 유지 전략은?
7. **rubric.yml DSL 스펙**: 항목 정의 / 가중치 / 임계값 / max_iteration 필드의 정확한 YAML 스키마는 어디에 문서화하는가?
8. **5단계 define 파이프라인과의 관계**: 현재 구현 완료된 define 5단계(seed→jtbd→problem-frame→scope→prd) 스크립트들을 v1 루프 엔진으로 감싸는 첫 대상은 cps-writing 1개만인가, 아니면 각각을 개별 실험으로 병렬 이관하는가?