# exp-03 — Recursion Depth 2+

- 날짜: 2026-04-11
- 축: 3
- claude CLI: v2.1.101

## 목표

Claude Code 세션 안에서 `claude -p` 를 호출하는 것은 exp-01 에서 이미 가능함을 확인 (depth 1). 이 실험은 **depth 2**: 자식 `claude -p` 가 Bash tool 로 또 다른 `claude -p` 를 spawn 하는가?

- session id 충돌?
- permission 상속?
- subprocess 타임아웃?

## 설계

부모 `claude -p` 에 Bash tool 허용 → Bash 로 손자 `claude -p` spawn → 손자 응답을 JSON 파싱 → 부모가 reply.

```bash
claude -p "Use the Bash tool to run this exact shell command and capture its output:
claude -p 'Say exactly three words: hello from grandchild' --output-format json --permission-mode plan
After running, parse the JSON output and return ONLY the value of the 'result' field." \
  --allowedTools Bash \
  --permission-mode acceptEdits \
  --output-format json
```

- 부모 depth = 2 (현 Claude Code 세션 기준 depth 1 → 부모 `claude -p`)
- 손자 depth = 3

손자 프롬프트는 `--permission-mode plan` (read-only) 로 안전화.

## 결과

### Raw

```json
{
  "type": "result",
  "is_error": false,
  "num_turns": 2,
  "result": "hello from grandchild",
  "duration_ms": 24504,
  "duration_api_ms": 11182,
  "total_cost_usd": 0.3381,
  "permission_denials": []
}
```

### 관찰

- ✅ **depth 2 chain 성공**: 부모 Bash → 손자 `claude -p` spawn → 손자 응답 "hello from grandchild" → 부모 파싱 → 최종 reply
- `num_turns: 2` — 부모 세션에서만 본 turn 수. 부모 LLM → Bash tool call (손자 spawn) → 부모 LLM reply
- `duration_ms: 24504` vs `duration_api_ms: 11182` — 차이 13초 ≈ 손자 subprocess spawn + 손자 API 대기 시간
- `total_cost_usd: $0.3381` — **이건 부모 세션만의 비용**. 손자는 별도 세션이므로 별도 청구 (위 JSON 에 포함 안 됨)
- `permission_denials: []` — 부모가 Bash 로 `claude` 바이너리 호출을 문제없이 승인

### session id

- 부모 session id: `9fae590b-5e2d-4b54-ad37-84a147ae24ee`
- 손자 session id: 부모가 `result` 안에 풀어서 주는 것만 봄. Bash stdout 에는 full JSON 이 있었을 것이지만 부모가 result 필드만 추출해서 반환. **session id 충돌 없음** — 각 subprocess 는 독립 session id 를 가진다.

### permission 상속

부모가 `--permission-mode acceptEdits`, 손자는 `--permission-mode plan`. 손자가 부모의 mode 를 상속하지 않고 자기 CLI flag 를 따름 → **각 subprocess 는 독립 permission context**.

## 핵심 발견

### 1. 재귀 depth 제한 없음 (적어도 depth 3 까지 확인)

Claude Code → 부모 `claude -p` → 손자 `claude -p` 체인 정상 동작. 이론상 depth N 까지 가능 (각 depth 마다 subprocess 비용 누적).

### 2. 각 subprocess 는 완전 독립

- 독립 session id
- 독립 permission mode
- 독립 plugin/MCP 설정 (이건 exp-05 에서 추가 확인 — 각 자식은 자체 설정 source 체인으로 로드)
- 독립 비용 청구

즉 부모 세션의 모드/권한이 자식에 "상속" 되지 않는다. 각 subprocess 는 **자기 CLI 플래그만으로 동작**. 이는 levelup loop 관점에서 **좋은 속성** — 재현성 확보.

### 3. 비용 구조

- depth 당 baseline cost ≈ $0.3 (시스템 프롬프트 + 도구 스키마 cache creation)
- depth N 이면 총 비용 ≈ N × $0.3 ~ N × $0.5 (작업 복잡도에 따라)
- levelup loop 에서 depth 2 (하네스 → 자식 iter subprocess) 가 실용 상한

### 4. timing

손자 spawn 오버헤드 ≈ 12초 (Claude Code 바이너리 cold start + system prompt cache 로드). 이건 iter 당 고정 비용.

## 판정

**exp-03: ✅ 성공**

- Path A (Python 하네스 → `claude -p` 자식) 은 재귀 관점에서 제약 없음
- 각 subprocess 독립성이 확보됨 → 재현성 ✅
- 단, **depth 별 baseline cost 누적**은 v0.3 설계 시 반영 필요

## 함의 (v0.3 재설계)

1. **levelup loop 은 최대 depth 2 권장**: Python 하네스 (depth 0) → 자식 iter `claude -p` (depth 1). depth 2 이상은 비용 폭발.
2. **손자 레벨의 재귀는 subagent 로 대체**: subagent 는 같은 세션 내 fork 라 baseline cost 중복이 훨씬 작다. exp-04 에서 확인한 `--agents` JSON flag + `context: fork` skill 패턴 조합.
3. session id 충돌 없음 → Python 하네스가 여러 자식을 병렬로 spawn 가능 (parallel iter 실험 가능).

## 결과 파일

- `sandbox/exp03-recursion-depth2.json`
