# moomoo-ax MVP (v0.1) 구현 핸드오프

## 스코프

`run` (Phase 2만) + `status`. 정적 게이트만. Claude 단일 모델.

CPS/PRD는 이미 있다고 가정하고, "코드 생성 → 정적 게이트 → keep/discard → 반복" 루프만 돌린다.

## 만들 파일

```
moomoo-ax/
├── skills/ax-loop/
│   ├── SKILL.md                 ← 스킬 진입점 (Claude Code가 읽는 파일)
│   └── scripts/
│       ├── orchestrator.py      ← 핵심. 루프 제어 + CLI
│       ├── gate_static.sh       ← lint/typecheck/build 게이트
│       └── worker.py            ← Claude headless 호출 래퍼
├── agents/
│   └── coder.md                 ← 코더 워커 역할 정의
├── harness/
│   └── schemas/
│       └── code_patch.json      ← 워커 산출물 JSON 스키마
└── .claude-plugin/
    ├── plugin.json              ← 이미 있음
    └── marketplace.json         ← 이미 있음 (없으면 생성)
```

## orchestrator.py — 핵심 로직

### CLI 인터페이스

```bash
python orchestrator.py run --project ~/hq/projects/rubato --max-iter 5
python orchestrator.py status --project ~/hq/projects/rubato
```

### run 커맨드 흐름

```
1. 프로젝트 .harness/ 디렉토리 확인/생성
2. CPS 또는 PRD 파일 존재 확인 (없으면 에러)
3. 루프 시작:
   a. worker.py로 Claude 호출 → 코드 패치 생성
   b. 패치 적용 (git apply 또는 직접 파일 쓰기)
   c. gate_static.sh 실행
   d. 판정:
      - 통과 → keep (git commit, 체크포인트 저장, best 갱신)
      - 실패 → discard (git checkout -- ., 에러 메시지를 다음 iteration 프롬프트에 포함)
   e. max_iter 도달 또는 연속 N회 실패 시 중단
4. 최종 상태 출력
```

### 판정 로직 (keep/discard)

```python
def judge(gate_result):
    if gate_result["static"]["passed"]:
        return "keep"
    else:
        return "discard"
    # MVP에서는 정적 게이트만이므로 단순 이진
```

### 체크포인트 저장

```python
# .harness/checkpoints/build_best.json
{
    "stage": "build",
    "timestamp": "ISO8601",
    "git_ref": "커밋 해시",
    "iteration": 3,
    "gate_results": {"static": true},
    "tokens_used": {"claude": 12000}
}

# .harness/checkpoints/history/build_001.json, build_002.json, ...
```

### 로그 기록

```python
# .harness/logs/iteration_001.json
{
    "iteration": 1,
    "timestamp": "ISO8601",
    "worker": "claude",
    "model": "claude-sonnet-4-20250514",
    "stage": "build",
    "verdict": "keep" | "discard",
    "gate_results": {"static": {"passed": true|false, "errors": [...]}},
    "tokens": {"input": 3000, "output": 2000},
    "duration_sec": 45,
    "error_summary": null | "린트 에러 3건"
}
```

## gate_static.sh

프로젝트 루트에서 실행. exit 0 = 통과, exit 1 = 실패.

```bash
#!/bin/bash
set -e

PROJECT_DIR="$1"
RESULT_FILE="$2"  # JSON 결과 출력 경로

cd "$PROJECT_DIR"

errors=()

# 1. TypeScript 타입체크
if ! npx tsc --noEmit 2>/tmp/ax-tsc.txt; then
    errors+=("typecheck")
fi

# 2. ESLint
if ! npx eslint --format json src/ > /tmp/ax-lint.json 2>&1; then
    errors+=("lint")
fi

# 3. Build
if ! npm run build 2>/tmp/ax-build.txt; then
    errors+=("build")
fi

# 결과 JSON 생성
if [ ${#errors[@]} -eq 0 ]; then
    echo '{"passed": true, "errors": []}' > "$RESULT_FILE"
    exit 0
else
    # 에러 상세를 JSON으로
    echo "{\"passed\": false, \"errors\": [\"${errors[*]}\"]}" > "$RESULT_FILE"
    exit 1
fi
```

주의: 프로젝트마다 lint/build 커맨드가 다를 수 있음. MVP에서는 Next.js(rubato) 기준으로 하드코딩해도 OK. 나중에 `.harness/config.json`으로 프로젝트별 커맨드 오버라이드.

## worker.py — Claude headless 호출

```python
import subprocess, json

def call_claude(prompt: str, output_schema_path: str | None = None) -> dict:
    """
    Claude CLI headless 호출.
    claude -p "프롬프트" --output-format json
    """
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        return {"error": result.stderr, "output": None}
    
    return json.loads(result.stdout)
```

### 코더 워커 프롬프트 조립

```python
def build_coder_prompt(
    agent_def: str,      # agents/coder.md 내용
    cps_content: str,     # CPS 또는 PRD 내용
    prev_errors: list,    # 이전 iteration 실패 에러 (있으면)
    project_context: str  # 프로젝트 구조/스택 요약
) -> str:
    prompt = f"""
{agent_def}

## 작업 컨텍스트

{project_context}

## 요구사항 (CPS/PRD)

{cps_content}

## 출력 형식

파일별 변경사항을 아래 JSON으로 출력:
```json
{{
  "files": [
    {{"path": "상대경로", "action": "create|modify|delete", "content": "전체 파일 내용"}}
  ],
  "summary": "변경 요약 1줄"
}}
```
"""
    if prev_errors:
        prompt += f"""
## 이전 시도 실패 원인 (반드시 수정)

{json.dumps(prev_errors, ensure_ascii=False, indent=2)}
"""
    return prompt
```

## agents/coder.md — 역할 정의

```markdown
# Coder

코드 생성 워커. CPS/PRD 스펙을 받아 구현 코드를 생성한다.

## 원칙

- 스펙에 명시된 범위만 구현. 추가 기능 금지.
- 기존 코드 패턴을 따른다. 새 패턴 도입 금지.
- 파일 경로는 프로젝트 루트 기준 상대경로.
- 하드코딩 금지 — 디자인 토큰, 텍스트 상수는 기존 시스템 경유.

## 출력

반드시 JSON 형식. files 배열에 변경할 파일 목록.
수정 시 파일 전체 내용을 content에 포함 (diff가 아닌 full file).
```

## harness/schemas/code_patch.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["files", "summary"],
  "properties": {
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "action", "content"],
        "properties": {
          "path": {"type": "string"},
          "action": {"enum": ["create", "modify", "delete"]},
          "content": {"type": "string"}
        }
      }
    },
    "summary": {"type": "string"}
  }
}
```

## status 커맨드

```bash
python orchestrator.py status --project ~/hq/projects/rubato
```

출력:
```
=== moomoo-ax status ===
Project: rubato
Phase 2 (Build):
  Iterations: 5 (3 keep / 2 discard)
  Best: build_003 (commit abc1234)
  Last gate: static ✓
  Tokens used: claude 24,500
```

`.harness/checkpoints/`와 `.harness/logs/`를 읽어서 집계.

## SKILL.md 내용

```markdown
# ax-loop

자율 제품 개발 루프. auto-research 패턴 기반.

## 사용법

### 전체 루프 실행
/ax run --project <경로> --max-iter <N>

### 상태 확인
/ax status --project <경로>

## 동작

1. CPS/PRD 파일을 읽음
2. Claude로 코드 생성
3. 정적 게이트(lint/typecheck/build) 실행
4. 통과 → keep(커밋), 실패 → discard(원복 + 에러 피드백)
5. max-iter까지 반복
6. 최종 best 체크포인트 출력
```

## 구현 순서 (권장)

1. **gate_static.sh** 먼저 — 가장 독립적. 단독 테스트 가능.
2. **worker.py** — Claude CLI 호출 + JSON 파싱. 단독 테스트 가능.
3. **orchestrator.py** — 위 둘을 엮는 루프. `run` + `status` 서브커맨드.
4. **agents/coder.md** + **harness/schemas/code_patch.json** — 파일 생성만.
5. **SKILL.md** — 스킬 진입점.

## 의존성

- Python 3.10+
- Claude CLI (`claude` 명령어 PATH에 있어야 함)
- Node.js + npm (대상 프로젝트의 lint/build용)
- git (커밋/원복용)

## MVP에서 안 하는 것

- Phase 0 (Define), Phase 1 (Plan), Phase 3 (Ship) — v0.2~v0.4
- 시각 게이트 (Playwright) — v0.3
- 구조 게이트 (ARIA) — v0.4
- Judge 게이트 (LLM 체크리스트) — v0.2
- 멀티모델 (Codex, Gemini) — v0.3+
- 동적 루브릭 생성 — v0.4
- Exploration/Exploitation rail — v0.3
- 대시보드 — meta-loop 이후
- `.harness/config.json` 프로젝트별 설정 — v0.2

## 테스트 방법

rubato 프로젝트에서 간단한 CPS 하나 만들고 돌려본다.

```bash
cd ~/hq/projects/moomoo-ax
python skills/ax-loop/scripts/orchestrator.py run \
  --project ~/hq/projects/rubato \
  --max-iter 3
```

성공 기준: 3회 iteration 돌고, keep/discard 판정이 로그에 남고, best 체크포인트가 생성되면 MVP 완료.
