# 2026-04-13 — Codex 전환 가능성 정리

## 목적

현재 `moomoo-ax` 코드베이스를 기준으로, **Claude Code 중심 구조를 Codex 에도 올라탈 수 있는 구조로 바꾸려면 무엇을 해야 하는지** 정리한다.

이 메모의 초점은 "당장 Claude 를 버린다" 가 아니라, **Claude 종속부를 분리해서 Codex backend 를 추가할 수 있게 만드는 것**이다.

## 결론 요약

전환은 가능하다. 다만 **지금 구조를 그대로 Codex 로 치환하는 1:1 포팅은 비현실적**이다.

이유는 간단하다.

1. 현재 product loop 배포물은 **Claude Code plugin 규약** 위에 올라가 있다.
2. 핵심 실행 경로가 `claude -p`, `--plugin-dir`, `/team-ax:ax-implement`, `Task(subagent_type=...)` 같은 **Claude 전용 인터페이스**에 묶여 있다.
3. 반대로 levelup/meta 쪽의 상당 부분은 이미 Python + shell + Supabase + Next.js 로 되어 있어서 **런타임만 분리하면 재사용 가능**하다.

따라서 추천 방향은:

> **"Claude plugin" 을 소스 오브 트루스로 두지 말고, "agent-agnostic stage bundle + runtime adapter" 구조로 재편한 뒤 Claude/Codex 를 각각 얇은 어댑터로 붙인다.**

## 현재 코드베이스에서 재사용 가능한 부분

Codex 전환 시 그대로 살릴 수 있는 축:

- `src/db.py`
  - Supabase 로깅 계층
- `scripts/ax_feedback.py`
  - 명시적 피드백 수집 CLI
- `scripts/ax_post_commit.py`
  - post-commit diff 기반 intervention 수집
- `dashboard/`
  - meta loop UI
- `labs/`
  - fixture, rubric, 실험 로그 구조
- `plugin/skills/ax-implement/scripts/`
  - `run_checks.sh`, `run_review_checks.sh`, `arch_compliance.py`, `dev_server_check.sh`
- `scripts/ax_product_run.py` 의 worktree 격리 방식
  - fixture repo 를 임시 worktree 로 복제해서 실행하는 아이디어 자체는 backend 와 무관하게 유효

즉, **문제의 핵심은 비즈니스 로직보다 런타임 결합**이다.

## 현재 코드베이스에서 Claude 종속이 강한 부분

### 1. 실행 래퍼

- `src/claude.py`
  - `claude -p` 호출 자체에 의존
  - `output_format="stream-json"` 파서가 Claude 이벤트 스키마에 묶여 있음
  - `allowed_tools`, `permission_mode`, `plugin_dir`, `bare`, `setting_sources`, `include_hook_events` 같은 옵션이 Claude 전용

### 2. product loop 진입 방식

- `scripts/ax_product_run.py`
  - prompt 기본값이 `/team-ax:ax-implement`
  - `plugin_dir=plugin` 로 로컬 Claude plugin 을 세션에 로드하는 구조
  - `.ndjson` 로그도 Claude event shape 를 전제로 함

### 3. 배포 제품 패키징

- `plugin/.claude-plugin/plugin.json`
- `plugin/skills/**/SKILL.md`
- `plugin/agents/*.md`

현재 배포 제품 `team-ax` 는 구조적으로 **Claude Code plugin** 이다.

### 4. 프롬프트 안의 Claude 문법

특히 [plugin/skills/ax-implement/SKILL.md](../plugin/skills/ax-implement/SKILL.md):

- `allowed-tools`
- `${CLAUDE_SKILL_DIR}`
- `/team-ax:ax-implement`
- `Task(subagent_type="team-ax:executor")`
- `Task(subagent_type="team-ax:reviewer")`
- `TodoWrite`

이 레벨은 단순 문구 치환으로는 옮겨지지 않는다.

## 로컬 Codex CLI 표면에서 확인된 사실

2026-04-13 현재 로컬에서 아래를 확인했다.

```bash
codex --help
codex exec --help
codex mcp --help
```

확인된 점:

- `codex exec` 가 존재한다.
- non-interactive 실행과 `--json` 출력이 가능하다.
- 작업 디렉토리 지정은 `--cd`, 샌드박스는 `--sandbox`, 추가 쓰기 경로는 `--add-dir` 로 줄 수 있다.
- `codex review` 와 `codex mcp` 가 별도 서브커맨드로 존재한다.

반대로 help 표면에서 **즉시 보이지 않는 것**:

- Claude 의 `--plugin-dir` 에 해당하는 로컬 plugin 로더
- `/team-ax:ax-implement` 같은 slash skill 호출 규약
- `Task(subagent_type=...)` 와 1:1 대응하는 plugin-subagent 로더

따라서 현재 기준의 Codex 전환은:

> **"Claude plugin 을 Codex 가 읽게 만든다" 가 아니라, "Python 오케스트레이터가 Codex 를 직접 호출하게 바꾼다" 가 맞다.**

## 추천 전환 전략

### 전략 A — 현실적 1차 목표

**Python 오케스트레이터 유지 + Codex backend 추가**

- `src/loop.py` 와 `scripts/ax_product_run.py` 는 유지
- Claude runtime 대신 Codex runtime adapter 를 추가
- stage 정의는 Claude plugin 에서 분리
- reviewer / executor / design-engineer 역할은 Python 쪽에서 명시적으로 fan-out

장점:

- 기존 levelup/meta 인프라를 최대한 재사용
- 전환 범위를 런타임 계층으로 제한 가능
- Claude 와 Codex 동시 지원이 가능

단점:

- `SKILL.md` 내부 오케스트레이션을 그대로 못 쓴다
- subagent 호출을 prompt 내부가 아니라 Python 레이어로 끌어올려야 한다

### 전략 B — 전면 재설계

**Codex-native product loop 로 갈아타기**

- `plugin/` 중심 구조를 버리고 Codex 전용 orchestration 문서를 새로 설계
- Claude 쪽은 호환 레이어로만 유지

장점:

- 장기적으로 구조가 더 깨끗함

단점:

- v0.3 목표를 늦춘다
- 지금까지 만든 `team-ax` 자산 활용도가 낮아진다

현재 단계에서는 **전략 A 가 맞다**.

## 권장 아키텍처

### 1. runtime adapter 계층 도입

신규 구조 예시:

```text
src/runtime/
├── base.py            # RunRequest / RunResult / ToolEvent / ReviewResult
├── claude_backend.py  # 기존 src/claude.py 내용 이관
├── codex_backend.py   # codex exec 래퍼
└── normalize.py       # 런타임별 event -> 공통 schema
```

핵심 원칙:

- `src/loop.py` 와 `scripts/ax_product_run.py` 는 `Claude` 를 직접 import 하지 않는다.
- 둘 다 `RuntimeBackend` 인터페이스만 의존한다.
- 로그/대시보드는 공통 schema 만 본다.

공통 결과 shape 예시:

```python
RunResult(
    success: bool,
    output: str,
    duration_sec: float,
    cost_usd: float | None,
    tokens: dict[str, int] | None,
    tool_events: list[ToolEvent],
    raw_event_log_path: Path | None,
    session_id: str | None,
    error: str | None,
)
```

### 2. stage 정의를 plugin 밖으로 빼기

지금은 `plugin/skills/ax-implement/SKILL.md` 가 사실상 source of truth 역할을 하고 있다. 이 구조로는 Codex 전환이 어렵다.

권장:

```text
stages/
└── ax-implement/
    ├── ORCHESTRATION.md
    ├── references/
    ├── scripts/
    └── roles/
        ├── executor.md
        ├── design-engineer.md
        └── reviewer.md
```

역할:

- `stages/ax-implement/` 가 **실제 source of truth**
- `plugin/skills/ax-implement/SKILL.md` 는 Claude adapter
- 이후 Codex prompt composer 도 같은 source 를 사용

즉, `plugin/` 은 배포 형식이지 원본이 아니어야 한다.

### 3. prompt 내부 orchestration 을 Python 으로 끌어올리기

가장 큰 구조 변화 포인트다.

현재:

- `SKILL.md` 가 build loop 를 돌면서
- 내부에서 `Task(subagent_type=...)` 를 호출하고
- `plan.md` 를 직접 갱신한다

Codex 전환 가능 구조:

- Python conductor 가 `plan.md` 를 읽음
- 태스크를 선택함
- 역할별 backend 호출을 직접 수행함
  - executor run
  - reviewer run
  - 필요 시 design-engineer run
- 결과에 따라 `plan.md` 갱신 / fix task 삽입

즉:

> **"오케스트레이션은 Python, 에이전트는 runtime backend"**

이렇게 바꾸면 Claude 에도 Codex 에도 붙일 수 있다.

## 파일 단위로 보면 무엇을 바꿔야 하나

### 1단계 — Claude 결합부를 격리

- `src/claude.py` → `src/runtime/claude_backend.py`
- `src/loop.py`
  - `import claude as claude_api` 제거
  - `--backend claude|codex` 옵션 추가
- `scripts/ax_product_run.py`
  - `claude.call()` 직접 호출 제거
  - backend 선택 가능하게 변경

### 2단계 — source of truth 재배치

- `plugin/skills/ax-implement/SKILL.md` 의 본문에서
  - build loop
  - review loop
  - subagent dispatch 규칙
  - plan.md 갱신 규칙
  - script 호출 규칙
  를 `stages/ax-implement/ORCHESTRATION.md` 로 옮긴다.

- `plugin/agents/*.md` 도 `stages/ax-implement/roles/*.md` 로 승격

### 3단계 — Codex backend 추가

Codex backend 최소 요구사항:

- `codex exec --json`
- `--cd <worktree>`
- `--sandbox workspace-write`
- 필요 시 `--add-dir`
- 마지막 메시지/이벤트 로그 파일 저장

이 backend 는 우선 **one-shot task runner** 로만 구현해도 된다.

중요:

- 첫 버전에서는 Codex 안에서 다시 subagent 를 부르게 하지 말고
- Python conductor 가 역할별로 여러 번 `codex exec` 를 호출하는 편이 안전하다

### 4단계 — 로그 공통화

현재 Claude 는 NDJSON event 를 남긴다. Codex 도 `--json` 이 있으므로 raw log 는 별도 저장 가능하다.

권장:

- raw log 는 backend별 원본 그대로 보존
- 대시보드/판정용은 공통 schema 로 normalize

예:

```text
.harness/runs/
├── <run_id>.claude.ndjson
├── <run_id>.codex.jsonl
└── <run_id>.normalized.json
```

### 5단계 — 점진 검증

동일 fixture 로 아래를 비교한다.

1. Claude backend
2. Codex backend

비교 축:

- 태스크 소진 여부
- `plan.md` 갱신 구조
- fix task 생성 규약 준수
- `run_checks.sh` / `run_review_checks.sh` 통과 여부
- git commit 단위
- intervention / feedback 수집 영향 없음

## 무엇을 먼저 하지 말아야 하나

### 1. `plugin/` 전체를 먼저 Codex 문법으로 바꾸지 말 것

그렇게 하면 Claude 경로도 깨지고, source of truth 분리 없이 문법만 갈아끼우는 실패를 반복한다.

### 2. `Task(subagent_type=...)` 를 Codex prompt 안에서 흉내내려 하지 말 것

현재 product loop 의 진짜 자산은 subagent 문법이 아니라:

- task 분할
- fix depth 규약
- reviewer gate
- backpressure
- worktree 격리

이다. 이 규약을 Python conductor 로 올려야 한다.

### 3. 대시보드/DB부터 건드리지 말 것

Codex 전환의 병목은 meta loop 가 아니라 runtime adapter 다.

## 추천 작업 순서

1. `src/runtime/` 계층 도입
2. `src/loop.py` 를 runtime-agnostic 하게 수정
3. `scripts/ax_product_run.py` 를 runtime-agnostic 하게 수정
4. `stages/ax-implement/` 를 source of truth 로 분리
5. `plugin/skills/ax-implement/` 를 Claude adapter 로 축소
6. `codex_backend.py` 추가
7. 동일 fixture 로 Claude/Codex 양쪽 smoke 실행
8. 그 다음에야 ax-qa / ax-design 확장 검토

## 최소 완료 조건

Codex 전환 "가능" 판정 기준:

- `src/loop.py` 가 `--backend codex` 로 1개 stage 를 실행할 수 있다.
- `scripts/ax_product_run.py` 가 `--backend codex` 로 fixture worktree 실행이 된다.
- `plan.md` 갱신 / fix task 삽입 규약이 runtime 과 무관하게 유지된다.
- 대시보드/DB 스키마를 깨지 않고 로그가 들어간다.
- Claude backend 도 계속 동작한다.

## 한 줄 권고

> **Claude plugin 을 포팅 대상으로 보지 말고, `runtime adapter + stage bundle + Python conductor` 로 축을 재정의해야 Codex 전환이 현실화된다.**
