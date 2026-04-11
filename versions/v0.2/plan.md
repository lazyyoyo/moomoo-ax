# v0.2 — R5 fix + 수집 인프라 + ax-implement (C') 패턴 정립

## 목표

> **"levelup loop 가 SKILL.md 를 안전하게 개선하고, 그 개선이 '자연어→script 추출'까지 포함한다는 패턴을 ax-implement 1 stage 로 증명한다."**

v0.1 은 engine 1 cycle (labs/ax-qa 자체 발명 버전) 을 돌렸다.
v0.2 는 방향 전환:

1. **(C') Progressive Codification 패턴 정립** — team-product 스킬을 seed 로 포팅 → labs 래퍼로 실행 → **improve target 은 SKILL.md 자체 + deterministic 규칙의 script 추출**까지. `ax-implement` 1 stage 로 이 패턴이 돌아가는지 증명.
2. **엔진 안전성** — R5 `improve_script()` 버그 fix + `improve_target` 추상화 (현재 `script.py` 하드코딩 → stage 별 선언 경로)
3. **북극성 수집 2 채널** — post-commit hook + `/ax-feedback` CLI
4. **haru 실전 첫 접촉** — E (ax-implement) + F (ax-qa) 둘 다 **haru** (`~/hq/projects/journal/`) 에서 진행. private 제품이라 나쁜 산출물이 public 프로젝트로 흘러갈 리스크 없음. v0.1 `labs/ax-qa` 버전은 그대로 재사용.

## 범위 원칙

- **1 stage only**: `ax-implement` 만. ax-qa 포팅은 v0.3.
- **패턴 정립이 곧 과업**: 여러 stage 동시 포팅하지 않음. (C') 가 실제로 도는지가 유일한 판단 기준.
- **v0.1 labs/ax-qa 는 동결** — 엔진 smoke test 로 남기되 건드리지 않음. rubato 실전 (F) 에서 재사용.
- **토큰 효율을 rubric 축에 편입** — 자연어 SKILL.md 의 토큰 낭비가 수치로 드러나야 script 추출 판정이 가능.
- **재현성 체크, 기준선 확정, 대시보드 v2 는 out of scope** — v0.3.
- **`/ax-diff` 수동 명령 out of scope** — v0.2 는 post-commit hook 하나.

## (C') Progressive Codification — 핵심 개념

team-product 스킬은 쓸 만한 운영 지식이 쌓여 있지만 **전부 자연어**라서 두 가지 병목이 있다:

1. **자의적 해석**: AI 가 "이 체크 해야 함" 같은 문장을 그냥 넘어갈 수 있다
2. **토큰 낭비**: 매번 같은 체크리스트를 재읽고 재해석

v0.2 의 진짜 가치는 이 두 병목을 구조적으로 푸는 패턴을 박는 것:

```
[seed]     team-product/skills/product-implement/SKILL.md
            (자연어 100%)
              ↓
[포팅]     plugin/skills/ax-implement/SKILL.md   (seed v0)
              ↓
[labs 래퍼] labs/ax-implement/
            ├── program.md            harness 규칙 + improve_target 선언
            ├── rubric.yml            오너기대치 + 정량 + 토큰효율
            ├── script.py             fixture + skill 로드 → Claude CLI
            └── input/{fixture}/
              ↓
[1 cycle]  실행 → 산출물 평가 → rubric 점수 + 토큰 소비 기록
              ↓
[improve]  SKILL.md 개선  OR  deterministic 규칙 → scripts/ 추출
```

improve 가 "SKILL.md 몇 줄 고치기" 만이 아니라 **자연어 규칙을 코드로 분리하는 것**까지 포함한다는 게 핵심.
v0.2 안에서 실제 script 추출까지 자동으로 일어나진 않아도 **패턴/훅/`improve_target` 추상화**는 v0.2 에서 완결.

## 완료 기준

### A. 엔진 — R5 fix + `improve_target` 추상화  ✅

- [x] `src/loop.py:improve_script()` 리팩토링 (`improve_artifact()` 로 개명 + 함수 분리)
  - [x] 프롬프트 강화: "반드시 대상 파일 **전체**를 단일 code block 에 출력" 명시 (`build_improve_prompt`)
  - [x] 덮어쓰기 전 구조 체크 (`validate_structure`, 언어별)
    - python: `def main(` 또는 `if __name__` 존재
    - markdown: frontmatter `name:` 또는 H2 섹션 2개 이상
  - [x] 덮어쓰기 전 백업: `{target}.prev` 로 보존 (`backup_and_write`)
  - [x] 최소 크기 가드: python 30줄, markdown 40줄 미만 거부
  - [x] 실패 시 meta 에 `skipped: true` + `skip_reason` 기록 (print 로그도)
- [x] **`improve_target` 추상화** (`load_program` frontmatter 파싱)
  - [x] `labs/ax-qa/program.md` 에 frontmatter `improve_target: script.py` 추가
  - [x] `src/loop.py:run()` 이 `program_config["improve_target"]` 읽어서 lab_dir 기준 경로 해석
  - [x] `best/` 저장 경로도 `improve_target_path.name` 사용하게 일반화
  - [x] `script_version` 로그 컬럼은 이제 improve_target 해시 (ax-qa 는 script.py 로 값 동일)
- [x] **단위 테스트** `tests/test_loop_improve.py` — 23 케이스 전원 통과
  - extract_code_block: 블록 크기 기반 선택 (R5 핵심 가드) + 폴백 + 언어별
  - validate_structure: python/markdown 각 pass/fail 케이스
  - backup_and_write: .prev 생성 / 파일 없을 때 건너뜀
  - load_program: frontmatter 있음/없음/파일 없음
  - **improve_artifact R5 재현 시나리오**: 9줄 부분 블록 → skip + 원본 유지
  - improve_artifact 정상 교체 → 적용 + .prev 생성
  - improve_artifact markdown 타겟 end-to-end
- [x] **labs/ax-qa 회귀 실행**: `--max-iter 2 --threshold 0.95` 로 기존 동작 보존 확인
  - iter 1 score **1.0** (v0.1 0.96 대비 향상), 임계값 도달 조기 종료
  - cost $0.9653, improve_target 경로 정확히 로깅, best/ 저장 정상
- [ ] (선택) `--threshold 0.99` 로 improve 경로 실행 검증 — 비용/품질 저하 리스크 있어 v0.2 내 보류. 단위 테스트로 모든 분기 커버됨.

### B. 토큰 집계 조사 (격상: rubric 설계 input)  ✅

v0.2 에서 B 는 단순 버그 조사가 아니라 **rubric "토큰 효율" 축 설계의 전제**였음.

- [x] `src/claude.py` 의 token 파싱 경로 확인 — Claude CLI `--output-format json` 구조 재검증
- [x] prompt caching 필드 확인 — `cache_creation_input_tokens` / `cache_read_input_tokens` **둘 다 별도 존재**. "print hello" 최소 프롬프트에도 cache_creation 36,796 토큰 (세션 baseline).
- [x] **결정: (b) — cache 필드 별도 키로 기록**
  - (a) 미채택: prompt byte 토큰 추정 오차 큼
  - (c) 미채택: rubric 토큰 효율 축 설계 불가
  - 스키마 변경 없음 (tokens JSONB 가 새 키 흡수)
- [x] `src/claude.py` `tokens` shape 확장: `{input, output, cache_creation, cache_read}` (4 필드)
- [x] `src/loop.py` `empty_tokens` 4 필드 + stderr aggregation 도 4 필드 합산
- [x] `src/judge.py` empty return 도 4 필드 shape
- [x] `src/db.py` `AX_VERSION = "v0.2"` bump
- [x] dashboard 호환 확인 — `t[part]?.input ?? 0` 옵셔널 체이닝이라 새 필드 무시, 기존 키 유지 → 깨지지 않음. 대시보드 cache breakdown 표시는 v0.3.
- [x] 실측 검증: `.venv/bin/python -c "import claude; claude.call('say hi')"` → `{'input': 6, 'output': 10, 'cache_creation': 36830, 'cache_read': 0}` cost $0.3103 반환 확인
- [x] **rubric 토큰 효율 축 설계 (E 로 전달)**: 1) 권장 `total_cost_usd` (cache tier 가중치 반영), 2) 보조 `output_tokens` (산출물 장황함 감지). 첫 run 을 기준선으로 잡고 상대 비교로 감점. absolute threshold 는 v0.3.
- [x] `notes/v0.2-token-investigation.md` 결정 기록 (usage 필드 전수 정리 + rubric 설계 포함)

### C. 자동 diff 수집 — post-commit hook  ✅

- [x] **설계 확정**: `.ax-generated.jsonl` JSONL 매니페스트 + `.ax-artifacts/{path}` 원본 사본. 커밋 후 hook 이 교집합 검사 → diff 측정 → intervention insert → 매니페스트/artifact 제거 (베이스라인 리셋).
- [x] `scripts/ax_generated.py` — 매니페스트 헬퍼 (`record` / `lookup` / `read_artifact` / `reconcile` / `all_tracked_paths`)
- [x] `scripts/ax_post_commit.py` — hook 본체
  - [x] `__file__` 기준 moomoo-ax 루트 자동 해석 → .env 로딩 재사용
  - [x] `git diff-tree --no-commit-id --name-only -r HEAD` 로 커밋 변경 파일 추출
  - [x] `difflib.SequenceMatcher` 기반 hunks/lines 측정 (pure Python)
  - [x] Supabase `interventions` row insert (`src/db.py:log_intervention`)
  - [x] 성공 시 매니페스트 엔트리 + artifact 제거 (베이스라인 리셋)
  - [x] `MOOMOO_AX_DRY_RUN=1` 환경변수로 dry-run 모드
  - [x] hook 실패가 커밋 깨지 않도록 0 exit 보장
- [x] `src/db.py` `log_intervention()` 함수 추가 (interventions 스키마 대응)
- [x] `scripts/install_ax_diff_hook.sh` — 대상 프로젝트에 설치
  - [x] `.git/hooks/post-commit` 에 marker 블록 append (idempotent)
  - [x] 기존 post-commit 과 공존
  - [x] **`.gitignore` 자동 갱신** — `.ax-generated.jsonl` + `.ax-artifacts/` 제외 (smoke 1회차에서 발견)
- [x] **단위 테스트** `tests/test_ax_post_commit.py` — 15 케이스 전원 통과
  - ax_generated: record / lookup / reconcile / all_tracked_paths / latest-entry 선택
  - compute_diff_stats: identical / pure add / pure delete / replace
  - process_commit end-to-end: 매니페스트 없음 / 원본 그대로 / 수정됨 / untracked 무시 / 혼합
  - 임시 git repo fixture 로 실 git 명령 흐름 검증
- [x] **실 smoke test (`/tmp/ax-hook-smoke/`)**:
  - install → post-commit hook + .gitignore 블록 생성
  - record → 수정 → commit → hook 자동 발동
  - Supabase `interventions` 실 insert (3+ / 1-, hunks 2/1, commit sha 정확)
  - smoke row 삭제, 임시 repo `~/.Trash/` 이동
- [x] 대시보드 `north-star/page.tsx` 이미 `interventions` count 읽음 → F 에서 실 row 들어오면 자동 표시

### D. `/ax-feedback` CLI  ✅

- [x] `plugin/skills/ax-feedback/SKILL.md` — team-ax plugin **첫 실제 skill** (나머지 ax-* 폴더는 아직 껍데기)
  - 호출 예 + 동작 설명 + 실행 커맨드 절대경로 + 왜 이 채널이 필요한지 명시
  - priority LLM 자동 추정은 v0.3+ 으로 명시적 분리
- [x] `scripts/ax_feedback.py` — CLI
  - [x] 본문: positional arg 우선, 비면 stdin 폴백, 둘 다 없으면 exit 1
  - [x] 기본 project: `git rev-parse --show-toplevel` basename 자동 추출
  - [x] 기본 user: `MOOMOO_AX_USER` env → `git user.name` 매핑 (`lazyyoyo`→`yoyo`) → `yoyo` 폴백
  - [x] `--priority {high,medium,low}` 기본 medium (argparse choices 로 CHECK 제약 사전 방어)
  - [x] `--stage`, `--project`, `--user` 옵션 제공
  - [x] `feedback_backlog` insert → row id 수신 (service_role, `return=representation`)
  - [x] 확인 메시지: id / user / priority / project / stage / content 미리보기
- [x] `src/db.py` `log_feedback()` 함수 추가 (`return=representation` prefer header 로 id 반환)
- [x] **단위 테스트** `tests/test_ax_feedback.py` — 14 케이스 전원 통과
  - infer_user: env var 우선, lazyyoyo → yoyo 매핑, unknown passthrough, git 없음 폴백
  - infer_project: toplevel basename, 저장소 밖 None
  - read_content: arg 우선, 공백 trim, 빈 arg + tty 는 empty, stdin 폴백
  - CLI subprocess: 빈 content → exit 1
  - main() mock 통합: happy path / default medium / db 실패 exit 2
- [x] **실 smoke** — `.venv/bin/python scripts/ax_feedback.py --priority low --stage ax-feedback "..."` 실행
  - Supabase row insert 확인: id `2a412956-dd69-44fd-bc22-45efafd5de19`, user=yoyo, project=moomoo-ax, priority=low, status=open
  - 이 row 는 **첫 실 피드백** 으로 보존 (대시보드 empty state → 실 content 검증)
- [x] 대시보드 `feedback/page.tsx` + `north-star/page.tsx` 가 이미 `feedback_backlog` 읽음 → 자동 표시

### E. `ax-implement` — (C') 패턴 첫 케이스  ✅ (파이프 검증)

> **결과 요약**: levelup loop 파이프 검증 완료. iter 1 score 0.886 → improve → iter 2 score 1.0.
> 단, 이번 run 에서 발견: **자연어 압축 ≠ codification**. 진짜 codification (`[run: ...]` 규약 + script 추출 + multi-file bundle + skill invoke 메커니즘) 은 **v0.3 로 이월**. 상세: `notes/2026-04-11-v0.2-e-codification-insight.md`.

#### E1. team-product 포팅  ✅
- [x] `plugin/skills/ax-implement/SKILL.md` ← team-product/skills/product-implement/ 에서 복사 (295줄)
- [x] `plugin/skills/ax-implement/references/` ← preflight/review/security/backpressure 4개 복사 (현재 장식 상태 — v0.3 에서 inline 또는 tool read 결정)
- [x] frontmatter rename (ax-implement)
- [x] moomoo-ax 컨텍스트 불일치 구간에 `[ax-note]` 주석 (subagent 계층, .phase 파일, Codex Adversarial, /product-qa GATE 등)

#### E2. labs 래퍼  ✅
- [x] `labs/ax-implement/program.md` — 오너 규칙 + 입력/출력 계약 + `improve_target: ../../plugin/skills/ax-implement/SKILL.md`
- [x] `labs/ax-implement/rubric.yml` — **범용 (fixture-agnostic)** 으로 재작성. critical 6 + high 6 + medium 7 + low 3. fixture-specific 검증은 SPEC.md 의 "완료 기준" 으로 위임
- [x] `labs/ax-implement/script.py` — stdin fixture + SKILL.md 주입 + Claude CLI call + stdout 산출물

#### E3. fixture 준비  ✅
- [x] **haru** 의 `7475bef feat(dev): @날짜 파서 구현 + 테스트 16건` 선정 — 단일 파일 파서 98줄 + 테스트 16건, spec 문서 (`dev/docs/specs/date-natural-input.md`) 존재
- [x] `labs/ax-implement/input/haru-7475bef/` — `SPEC.md` (완료 기준 7개) + `META.md` + `base/{parse-hashtag.ts,date-utils.ts}`

#### E4. 첫 cycle 실행  ✅
- [x] v0 rubric (fixture-specific) 으로 첫 run → score **1.0** 바로 통과, cost $0.9510, duration 97s. 파이프 검증만 됨.
- [x] rubric 범용화 리팩터 (범용 lint 축 추가) 후 재실행 → iter 1 score **0.886** (medium 2 fail — 함수 길이, DRY 요일 중복)
- [x] `labs/ax-implement/logs/` + `best/` 생성 확인 (이전 v1 rubric run 은 `labs/ax-implement/logs_run1_v1rubric/`, `best_run1_v1rubric/` 로 보존)
- [x] Supabase `levelup_runs` row 확인 (2 runs)

#### E5. improve 경로 동작 확인  ✅
- [x] iter 1 score 0.886 → `improve_artifact` 호출 → SKILL.md 덮어쓰기 (`6a441acf → a2fdb5f1`, 295줄 → 54줄, R5 guard 정상 동작)
- [x] iter 2 가 새 SKILL.md 로 정상 로드 → score **1.0** → 임계값 도달 종료
- [x] **"script 추출 후보" 식별**: SKILL.md 안의 R-LEN (공개 함수 본체 60줄) 과 R-DRY (리터럴/상수 단일 선언) 두 규칙이 가장 우선 순위. R-LEN 은 AST 기반 `scripts/check_r_len.py` 로 추출 가능 (v0.3 첫 타겟). R-DRY 는 AST + regex 스캔 조합.

#### E 진행 메모
- 2026-04-11 첫 run — v0 rubric 은 fixture-specific 하게 잘못 짜여서 score 1.0 바로 통과. improve 경로 미발동.
- 2026-04-11 rubric 범용화 — fixture-agnostic 으로 재작성 후 재실행. iter 1 0.886 → improve → iter 2 1.0. (C') 패턴 파이프 증명.
- 2026-04-11 E 마무리 — SKILL.md 는 원본 295줄 복구. 54줄 결과물은 `plugin/skills/ax-implement/SKILL.iter2-snapshot.md` 로 보관. 교훈 노트: `notes/2026-04-11-v0.2-e-codification-insight.md`.

#### E 미해결 (v0.3 로 이월)
- **skill invoke 메커니즘 괴리** — 현재 `claude -p` one-shot 은 Claude Code plugin 의 tool-enabled skill invocation 과 다름. levelup loop 가 측정하는 품질이 product loop 실 품질과 괴리.
- **`[run: ...]` 규약 부재** — 이번 run 은 자연어 295줄을 자연어 54줄로 압축만 했음. 진짜 codification 은 자연어가 `[run: scripts/foo.py]` 로 교체돼야 함.
- **improve_target = single file** — SKILL.md 만 개선 가능. skill bundle (SKILL.md + scripts + references + agents) 단위로 확장 필요.
- **improve tokens 로깅 bug** — `logs/{iter}.json` 의 `tokens.improve` 가 0 으로 찍힘 (loop.py 에서 log_data serialize 가 improve 호출보다 먼저). `total_cost_usd` 는 정상. fix 소요 작음.
- **references/ 장식 상태** — 4개 파일 복사돼있지만 script.py 가 SKILL.md 만 주입. inline 합치기 or tool-based read 로 해결 필요.

### F. haru 실전 첫 적용 (ax-qa, v0.1 labs 버전)

- [ ] **haru** 최근 dev 작업 중 **아직 머지 안 된 브랜치 1개** 선정 (yoyo 확인)
- [ ] 해당 브랜치 변경 파일을 fixture 형태로 `labs/ax-qa/input/` 에 주입
- [ ] `labs/ax-qa` 실행 → QA Report 산출
- [ ] 산출물을 haru 브랜치에 적용 (오너 수락/수정)
- [ ] interventions row 자동 수집 확인 (C 완료 후)
- [ ] `versions/v0.2/first-contact.md` — 체감 리포트, 오너 개입 원본 감각 기록
- [ ] 주의: haru 는 yoyo+남편 2인 사용 private 제품. ax-qa 산출물이 부적절해도 이 자리에서는 적용/거부 판단 자유롭게.

### G. 대시보드 최소 업데이트

- [ ] Live 탭 30초 auto-poll (setInterval + revalidate)
- [ ] 다른 탭 수정 없음
- [ ] 빌드/배포

## Out of scope (v0.3+)

- **ax-qa 포팅** (v0.1 labs 만 계속 사용) → v0.3
- **ax-define / ax-design / ax-init / ax-deploy 포팅** → v0.3~0.5
- **script 추출 자동화** — v0.2 는 식별만, 자동 분리는 v0.3+
- **`/ax-diff` 수동 명령** → v0.3
- **재현성 체크 / 기준선 숫자 확정** → v0.3
- **LLM diff severity 분류** → v0.3~0.4
- **대시보드 v2 재설계** → v0.3 판단
- **product_runs 자동 수집** (plugin 이 아직 skill 껍데기) → v0.3
- **`ax-autopilot`** → v0.4
- **하네스 진화 (rnd/)** → v1.x

## 확정 사항 (인터뷰 결과 + C' 전환)

1. **v0.2 범위**: 1 stage (ax-implement) 만. 다른 stage 포팅은 v0.3+
2. **패턴**: (C') Progressive Codification — team-product seed 포팅 + labs 래퍼, improve 대상은 SKILL.md + deterministic 규칙의 script 추출 (개념/훅 v0.2, 자동 추출 v0.3+)
3. **자동 diff 채널**: post-commit hook (`.ax-generated` 매니페스트 기반). `/ax-diff` 수동은 v0.3
4. **`/ax-feedback`**: CLI 직접 호출만 (대시보드 폼은 v0.3+)
5. **rubric 축**: 오너 기대치 + 정량 + **토큰 효율** (자연어 SKILL 의 낭비가 수치로 드러나게)
6. **rubato 실전**: v0.1 labs/ax-qa 버전으로 진행. ax-qa 포팅은 v0.3.
7. **ax-qa 동결**: v0.1 smoke test 로 남기되 건드리지 않음. improve_target 추상화 회귀 테스트에만 사용.

## 작업 순서 (권장)

```
A (R5 fix + improve_target 추상화)
  │     └─ B 와 독립, 병행 가능
  │
  ├─ B (토큰 조사 + rubric 토큰 축 설계)
  │
  ├─ C (post-commit hook)  ─────┐
  ├─ D (/ax-feedback CLI)  ─────┤  독립
  │                             ↓
  E (ax-implement 포팅 + 래퍼 + 첫 cycle)
      E1 포팅 → E2 래퍼 → E3 fixture → E4 첫 run → E5 improve 경로
  │
  ├─ F (rubato 실전 ax-qa) — C 완료 필수
  │
  └─ G (Live 30초 poll)
```

- A 는 반드시 먼저 (E5 에서 SKILL.md 덮어쓰기 검증하려면 improve_target 추상화가 있어야 함)
- B 는 A 와 병렬, 단 결과가 E 의 rubric 설계에 들어가야 하므로 **E2 이전에 결정 완료**
- C/D 는 A/B 와 병렬 가능
- E 의 E5 는 A 완료 후에만 의미 있음
- F 는 C 완료 후 (hook 없으면 interventions 수집 불가)

## 리스크 / 열린 질문

- **R6 (해소)**: post-commit hook 의 product_runs 의존 → `.ax-generated` 매니페스트 파일 기반으로 대체. v0.2 E 에서 ax-implement 실행 시 자동으로 매니페스트 생성하는 훅도 함께.
- **R7: ax-implement fixture recreate 난이도** — "작은 feature 가 들어가기 직전 상태" 를 만드는 게 single commit rollback 으로 자동화 가능한지 확인. 여의치 않으면 수동 구성. haru 는 구현 중이라 적절한 commit 을 고르기 쉬운 편.
- **R8: 토큰 집계 수정이 대시보드 Tokens 탭 깨짐** — B 결정 (c)(현상 유지 + 주석) 이 제일 싸고 v0.3 에서 정식 처리.
- **R9: haru 실전 브랜치 선정** — E3, F 시작 시점에 yoyo 와 sync 필요. haru HANDOFF.md / BACKLOG.md 확인.
- **R10: R5 회귀 테스트** — 함수 분리 후 pytest 1개 추가. improve_target 추상화로 python/markdown 양쪽 테스트.
- **R11 (신규): `improve_target` 이 markdown 일 때 "구조 체크" 기준을 어떻게 잡을지** — frontmatter `name:` 존재 + 최소 줄수 가드 우선. 정교화는 v0.3.
- **R12 (신규): team-product 포팅 시 팀 의존성 (conductor, subagent 구조)** — v0.2 는 "복사 후 불필요한 것 주석만" 으로 최소 편집. 본격 재구성은 levelup loop 가 담당.
- **R13 (신규): 토큰 효율 축이 rubric 에 들어가면 첫 run 에서 점수 왜곡 가능** — 첫 run 의 토큰 수치를 "기준선" 으로 박고, improve 이후 상대 비교로만 감점. 절대 threshold 는 v0.3.

## 진행 메모

(구현 중 업데이트)

- 2026-04-11: plan v1 작성 — R5 fix + 수집 인프라 + 2번째 stage
- 2026-04-11: plan v2 전면 개정 — (C') Progressive Codification 전환, 범위 1 stage 로 축소, ax-implement 재정의, improve_target 추상화 추가
- 2026-04-11: plan v2.1 — 실전 접촉지를 rubato → **haru** 로 전환 (E, F 둘 다). private 제품 우선 원칙을 PROJECT_BRIEF 사용자 섹션에도 명문화.
