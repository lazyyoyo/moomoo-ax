# exp-01 — Echo (minimum Read tool call)

- 날짜: 2026-04-11
- 축: 3 (하이브리드 loop 가능성 검증)
- claude CLI: v2.1.101
- 실행 환경: moomoo-ax 프로젝트 Claude Code 세션 안에서 `Bash` 툴로 자식 `claude -p` 호출 (즉 exp-03 recursion 의 preflight 겸함)

## 목표

Python subprocess 가 `claude -p` 를 호출해서 **실제 Read tool call 을 수행**하게 할 수 있는가? 즉 `claude -p` 가 single-shot LLM 호출이 아니라 tool loop 를 돌릴 수 있는가?

## 설계

3개 테스트를 순차 실행:

| # | 목적 | 플래그 | 프롬프트 |
|---|---|---|---|
| 1 | Control (tool 없이 응답) | `--output-format json --permission-mode plan` | "Say exactly: hello world from child" |
| 2 | Read tool | `--output-format json --allowedTools Read --permission-mode acceptEdits` | "Read sandbox/fixture.txt and output the third line exactly" |
| 3 | Write + Read 연쇄 | `--output-format json --allowedTools Read Write --permission-mode acceptEdits` | "Write a new file with content X, then Read it back and echo" |

fixture:
```
hello from fixture
line 2: moomoo-ax v0.3 exp-01
line 3: the secret word is "levelup"
```

## 결과

### Test 1 — Control

- `is_error: false`, `stop_reason: end_turn`, `num_turns: 1`
- `result`: `"hello world from child"` ✅
- `duration_ms`: 16435
- `total_cost_usd`: 0.3907
- `usage.cache_creation_input_tokens`: 38572 (system prompt + tool def)
- `modelUsage`: Opus 4.6 (126 in/9 out) + **Haiku 4.5 가 보조 모델로 함께 호출됨** (16 in/510 out) — 추정: background classifier/summarizer
- `permission_denials`: []

**관찰**: 아무 tool 을 쓰지 않아도 38K cache creation — system prompt + tool schema 가 기본 로드된다. 호출당 baseline 비용 $0.24 ~ $0.39.

### Test 2 — Read

- `is_error: false`, `stop_reason: end_turn`, **`num_turns: 2`**
- `result`: `"line 3: the secret word is \"levelup\""` ✅ (파일 내용 정확)
- `duration_ms`: 10873
- `total_cost_usd`: 0.3337
- `permission_denials`: []

**관찰**: `num_turns` 가 1 → 2 로 증가 = Read tool call 이 한 바퀴 돌았다. `result` 가 fixture 의 정확한 3번째 줄과 일치 → **Read tool 이 실제 실행되고 내용이 응답에 반영됨**.

### Test 3 — Write + Read

- `is_error: false`, `stop_reason: end_turn`, **`num_turns: 3`**
- `result`: `"파일 내용: 'written by child claude session, exp-01 test 3'"` ✅
- 디스크 확인: `notes/v0.3-experiments/sandbox/exp01-child-wrote.txt` **실제 생성됨** (46 bytes, 내용 일치)
- `total_cost_usd`: 0.3590
- `permission_denials`: []

**관찰**: Write → Read → reply 의 3-step tool loop 가 한 subprocess 안에서 완전히 수행되고, 변경이 디스크에 persist 됨.

## 핵심 발견

### 1. `claude -p` 는 tool loop 이다 (조건부)

`--allowedTools` + `--permission-mode acceptEdits` 가 주어지면, `-p` 모드에서도 **Read / Write / (추정) Bash / Edit / Grep / Glob 가 실제로 실행되는 multi-turn 루프** 를 돌린다.

v0.2 F 의 관찰 ("`claude -p` one-shot 은 tool 접근 불가") 은 **플래그 누락에 의한 조건부 오판**. tool 이 차단된 게 아니라, **플래그 없이 호출하면 `-p` 기본 모드가 permission 거부로 tool 을 막는 것**.

### 2. `src/claude.py` 는 플래그를 안 쓰고 있었다

`src/claude.py:38`:
```python
["claude", "-p", prompt, "--output-format", output_format]
```

`--allowedTools`, `--permission-mode` 전무. 그래서 v0.1/v0.2 의 모든 levelup 호출은 사실상 text-generation-only 모드였다.

**fix 는 1~2 줄**:
```python
["claude", "-p", prompt,
 "--output-format", output_format,
 "--permission-mode", "acceptEdits",
 "--allowedTools", "Read", "Write", "Edit", "Grep", "Glob", "Bash"]
```

### 3. JSON output 스키마 (exp-05 선행 답)

`--output-format json` 반환 구조 (확인된 필드):

```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "duration_ms": ...,
  "duration_api_ms": ...,
  "num_turns": ...,              // tool loop 횟수 지표
  "result": "...",               // 최종 assistant message
  "stop_reason": "end_turn|...",
  "session_id": "uuid",
  "total_cost_usd": ...,
  "usage": {
    "input_tokens", "output_tokens",
    "cache_creation_input_tokens", "cache_read_input_tokens",
    "server_tool_use": { "web_search_requests", "web_fetch_requests" },
    "service_tier", "cache_creation": {...},
    "iterations": [...],
    "speed": "standard"
  },
  "modelUsage": {
    "claude-opus-4-6[1m]": {..., "costUSD": ..., "contextWindow": 1000000},
    "claude-haiku-4-5-20251001": {..., "costUSD": ...}
  },
  "permission_denials": [],      // deny 당한 tool call 기록
  "terminal_reason": "completed",
  "fast_mode_state": "off",
  "uuid": "..."
}
```

미확인 필드:
- tool_use 배열 (per-turn tool call log) 은 `json` 형식에선 안 나옴. **stream-json** 에서 나올 것으로 추정 → exp-05 에서 검증.
- 개별 tool 의 input/output 은 result 안에 섞여서만 보임.

### 4. 재귀 호출 가능 (exp-03 preflight)

이 실험 자체가 Claude Code 세션 **안에서** Bash 로 자식 `claude -p` 를 호출한 것. 3번 모두 성공 → **recursion depth 1 까지는 확실히 가능**. session id 는 독립, permission 은 별도 계산됨 (parent bypassPermissions 영향 없음 — 자식은 명시 플래그로 permission 모드 지정).

exp-03 의 본 검증 (2 depth 이상, session id 충돌) 은 별도 실험 필요.

### 5. 비용 구조

- 호출당 baseline: **$0.24 ~ $0.39** (Opus 4.6)
- 38K cache creation 이 기본으로 박힘 → 반복 호출 시 cache read 로 줄어들 수 있지만 자식 세션이 독립이면 cache 가 재활용 안 될 수 있음
- **Haiku 4.5 보조 모델**: 모든 호출에 $0.08 ~ $0.15 추가 (background classifier 로 추정)
- levelup loop 이 iteration 마다 자식 세션 띄우면 **iter 당 $0.4 ~ $0.5** 상한 고려. v0.3 cost 설계에 반영 필수.

## 결과 파일

- `sandbox/fixture.txt` — 테스트 입력
- `sandbox/exp01-test1-control.json` — Test 1 raw output
- `sandbox/exp01-test2-read.json` — Test 2 raw output
- `sandbox/exp01-test3-write.json` — Test 3 raw output
- `sandbox/exp01-child-wrote.txt` — 자식 세션이 실제 생성한 파일

## 판정

**exp-01: ✅ 성공 (조건부)**

`claude -p` + `--allowedTools` + `--permission-mode acceptEdits` 조합이면 subprocess 에서 실제 tool loop 가 돈다. 이는 v0.3 하이브리드 Path A (Python 하네스 + 자식 세션 tool loop) 의 **핵심 전제를 통과**시킨다.

단, 이것만으로는 다음이 보장되지 않음 — 별도 실험 필요:

| 미확인 | 이월 실험 |
|---|---|
| Plugin/Skill 이 자식 세션에 로드되나 | exp-04-skill-load |
| 부모 MCP 상속 or 자식 MCP 로드 | exp-06-mcp |
| recursion depth 2+ | exp-03-recursion |
| stream-json 의 per-tool log 구조 | exp-05-cost-tracking |
| `--agents` JSON 으로 ad-hoc subagent 정의 | (exp-02 확장) |

## 함의 (v0.3 재설계 힌트)

1. **v0.2 F 의 "Python one-shot ≠ tool loop" 는 오판이었다**. levelup loop 의 **전면 재설계는 불필요할 수 있다**. `src/claude.py` 에 플래그만 추가해도 v0.2 E 의 Test (SKILL.md 압축 iteration) 가 실제 tool 을 쓰면서 돌았을 가능성이 크다.
2. 다만 **"자연어 압축 ≠ codification"** (결함 1) 은 여전히 유효. 이건 tool loop 유무와 독립된 문제.
3. **Path A 의 존재 가능성은 거의 확정**. 이제 물어야 할 것: "전면 Python 하네스 유지 + `--allowedTools` 추가" vs "team-ax 플러그인 내에서 Skill + Hook 로 loop 를 encapsulate" 중 어느 쪽이 Progressive Codification 을 더 잘 실현하는가.
4. **비용 구조** 는 iter 당 baseline $0.4 이상. v0.3 에서 max-iter 3 + threshold 0.95 기본값이면 iter 당 $0.4 × 3 = $1.2/run. rubato 의 한 기능당 run 비용으로는 acceptable.

## 다음 액션

1. `exp-02-stateful.md` — 더 복잡한 multi-file stateful task (이미 Test 3 에서 일부 검증됨, 더 확장)
2. `exp-03-recursion.md` — depth 2 재귀 (자식이 또 자식을 호출)
3. `exp-04-skill-load.md` — `claude --plugin-dir plugin -p "/team-ax:ax-implement ..."` 로 team-ax 스킬을 자식 세션에 로드 가능한지
4. **`src/claude.py` 수정 PoC**: 플래그 추가 후 v0.2 E 의 `labs/ax-implement` 재실행 → 결과 비교 (단, v0.3 리서치 끝날 때까지 **본 수정은 금지** 원칙 유지. PoC 는 별도 브랜치에서)
5. v0.2 F 의 "ax-qa 재설계 필수" 가정을 재검토: Playwright MCP 는 여전히 상속/로드 이슈가 별개 (exp-06)
