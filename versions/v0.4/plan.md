# v0.4 — 관찰 먼저, Claude conductor + Codex workers 첫 편입

## 한 줄 목표

> **`product_runs` 를 end-to-end 로 기록/표시하고, Claude conductor 아래에서 Codex executor + reviewer 루프를 fixture 에 먼저 붙인 뒤, moomoo-ax 내부 1개 subdir 에 dogfooding 한다.**

## v0.4 의 의미

v0.3 은 `team-ax/ax-implement` 1 stage 가 **돌아간다** 는 사실을 격리 fixture 에서 증명했다.
v0.4 는 그 성공을 세 단계로 확장한다.

1. **보이게 만들기** — product loop 실행을 `product_runs` 로 수집하고 대시보드에서 본다
2. **노동 주체 바꾸기** — Claude 는 conductor, Codex 는 executor / reviewer worker 로 붙인다
3. **실제 대상에 써보기** — moomoo-ax 내부 작은 범위에 dogfooding 한다

공식적인 **team-product 대체 선언은 여전히 v0.5** 에 둔다.
v0.4 는 "작은 실전에서 대체 가능" 을 증명하는 버전이다.

## 범위 원칙

- **오너 선호: 선계획 후실행** — 구현 전 각 트랙의 범위 / 비범위 / 성공 기준을 먼저 문서로 고정
- **트랙은 1개씩 닫기** — A 완료 전 B 시작 금지, B 완료 전 C 시작 금지
- **v0.3 baseline 보존** — `v0.3.0` 이 통과한 Claude-only 경로는 비교 기준으로 유지
- **Claude 는 conductor** — stage 흐름 제어 / task 선택 / worker 호출 / 결과 판정 / fix task 삽입만 담당
- **Codex 는 worker** — implement stage 의 executor / reviewer 역할만 맡음
- **tmux 는 필수 아님** — 기본 판정은 항상 `events.jsonl` / `meta.json` / `last-message.txt` 파일 기준
- **본선 전체 재설계 금지** — runtime-neutral harness 재작성, multi-stage 확대, autopilot 일반화는 v0.5+

## 현재 baseline

- `v0.3.0` 태그: `team-ax/ax-implement` 가 격리 fixture 에서 end-to-end PASS
- `scripts/ax_product_run.py` 는 fixture copy → `claude.call()` → `.harness/runs/<run_id>.ndjson` 저장까지 가능
- `dashboard/src/lib/supabase.ts` 와 `dashboard/src/app/(dashboard)/live|projects` 는 이미 `product_runs` 타입/조회 코드를 가짐
- `versions/v0.1/supabase-schema.sql` 에 `product_runs` 테이블 정의는 존재하지만, 현재 드라이버가 write 하지 않음
- `scripts/poc/` 와 `notes/2026-04-13-codex-*.md` 에 Codex one-shot worker / tmux host PoC 자산이 있음

## 완료 기준

### A. 관찰 인프라

- [ ] `scripts/ax_product_run.py` 가 **run 시작/종료를 parent-side 로 `product_runs` 에 기록**
- [ ] 최소 기록 필드: `id`, `ax_version`, `user_name`, `project`, `command`, `stage`, `status`, `started_at`, `finished_at`, `duration_sec`, `cost_usd`, `num_turns`, `fixture_id`, `session_id`
- [ ] `dashboard/src/app/(dashboard)/live/page.tsx` 와 `projects/page.tsx` 에서 실제 row 가 보임
- [ ] intervention 과의 시간 범위 join 또는 후속 계산 경로가 정리됨

### B. Codex executor+reviewer pilot

- [ ] `ax-implement` 의 기존 `task 선택 → executor 구현 → reviewer 판정 → fix task` 루프는 유지
- [ ] executor / reviewer 는 **Codex one-shot worker** 로 호출
- [ ] Claude 는 결과 파일을 읽고 `[x]` / fix task / 중단 여부만 판정
- [ ] `static-nextjs-min` fixture 1회 green
- [ ] worker 실패가 `infra_error`, `failed`, `REQUEST_CHANGES` 로 구분돼 Claude 쪽 분기 기준이 명확함

### C. dogfooding

- [x] `--target-subdir` 또는 동등한 경로 가드로 child write 범위를 제한
- [x] moomoo-ax 내부 1개 소형 태스크에서 Codex executor+reviewer 루프 1회 수행
- [x] 지정 subdir 밖 파일 오염이 없음을 확인

## close-out note

v0.4 는 아래 범위까지 달성한 상태로 close 한다.

- Track A: `product_runs` 관찰 인프라와 dashboard 반영 완료
- Track B: Codex executor/reviewer fixture green 완료
- Track C: `dashboard/` 대상 direct skill dogfooding 1건 완료

남은 open item 은 버전 미완료가 아니라 v0.5 이월로 본다.

- A.3.3 finish idempotency
- A.5 failed run `status=failed` 검증
- C.3.1 direct skill run 외 driver 경로로도 `product_runs` 증거 남기기

## Out of scope (v0.5+)

- `ax-qa` 포팅
- levelup loop smoke
- planner subagent
- 드라이버 자동 판정 완성형
- `ax-autopilot` 상위 오케스트레이터
- runtime-neutral harness 재작성
- Codex 를 init/design/deploy/qa 까지 확대

---

## Track A — 관찰 인프라 🎯 최우선

> **핵심 질문: "product loop 가 실제로 몇 번, 얼마에, 얼마나 오래, 어떤 상태로 돌았는가?" 를 DB 와 대시보드에서 바로 보이게 만들 수 있는가**

### A.1 스키마 정렬

- [x] **A.1.1 `product_runs` 실사용 필드 확정**
  - 기준 파일: `versions/v0.1/supabase-schema.sql`, `dashboard/src/lib/supabase.ts`
  - v0.4 필수 컬럼:
    - `id uuid`
    - `created_at timestamptz`
    - `ax_version text`
    - `user_name text`
    - `project text`
    - `command text`
    - `stage text`
    - `status text` (`running|done|failed|cancelled`)
    - `started_at timestamptz`
    - `finished_at timestamptz`
    - `duration_sec numeric`
    - `cost_usd numeric`
    - `num_turns int`
    - `fixture_id text`
    - `session_id text`
    - `tool_call_stats jsonb`
    - `input_intent text`
    - `output_path text`
- [x] **A.1.2 migration 파일 추가**
  - 기존 `product_runs` 테이블을 drop/recreate 하지 말고 **ALTER 기반** 으로 맞춘다
  - 위치: `versions/v0.4/` 아래 SQL 파일 신규

### A.2 DB write 경로 추가

- [x] **A.2.1 `src/db.py` 에 product run write 함수 추가**
  - `start_product_run(...)`
  - `finish_product_run(...)`
  - 서비스 role 만 사용. 기존 env 이름 `SUPABASE_SERVICE_ROLE_KEY` 유지
- [x] **A.2.2 id 는 드라이버가 먼저 발행**
  - DB generated id 에 의존하지 말고 driver 가 uuid 발행 → insert / update 에 같은 id 사용
  - 그래야 `running` → `done|failed` 갱신이 단순해짐

### A.3 드라이버 parent-side logging

- [x] **A.3.1 `scripts/ax_product_run.py` 시작 row insert**
  - run 시작 직후 `status=running`
  - `project` 는 fixture / target-subdir / cwd 기준으로 추론
  - `command` 는 기본 `/team-ax:ax-implement`
  - `fixture_id` 는 fixture run 일 때만 기록
- [x] **A.3.2 종료 row update**
  - `status=done|failed`
  - `duration_sec`, `cost_usd`, `num_turns` 기록
  - `session_id` 는 ndjson 또는 CLI 결과에서 best-effort 추출
  - `tool_call_stats` 는 최소한 task/review/check 스크립트 호출 수를 JSON 으로 저장
- [ ] **A.3.3 idempotency**
  - 같은 run id 로 finish 가 중복 호출돼도 row 가 깨지지 않게 보수적으로 작성

### A.4 대시보드 최소 보정

- [x] **A.4.1 `dashboard/src/lib/supabase.ts` `ProductRun` 타입 갱신**
- [x] **A.4.2 `dashboard/src/app/(dashboard)/live/page.tsx`**
  - `status=running` row 에 `stage`, `project`, `duration` 정도만 추가
- [x] **A.4.3 `dashboard/src/app/(dashboard)/projects/page.tsx`**
  - 실제 `product_runs` row 기준으로 실행 횟수 / 진행중 여부 표시 확인
- [x] **A.4.4 필요하면 `north-star` 보조 수치 추가**
  - 단, 카드 재설계는 금지. 기존 화면에 작은 배지/행 추가 수준

### A.5 검증

- [x] fixture run 1회로 `product_runs` row 생성/갱신 확인
- [x] 대시보드 live/projects 에 실제 표시 확인
- [ ] 실패 run 1회도 `status=failed` 로 남는지 확인

실측 메모:
- runtime 검증 run 기준 `running → done` 전이 확인
- `/projects` 반영 확인, `/live` 는 종료 후 empty state 로 일치
- `tool_call_stats.task_subagent_counts` 는 `Task` / `Agent` 둘 다 best-effort 로 집계한다. Track B 부터는 Codex worker 경로가 기본이라 빈 값이어도 blocker 아님

### A 성공 기준

- `scripts/ax_product_run.py` 1회 실행으로 `product_runs` 가 `running → done|failed` 로 바뀜
- 대시보드에서 실제 row 조회 가능
- 이 시점부터 dogfooding / Codex pilot 의 비용/시간/실패 상태를 관찰할 수 있음

---

## Track B — Codex executor+reviewer pilot

> **핵심 질문: Claude conductor 가 Codex executor / reviewer worker 2개를 호출하고, 그 결과만으로 기존 fix task 루프를 유지할 수 있는가**

### B.1 계약 고정

- [x] **B.1.1 executor result schema**
  - `status`: `ok | failed | infra_error`
  - `summary`
  - `changed_files[]`
  - `checks_run[]`
- [x] **B.1.2 reviewer result schema**
  - `verdict`: `APPROVE | REQUEST_CHANGES | ERROR`
  - `blocking_issues[]`
  - `non_blocking_issues[]`
  - `summary`
- [x] **B.1.3 normalize 규칙**
  - exit code 만 믿지 않음
  - `events.jsonl` / `meta.json` / `last-message.txt` 를 합쳐 최종 상태 산출
  - 상세 계약: `notes/2026-04-14-codex-worker-contract.md`

### B.2 PoC 자산 승격

- [x] **B.2.1 `scripts/poc/` 자산 중 본선 편입 대상 선정**
  - `run_codex_worker.sh`
  - `summarize_codex_worker.py`
  - 필요 시 `tmux_*` 는 debug-only 로 유지
- [x] **B.2.2 supported wrapper 경로로 승격**
  - `scripts/` 또는 `src/` 아래 정식 위치로 이동/복제
  - `poc` 디렉토리는 실험 로그와 구분

실행 자산:
- `scripts/codex/run_worker.sh`
- `src/codex_worker.py`
- `plugin/skills/ax-implement/scripts/run_codex_worker.sh`
- `plugin/skills/ax-implement/scripts/render_codex_task.py`
- `plugin/skills/ax-implement/templates/CODEX_EXECUTOR_TASK_TEMPLATE.md`
- `plugin/skills/ax-implement/templates/CODEX_REVIEWER_TASK_TEMPLATE.md`

### B.3 conductor 연결

- [x] **B.3.1 `plugin/skills/ax-implement/SKILL.md` 수정**
  - Claude 가 직접 구현/리뷰하는 subagent path 제거
  - 대신 task file 작성 → Codex executor 호출 → 결과 read
  - 이어서 reviewer 입력 생성 → Codex reviewer 호출 → verdict read
- [x] **B.3.2 allowed-tools 정리**
  - raw `codex` 직접 허용보다 wrapper 실행만 허용
  - 경로는 절대경로 기준
- [x] **B.3.3 실패 분기**
  - executor `infra_error` → 즉시 중단 또는 재시도
  - reviewer `REQUEST_CHANGES` → fix task 삽입
  - reviewer `ERROR` → Claude fallback 또는 오너 개입

실행 자산 연결 메모:
- `plugin/skills/ax-implement/SKILL.md` 는 `Task` 도구 없이 Codex executor / reviewer wrapper 호출만 사용
- reviewer 입력은 executor `result.json.changed_files[]` 를 읽어 scope 로 넘긴다
- 수동 검증 기준은 `.harness/codex/<task-id>/*/logs/result.json` 생성과 plan.md 전환 여부

### B.4 fixture pilot

- [x] **B.4.1 `static-nextjs-min` 에서 1회 green**
  - Claude 는 plan/read/edit/conduct 만 수행
  - Codex executor 가 실제 코드 변경
  - Codex reviewer 가 APPROVE / REQUEST_CHANGES 판정
- [x] **B.4.2 최소 1회 실패 분기도 실증**
  - REQUEST_CHANGES 또는 executor failure 중 1개는 의도적으로 관찰해 분기 확인

실측 메모:
- 첫 pilot (`run_id=69ddd1eb0aa4`) 은 **partial evidence**
  - 원 3 task + fix 1개는 모두 APPROVE 까지 도달
  - 그러나 `stage-final-review` 가 `REQUEST_CHANGES` 를 반환하며 `T-004~T-007` 태스크를 추가 생성
  - 약 43분 시점 수동 중단, green close 불가
  - 상세: `notes/2026-04-14-track-b-pilot-partial.md`
- rerun (`run_id=6593deebdf82`) 에서 fixture green 달성
  - reviewer-only retry 없음
  - stage-final recursive loop 없음
  - `product_runs` done 기록
  - 상세: `notes/2026-04-14-track-b-pilot-rerun.md`

### B.5 latency reduction pass

- [x] **B.5.1 fix approve 시 원 태스크 즉시 닫기**
  - `T-FIX-*` approve 후 `T-001-retry` 같은 reviewer-only 재호출 금지
- [x] **B.5.2 checks 를 conductor/script 로 이동**
  - Codex worker 는 구현/리뷰 중심, 결정론적 checks 는 Claude conductor 가 실행
- [x] **B.5.3 dependency / 환경 복구를 preflight 로 격리**
  - worker 가 `npm install` 같은 환경 복구로 새지 않게 제한
- [x] **B.5.4 task prompt 축소**
  - executor/reviewer 입력 범위를 필요한 파일과 핵심 spec 으로 제한
- [x] **B.5.5 stage-final-review blocking 범위 제한**
  - fixture pilot 단계에서 recursive remediation loop 가 크게 확장되지 않도록 가드
- [x] **B.5.6 rerun + latency baseline 확보**
  - 성공 기준: 구조적 green 유지 + `product_runs` 정상 종료 + elapsed/cost/turns 기록
  - 결과:
    - rerun `6593deebdf82`: green, elapsed `20m 48s`
    - model-routing rerun `e0f0a5be8b5a`: green, elapsed `22m 24s`
  - 결론: latency 는 known issue 로 기록한다. v0.4 에서는 dogfooding 진입 차단 기준이 아니라 관찰 지표로 취급한다
- [x] **B.5.7 risk-based 모델 라우팅**
  - 저위험 task 는 `gpt-5.4-mini`, 공용 component/config 는 `gpt-5.3-codex`, `stage-final-review` 는 `gpt-5.4`
  - 선택 근거를 `model-selection.json` 으로 남겨 rerun 시 비교 가능하게 함

구현 메모:
- `plugin/skills/ax-implement/scripts/run_task_checks.sh` 추가
- executor prompt 는 구현 중심, dependency 복구 / broad checks 금지로 축소
- reviewer 는 `checks.json` 을 우선 입력으로 사용
- stage-final-review 는 v0.4 fixture pilot 에서 비재귀 audit 로 제한

### B 성공 기준

- `team-ax/ax-implement` 의 구현/리뷰 노동 주체가 Codex 로 바뀌어도 fixture green
- Claude 는 conductor 로만 남음
- 결과 계약이 고정돼 이후 dogfooding 에 그대로 재사용 가능
- latency / cost / turns 는 `product_runs` 와 run note 에 기록되며, v0.4 에서는 최적화 대상이지 진입 차단 기준은 아님

---

## Track C — moomoo-ax dogfooding

> **핵심 질문: Codex executor+reviewer 루프를 moomoo-ax 내부 작은 범위에 붙여도 repo 오염 없이 실제 개선 작업이 가능한가**

### C.1 경로 가드

- [x] **C.1.1 `scripts/ax_product_run.py` 또는 별도 드라이버에 `--target-subdir` 추가**
- [x] **C.1.2 worker write 범위 제한**
  - child session 이 지정 subdir 밖 파일을 수정 못하게 tool allow 패턴 제한
- [x] **C.1.3 self-edit 금지**
  - `plugin/skills/ax-implement/`, `scripts/ax_product_run.py`, worker adapter 본체는 dogfooding 대상에서 제외

Track C 진입 조건:

- Track A 완료
- Track B 구조적 green 완료
- latency known issue 를 backlog 로 수용

### C.2 첫 대상

- [x] **C.2.1 `dashboard/` 내부 소형 태스크 1개**
  - 예: `product_runs` 카드 보강, 표시 필드 개선, 빈 상태 문구 정리
- [x] **C.2.2 run 전후 git status 비교**
  - target-subdir 밖 변경 없음을 확인

실측:
- direct skill run 으로 `dashboard/plan.md` 의 `T-001` + `T-FIX-T-001-1` 둘 다 APPROVE
- 최종 수정 파일은 `dashboard/src/app/(dashboard)/projects/page.tsx`
- 상세: `notes/2026-04-14-track-c-dashboard-dogfooding.md`

### C.3 기록

- [ ] `product_runs` 로 run 기록 확인
- [ ] 필요 시 interventions / feedback 과 연결
- [x] `notes/` 에 dogfooding 회고 1건 작성

메모:
- runtime 검증은 direct skill run 으로 수행했기 때문에 `product_runs` row 는 남기지 않음
- 증거는 `dashboard/.harness/codex/.../result.json` 기준

### C 성공 기준

- [x] moomoo-ax 내부 소형 태스크 1건을 Codex executor+reviewer 루프로 처리
- [x] subdir 밖 오염 없음
- [x] 이후 같은 방식으로 실제 프로젝트 확장이 가능하다는 자신감 확보

---

## Phase D — 마감

- [x] `versions/v0.4/report.md`
- [x] `HANDOFF.md` 업데이트
- [x] `BACKLOG.md` 정리
- [x] `PROJECT_BRIEF.md` 로드맵 조정 (필요 시)
- [ ] tag / close-out 판단

---

## 작업 순서

```
Track A  관찰 인프라
  A.1 schema alignment
  A.2 db write 함수
  A.3 driver logging
  A.4 dashboard 최소 보정
  A.5 검증
      │
      ▼
Track B  Claude conductor + Codex executor/reviewer
  B.1 result schema 고정
  B.2 PoC 자산 승격
  B.3 SKILL.md / wrapper 연결
  B.4 fixture pilot (partial evidence 확보)
  B.5 latency baseline / known issue 정리
      │
      ▼
Track C  dogfooding
  C.1 target-subdir guard
  C.2 small task 1건
  C.3 회고
      │
      ▼
Phase D  report / handoff / backlog / close-out
```

## 리스크

| # | 리스크 | 영향 | 대응 |
|---|---|---|---|
| R1 | `product_runs` schema 와 dashboard 타입 불일치 | 중 | Track A 에서 타입/컬럼 먼저 고정 |
| R2 | driver 가 `running` row 는 넣었지만 finish update 실패 | 중 | start/finish 함수 분리 + id driver 발행 + 실패 시 stderr 남김 |
| R3 | Codex worker 의 exit code 와 실제 판정 불일치 | 중 | normalize 는 항상 파일 기반 (`meta.json`, `events.jsonl`, `last-message.txt`) |
| R4 | Claude conductor 가 worker 결과를 잘못 해석 | 중 | executor/reviewer schema 를 문서와 코드에서 동시에 고정 |
| R5 | dogfooding 중 본체 오염 | 높 | `--target-subdir` 제한 + self-edit 금지 + 전후 git status 확인 |

## 이번 버전의 한 줄 기준

> **v0.4 는 "Codex 로 바꾸는가?" 를 논쟁하는 버전이 아니라, "Claude 가 지휘하고 Codex 가 일하는 구조를 관찰 가능한 상태로 실제로 붙여보는 버전" 이다.**
