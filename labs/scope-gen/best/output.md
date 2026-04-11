## SLC Checklist
- **Simple**: 루프 엔진(loop.py) + judge.py + db.py + 대시보드 뷰 1개 — 혼자서 2주 스프린트 범위. labs/cps-writing 실험 1개로 검증.
- **Lovable**: 오너가 `program.md + rubric.yml`만 정의하고 루프를 돌리면, 반복마다 점수가 오르면서 best가 자동 갱신되고 대시보드에서 진행 상황이 보임 → "내가 안 봐도 돌아간다"는 해방감.
- **Complete**: 생성 → 평가 → 피드백 → keep/discard → 종료 조건 → 로그 → 대시보드 → promotion까지 한 사이클이 끊김 없이 완결. 반쪽 X.

## v1 Scope

| 기능 | S | L | C | 버전 |
|------|---|---|---|------|
| 루프 오케스트레이터 (loop.py): script.md로 산출물 생성 → judge → keep/discard → 다음 iteration | ✅ | ✅ | ✅ | v1 |
| LLM Judge (judge.py): rubric.yml 항목별 점수화 + 총점 + 실패 항목 리스트 반환 | ✅ | ✅ | ✅ | v1 |
| 실패 항목 → script.md 수정 피드백 자동 주입 (self-improvement 사이클) | ✅ | ✅ | ✅ | v1 |
| best/ 디렉토리 갱신: 최고점 iteration의 script + 산출물 쌍 저장 | ✅ | ✅ | ✅ | v1 |
| 종료 조건: 점수 ≥ 임계값 OR max iteration 도달 | ✅ | ✅ | ✅ | v1 |
| 범용 엔진 구조: program.md + rubric.yml만 실험별 입력 (엔진은 불변) | ✅ | ✅ | ✅ | v1 |
| Supabase 로그: iteration별 점수 / diff / keep 여부 / timestamp | ✅ | ✅ | ✅ | v1 |
| 대시보드 실험 상세 뷰: iteration별 점수 추이 + best 승격 이력 + 현재 script diff | ✅ | ✅ | ✅ | v1 |
| labs → plugin 승격 파이프라인: 임계값 초과 시 plugin/.claude-plugin/ 으로 script 복사 + 수동 승인 게이트 | ✅ | ✅ | ✅ | v1 |
| labs/cps-writing 실험 1개로 end-to-end 검증 | ✅ | ✅ | ✅ | v1 |
| 단계별 독립 실행 모드 (define 5단계 중 1단계만 실행) | ✅ | ❌ | ❌ | v2 |
| rubric meta-loop (평가 기준 자체 진화) | ❌ | ✅ | ❌ | v3 |
| tournament 방식 병렬 script 변형 경쟁 | ❌ | ❌ | ❌ | v3 |
| 대시보드 실험 비교 뷰 (여러 실험 가로 비교) | ✅ | ❌ | ❌ | v2 |
| 자동 promotion (수동 게이트 없이 임계값만으로 승격) | ✅ | ❌ | ❌ | v2 |

## Out of Scope
- **평가 기준 자동 개선**: rubric.yml은 루프 안에서 불변. 변경은 오너가 버전 단위로만.
- **병렬 변형 탐색**: 한 iteration에 한 script만. tournament / beam search 없음.
- **자동 승격**: promotion은 점수 임계값 + 오너 수동 승인 2단계. 완전 자동화 X.
- **단계별 특수 로직**: define / design / implement 단계별로 엔진 코드가 달라지지 않음. 모든 차이는 program.md + rubric.yml로 표현.
- **실시간 개입 UI**: 대시보드는 read-only 관측용. 루프 중단 / 파라미터 조정은 CLI로만.
- **다중 실험 동시 실행**: v1은 직렬 1개 실험. 병렬 실행은 v2 이후.
- **로컬 최적해 탈출 메커니즘**: 단조 개선 가정에 의존. 정체 감지 시 재시작 로직 없음 (핵심 가정 3 검증 후 판단).

## 핵심 사용자 플로우 (v1)

1. 오너가 `labs/{experiment}/` 에 `program.md` (규칙) + `rubric.yml` (평가 항목) + `input/` (입력) + 초기 `script.md` 작성
2. `python src/loop.py labs/{experiment}` 실행 → 루프 시작
3. 루프가 자동 진행: script.md로 산출물 생성 → judge.py가 rubric 항목별 점수 매김 → 총점 > best면 `best/` 갱신 + iteration 로그 Supabase 저장 → 실패 항목을 script.md 수정 피드백으로 주입 → 다음 iteration
4. 종료 조건 도달 (점수 ≥ 임계값 OR max iteration) → 루프 자동 종료
5. 오너가 https://moomoo-ax.vercel.app 에서 실험 상세 뷰 열람 → iteration별 점수 추이 / best 승격 이력 / 최종 script diff 확인
6. best 점수가 promotion 임계값 초과하면 `python src/promote.py labs/{experiment}` 실행 → 오너 승인 프롬프트 → `plugin/.claude-plugin/` 으로 script 복사 → 다른 프로젝트에서 재사용 가능