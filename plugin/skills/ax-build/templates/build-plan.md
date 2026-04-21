# build-plan — {제품 이름} {버전}

> 사람이 읽는 계획서. 기계 SSOT는 `.ax/plan.json` (planner 산출 — 워커 스폰/폴링/커밋에 사용).
> 본 문서는 계획 의도 + 분할 근거 + 오너 확인용 요약을 담는다.

## 공통 기반 (kind: common — 최우선 순차)

<!-- 여러 태스크가 공유하는 파일/레이어. 없으면 "없음" 표기. common 태스크는 다른 모든 task의 blockedBy에 들어간다. -->

- [ ] DB: {테이블/컬럼 변경 내용} — 파일: `db/migrations/...`
- [ ] API: {공통 엔드포인트} — 파일: `src/api/...`
- [ ] 타입: {공통 타입/인터페이스} — 파일: `src/types/...`
- [ ] DS: {신규 컴포넌트 — ax-design 호출} — 파일: `src/components/ui/...`

## 태스크 (kind: task — 파일 whitelist 기반 병렬)

각 태스크는 **파일 집합**이 겹치지 않아야 같은 라운드에 병렬 스폰된다. 겹치면 `blockedBy`로 순차화.

### 태스크 T1: {태스크명}

- 디자인: {필요 / 불필요 / DS 조합}
- **파일 whitelist**: `src/admin/timeseries/**`, `src/api/timeseries/route.ts`
- **blockedBy**: (있으면 나열, 없으면 비움)
- 지시:
  - {구체 instruction 1} → 검증: {검증 방법}
  - {구체 instruction 2} → 검증: {검증 방법}

### 태스크 T2: {태스크명}

- 디자인: {필요 / 불필요}
- **파일 whitelist**: `src/admin/users/**`, `src/api/users/route.ts`
- **blockedBy**: (예: `[T0-common]`)
- 지시:
  - {구체 instruction} → 검증: {검증 방법}

## 병렬 라운드 설계

<!-- plan.json의 blockedBy 그래프에서 도출된 라운드. 같은 라운드 = 동시에 spawn되는 워커 집합. -->

| 라운드 | 태스크 | 병렬도 | 비고 |
|---|---|---|---|
| R0 | T0-common (공통 기반) | 1 | 단독 순차 |
| R1 | T1, T2 | 2 | common 완료 후 병렬 |
| R2 | T3 | 1 | T1 완료 전제 |

- 라운드별 워커 수 최대 5 (초과 시 병렬 효율 저하)
- common은 항상 R0 단독 처리

## 리스크 / 미결 사항

<!-- 파일 겹침 애매한 태스크, 전역 리팩토링 등 -->

- {리스크 1}
- {미결 1}

## 참조

- `.ax/plan.json` — 기계 SSOT (이 문서와 동기 유지)
- `plugin/skills/ax-build/SKILL.md` — ax-build 흐름
- `plugin/skills/ax-execute/SKILL.md` — 워커 프로토콜
- `plugin/agents/planner.md` — 분할 규칙
