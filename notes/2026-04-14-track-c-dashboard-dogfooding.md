# 2026-04-14 — Track C dashboard dogfooding

## 목표

- `dashboard/` subtree 에서 `team-ax/ax-implement` skill 을 직접 사용해
  Codex executor / reviewer 루프가 실제 개선 작업 1건을 처리하는지 확인
- 범위는 `dashboard/plan.md` 의 `T-001` 1건으로 제한

## 실행 방식

- Claude 세션에서 `dashboard/` 를 cwd 로 두고 `/team-ax:ax-implement` 직접 호출
- prompt 에 `[TARGET_SUBDIR] dashboard [/TARGET_SUBDIR]` 블록을 포함해 subtree mode 로 실행
- direct skill run 이므로 `product_runs` 증거는 남기지 않고 `.harness/codex/...` 증거를 기준으로 판단

## 결과

- `T-001` executor: **idempotent ok**
  - `src/app/(dashboard)/projects/page.tsx` 는 이미 stage/status/command 표시가 구현된 상태
  - `changed_files=[]`
- `T-001` reviewer: **REQUEST_CHANGES**
  - `product_runs` select 의 `error` 를 무시해 empty state 와 query failure 가 구분되지 않는
    silent failure 지적
- `T-FIX-T-001-1` executor: **ok**
  - `projects/page.tsx` 에 query error summary / error banner / card별 error fallback 추가
- `T-FIX-T-001-1` reviewer: **APPROVE**
- 최종적으로 `dashboard/plan.md` 에서 `T-001`, `T-FIX-T-001-1` 모두 `[x]`

## 부수 수확

- 초기 재실행에서 skill runtime blocker 2건 확인
  - macOS bash 3.2 + `set -u` 에서 empty array expansion failure
  - plugin cache / marketplace 설치 시 `scripts/codex/run_worker.sh` 경로 불일치
- 이후 plugin runtime 을 self-contained bundle 로 수정하고 version `0.1.3` 으로 재배포
- 수정 후 direct skill run 이 reviewer까지 정상 완주함

## 검증 / 한계

- reviewer 결과 파일:
  - `dashboard/.harness/codex/T-001/reviewer/logs/result.json`
  - `dashboard/.harness/codex/T-FIX-T-001-1/reviewer/logs/result.json`
- changed file 기준 `eslint` / `tsc --noEmit` 확인
- `stage-final-review` 와 전체 `run_checks.sh` 는 이번 T-001 범위 밖으로 두고 생략
- dashboard 전체 lint baseline issue 는 별도 존재

## 결론

Track C 의 최소 목표였던 **`dashboard/` 대상 첫 dogfooding 1건**은 달성.
다만 direct skill run 이었기 때문에 `product_runs` 로 실행 증거를 남기는 경로는
v0.5 에서 `ax_product_run.py` hardening 과 함께 다시 맞출 필요가 있다.
