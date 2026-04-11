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

### B. 토큰 집계 조사 (격상: rubric 설계 input)

v0.2 에서 B 는 단순 버그 조사가 아니라 **rubric "토큰 효율" 축 설계의 전제**다.

- [ ] `src/claude.py` 의 token 파싱 경로 확인 — Claude CLI `--output-format json` 구조 재검증
- [ ] prompt caching 필드 확인 — `cache_read_input_tokens` / `cache_creation_input_tokens` 별도 존재 여부
- [ ] 수정안 결정:
  - (a) 실제 prompt byte 기반 대체 지표 추가
  - (b) cache 관련 필드를 별도 컬럼으로 기록
  - (c) 현상 유지 + 주석
- [ ] **rubric 토큰 효율 축 설계**: 같은 fixture 기준 output_tokens 가 일정 범위 넘으면 감점 (수치 기준선은 ax-implement 첫 run 결과 본 뒤 정함)
- [ ] `notes/v0.2-token-investigation.md` 로 결정 기록

### C. 자동 diff 수집 — post-commit hook

- [ ] `scripts/install-ax-diff-hook.sh` — `.git/hooks/post-commit` 에 idempotent append
- [ ] `scripts/ax_post_commit.py`
  - [ ] `.ax-generated` 매니페스트 파일 기반 판정 (product_runs 의존 회피, R6 해결책)
  - [ ] `git diff HEAD~1 HEAD -- {path}` → hunks/lines/files 파싱
  - [ ] `interventions` row insert (service_role)
- [ ] smoke test: 로컬에서 dummy `.ax-generated` + 파일 수정 commit → interventions row 확인
- [ ] 대시보드 North Star 탭에서 row 표시 확인

### D. `/ax-feedback` CLI

- [ ] `plugin/skills/ax-feedback/SKILL.md` — team-ax plugin 첫 실제 skill
- [ ] `scripts/ax_feedback.py`
  - [ ] arg 또는 stdin 입력
  - [ ] git repo 이름 → project 컨텍스트 자동 추출
  - [ ] `--priority high|medium|low`, 미지정 시 medium
  - [ ] `feedback_backlog` row insert (service_role)
  - [ ] 확인 메시지 + row id 출력
- [ ] 실사용 smoke: yoyo 세션에서 `/ax-feedback "..."` 한 번 호출 → 대시보드 Feedback 탭 확인

### E. `ax-implement` — (C') 패턴 첫 케이스

#### E1. team-product 포팅
- [ ] `plugin/skills/ax-implement/SKILL.md` ← team-product/skills/product-implement/ 에서 복사
- [ ] `plugin/skills/ax-implement/references/` ← 필요 체크리스트 복사 (preflight, review, security 등)
- [ ] skill 이름 / 경로 / team-ax 네이밍 rename
- [ ] 불필요한 팀 의존(예: conductor 메인세션 전제 등) 정리 — 단, 로직은 건드리지 않음. "이 부분은 script 추출 후보" 라고 주석만.

#### E2. labs 래퍼
- [ ] `labs/ax-implement/program.md`
  - 오너 규칙 / 입력 계약 / 출력 계약
  - `improve_target: ../../plugin/skills/ax-implement/SKILL.md`
  - fixture 디렉토리 구조 표준 준수 (`input/{fixture_id}/`)
- [ ] `labs/ax-implement/rubric.yml`
  - critical: 타입 체크 통과, 빌드 통과, 스펙 항목 전부 포함, Owner Expectation
  - high: 기존 테스트 regress 없음, lint 0, Owner Expectation
  - medium: 코드 스타일 일관성, 불필요 diff 없음, **토큰 효율**
  - low: 주석 품질, 변수명 일관성
- [ ] `labs/ax-implement/script.py`
  - stdin fixture 로드 (ax-qa 와 동일 `=== FILE: {rel} ===` 마커)
  - `plugin/skills/ax-implement/SKILL.md` 로드 → Claude CLI 시스템 프롬프트에 주입
  - fixture 스펙/컨텍스트 → Claude CLI user input
  - stdout: 구조화된 구현 산출물 (patch + 요약 + 자체 검증)

#### E3. fixture 준비
- [ ] **haru** (`~/hq/projects/journal/`) 최근 **작은 feature 커밋 1건** 선정 (30~100 줄 수준)
- [ ] `labs/ax-implement/input/{fixture_id}/`  — fixture_id 규약: `haru:{short_sha}`
  - `SPEC.md` — "이 커밋이 구현해야 했던 feature" 를 스펙 형태로 recreate
  - `base/` — 커밋 직전 상태의 관련 파일들
  - `META.md` — fixture_id, 원본 커밋 해시, 선택 이유
- [ ] haru 선정 과정 — 구현 중이면서 의도가 명확한 commit 우선. decisions.md / BACKLOG.md 참조해 맥락 복원 가능한 것.

#### E4. 첫 cycle 실행
- [ ] `.venv/bin/python src/loop.py ax-implement --user yoyo --fixture {fixture_id} --max-iter 2 --threshold 0.85` (threshold 첫 run 은 낮게)
- [ ] `labs/ax-implement/logs/` + `best/` 생성 확인
- [ ] Supabase `levelup_runs` row 확인
- [ ] 대시보드 Levelup 탭에 run 표시 확인

#### E5. improve 경로 동작 확인
- [ ] threshold 를 의도적으로 높여(`0.99`) iter 2 이상 돌려서 `improve_script` 가 `SKILL.md` 를 실제로 덮어쓰는지 확인
- [ ] 덮어쓴 SKILL.md 가 구조 체크 통과, 다음 iter 에서 정상 로드
- [ ] **"script 추출 후보"** 식별 — SKILL.md 섹션 중 deterministic 해 보이는 부분 리스트업 (자동 추출은 아니고 v0.3 입력)

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
