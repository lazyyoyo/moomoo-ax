# HANDOFF — v0.4 마감, v0.5 진입

**작성 시점**: 2026-04-14
**기준 버전**: `v0.4` close-out 완료
**다음 세션 작업**: v0.5 착수. 우선순위는 `(1) ax-implement 실전 사용성`, `(2) ax-define 기본 문서 Codex 작성`.

## 한 줄 요약

v0.4 에서 `product_runs` 관찰 인프라를 붙였고, `team-ax/ax-implement` 는 **Claude conductor + Codex executor/reviewer** 구조로 fixture green 을 달성했다. 이어 `dashboard/` subtree 첫 dogfooding 1건을 direct skill run 으로 처리해 `T-001 -> reviewer REQUEST_CHANGES -> fix task -> APPROVE` 루프까지 실증했다.

## 먼저 읽을 문서

1. **이 HANDOFF**
2. **`versions/v0.4/report.md`** — v0.4 전체 결과 / 이월 / 검증
3. **`PROJECT_BRIEF.md`** — 로드맵 업데이트됨 (`v0.5` 우선순위 반영)
4. **`BACKLOG.md`** — ready(v0.5) 우선순위 반영
5. **`versions/v0.4/plan.md`** — close-out 체크 상태
6. **`notes/2026-04-14-track-c-dashboard-dogfooding.md`** — 첫 dogfooding 상세
7. **`notes/2026-04-14-codex-worker-contract.md`** — executor/reviewer 결과 계약

## v0.4 에서 닫힌 것

### Track A — 관찰 인프라

- `src/db.py`
  - `start_product_run(...)`
  - `finish_product_run(...)`
- `scripts/ax_product_run.py`
  - fixture run 시작/종료 row 기록
  - `session_id`, `cost_usd`, `num_turns`, `tool_call_stats` 저장
- `dashboard/src/app/(dashboard)/live/page.tsx`
- `dashboard/src/app/(dashboard)/projects/page.tsx`
- `dashboard/src/lib/supabase.ts`
- migration:
  - `versions/v0.4/product-runs-migration.sql`

### Track B — Codex executor+reviewer pilot

- `plugin/skills/ax-implement/SKILL.md`
  - Claude 직접 구현/리뷰 경로 제거
  - Codex executor / reviewer wrapper 호출 구조로 전환
- 실행 자산
  - `plugin/skills/ax-implement/scripts/run_codex_worker.sh`
  - `plugin/skills/ax-implement/scripts/render_codex_task.py`
  - `plugin/skills/ax-implement/scripts/run_task_checks.sh`
  - `plugin/skills/ax-implement/scripts/select_codex_model.py`
  - `plugin/skills/ax-implement/templates/CODEX_*`
  - `plugin/scripts/codex/run_worker.sh`
  - `plugin/scripts/codex/normalize_codex_result.py`
- fixture green
  - rerun `6593deebdf82`
  - model-routing rerun `e0f0a5be8b5a`

### Track C — 첫 dogfooding

- 대상: `dashboard/`
- 태스크: `dashboard/plan.md` 의 `T-001`
- 결과:
  - `T-001` executor: 이미 구현됨 → `changed_files=[]`
  - `T-001` reviewer: silent failure 지적 → `REQUEST_CHANGES`
  - `T-FIX-T-001-1`: `projects/page.tsx` 에 query error handling 추가 → `APPROVE`
- 증거:
  - `dashboard/.harness/codex/T-001/...`
  - `dashboard/.harness/codex/T-FIX-T-001-1/...`

## 이번 세션에서 고친 runtime 버그

- plugin cache / marketplace 설치 시 Codex runner 경로 불일치
- macOS bash 3.2 + `set -u` 에서 empty array expansion 실패

이 둘은 plugin bundle 내부 self-contained runner 로 정리했고, plugin version 은 현재 **`0.1.3`** 이다.

## 아직 안 닫힌 것

이건 v0.4 blocker 가 아니라 **v0.5 이월**로 본다.

- `scripts/ax_product_run.py` finish idempotency hardening
- failed run 1회에 대한 `product_runs.status=failed` 검증
- direct skill run 이 아닌 driver 경로에서도 dogfooding evidence 를 안정적으로 남기기
- `stage-final-review` / 전체 `run_checks.sh` 를 실전 범위와 어떻게 결합할지 정책 정리

## 다음 세션 최우선

### 1. ax-implement 실전 사용성

지금 `ax-implement` 는 fixture / prewritten `plan.md` / 소형 subtree dogfooding 에서는 된다. 다음은 **실전 repo 에서 바로 쓰는 수준**까지 올려야 한다.

필수:
- plan 없는 프로젝트에서도 시작 가능해야 함
- planner/plan bootstrap 이 implement stage 안으로 들어와야 함
- dirty working tree baseline 처리 규칙을 실전 프로젝트용으로 더 명확히 해야 함
- direct Claude skill run 과 driver run 둘 다 같은 결과 계약을 유지해야 함

### 2. ax-define 기본 문서 Codex 작성

`define` 에서 오너가 문서 초안을 직접 쓰는 병목을 줄이는 게 두 번째 우선순위다.

목표:
- Claude 는 의도 수렴 / 범위 결정 / 승인 포인트만 담당
- Codex worker 가 기본 문서 초안 작성
- 최소 산출물:
  - spec 문서
  - `ARCHITECTURE.md`
  - `DESIGN_SYSTEM.md`
  - implement 가 바로 읽을 `plan.md`

## 원칙

- latency 논의는 다시 열지 말 것. 계속 **known issue** 로만 취급
- `team-product` 대체의 핵심은 Claude 성능 향상이 아니라 **Claude conductor + Codex hands** 구조 고정
- 실전 적용을 막는 병목부터 먼저 친다. 예쁜 일반화는 뒤
- 트랙은 여전히 **선계획 후실행**

## 검증 기준

- repo 테스트: `122 passed`
- dogfooding changed file lint/typecheck 확인
- 현재 워킹트리에서 `dashboard/` 변경 2개는 Track C 산출물:
  - `dashboard/src/app/(dashboard)/projects/page.tsx`
  - `dashboard/plan.md`

## 이번 버전 한 줄 수확

> v0.4 는 "Codex worker 를 붙일 수 있는가" 를 넘어서, "실제 dogfooding 1건에서 REQUEST_CHANGES -> fix -> APPROVE 루프를 돌릴 수 있는가" 까지 확인한 버전이다.
