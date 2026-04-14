# v0.4 report

## 한 줄 결론

> `product_runs` 관찰 인프라를 붙였고, Claude conductor + Codex executor/reviewer 구조를 fixture 와 `dashboard/` dogfooding 에서 실증했다.

## 목표 대비 결과

### Track A — 관찰 인프라

- `src/db.py` 에 `start_product_run` / `finish_product_run` 추가
- `scripts/ax_product_run.py` 가 fixture run 을 `product_runs` 로 기록
- `dashboard` 의 `live/projects` 화면이 `product_runs` row 를 읽어 표시
- migration: `versions/v0.4/product-runs-migration.sql`

실측:
- fixture rerun `6593deebdf82`: green
- model-routing rerun `e0f0a5be8b5a`: green

남긴 이월:
- finish idempotency hardening
- failed run 1회에 대한 `status=failed` 검증

### Track B — Codex executor+reviewer pilot

- executor / reviewer 결과 계약 고정
- one-shot Codex worker wrapper / normalize / model routing 도입
- `team-ax/ax-implement` 가 Claude 직접 구현이 아니라 Codex worker 호출 구조로 전환
- fixture 에서 REQUEST_CHANGES → fix task → APPROVE 루프 실증

known issue:
- latency 는 여전히 길다 (`20m 48s`, `22m 24s`)
- v0.4 에서는 blocker 가 아니라 관찰 지표로 취급

### Track C — moomoo-ax dogfooding

- `--target-subdir` 가드 추가
- `dashboard/` subtree 대상 첫 dogfooding 1건 수행
- `dashboard/plan.md` 의 `T-001` 과 `T-FIX-T-001-1` 모두 APPROVE 로 닫힘
- 상세: `notes/2026-04-14-track-c-dashboard-dogfooding.md`

실제 수정:
- `dashboard/src/app/(dashboard)/projects/page.tsx`
  - latest run 표시 유지
  - `product_runs` query failure 를 empty state 와 구분해 노출

추가 수확:
- plugin runtime blocker 2건 수정
  - bash 3.2 empty array handling
  - plugin bundle 내부 Codex runner/self-contained normalize 경로
- plugin version `0.1.3` 배포

한계:
- direct skill run 으로 검증했기 때문에 이번 dogfooding 자체는 `product_runs` row 를 남기지 않음
- 실행 증거는 `dashboard/.harness/codex/...` result.json 기준

## 산출물

- `versions/v0.4/plan.md`
- `versions/v0.4/product-runs-migration.sql`
- `notes/2026-04-14-codex-worker-contract.md`
- `notes/2026-04-14-track-b-pilot-partial.md`
- `notes/2026-04-14-track-b-pilot-rerun.md`
- `notes/2026-04-14-track-b-model-routing-rerun.md`
- `notes/2026-04-14-track-b-latency-reduction-plan.md`
- `notes/2026-04-14-track-c-dashboard-dogfooding.md`

## 검증

- repo 테스트: `122 passed`
- dashboard changed file lint: `npx eslint "src/app/(dashboard)/projects/page.tsx"`
- dashboard typecheck: `npx tsc --noEmit`

## v0.5 로 넘길 것

우선순위는 다음 둘이다.

1. `ax-implement` 를 실전에서 바로 쓰기 위해 planner/plan bootstrap 까지 포함해 hardening
2. `ax-define` 에서 기본 문서 초안 작성 (`spec`, `ARCHITECTURE`, `DESIGN_SYSTEM`, `plan`) 을 Codex worker 가 맡게 전환

후순위:
- `ax-qa`
- levelup smoke
- driver 자동 판정 완성형
