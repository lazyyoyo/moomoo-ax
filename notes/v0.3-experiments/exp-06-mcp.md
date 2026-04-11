# exp-06 — MCP Server in Child `claude -p` Session

- 날짜: 2026-04-11
- 축: 3
- claude CLI: v2.1.101

## 목표

부모 Claude Code 세션에 연결된 MCP 서버 (Playwright 등) 를 자식 `claude -p` 세션이 **실제로 호출**할 수 있는가?

exp-05 에서 `init` event 의 `mcp_servers` 배열에 Playwright 가 `status: "connected"` 상태로 나타남을 확인 — 그러나 connected ≠ callable. 이 실험은 실 호출을 검증.

## 설계

가장 가벼운 2-step Playwright 시나리오: about:blank 로 navigate 후 close.

```bash
claude -p "Use the MCP tool mcp__plugin_playwright_playwright__browser_navigate to navigate to the URL about:blank. After the navigation, use mcp__plugin_playwright_playwright__browser_close to close the browser. Then output exactly the single line: MCP_PLAYWRIGHT_OK" \
  --allowedTools mcp__plugin_playwright_playwright__browser_navigate mcp__plugin_playwright_playwright__browser_close \
  --permission-mode acceptEdits \
  --output-format json
```

**설계 포인트**:
- `--allowedTools` 에 MCP tool 전체 이름을 공백 구분으로 나열
- about:blank → browser 팝업 없이 안전
- 즉시 close → browser 리소스 누수 방지

## 결과

```json
{
  "is_error": false,
  "num_turns": 4,
  "result": "MCP_PLAYWRIGHT_OK",
  "duration_ms": 21285,
  "duration_api_ms": 19353,
  "total_cost_usd": 0.5940,
  "permission_denials": [],
  "modelUsage": {
    "claude-opus-4-6[1m]": { "inputTokens":14, "outputTokens":354, "cacheReadInputTokens":75169, "cacheCreationInputTokens":74726, "costUSD": 0.5135 }
  }
}
```

## 관찰

### 1. MCP tool 실 호출 성공

- `num_turns: 4` → (tool_use navigate) + (tool_result) + (tool_use close) + (tool_result) + text reply. MCP tool loop 가 한 subprocess 안에서 완료.
- `result: "MCP_PLAYWRIGHT_OK"` — 프롬프트 지시 그대로 정확히 반환.
- `permission_denials: []` — `--allowedTools` 에 명시된 두 MCP tool 이 permission 없이 통과.

### 2. MCP tool 이 `--allowedTools` 에 그대로 들어간다

```
--allowedTools mcp__plugin_playwright_playwright__browser_navigate \
               mcp__plugin_playwright_playwright__browser_close
```

공백 구분, full name, 와일드카드 없이 — 작동. 여러 tool 을 반복 지정 가능. 패턴 `mcp__plugin_playwright_playwright__*` 은 이 실험에서 시도 안 함 — 별도 확인 필요.

### 3. 비용 구조

- **$0.594** — 이번 세션 중 가장 비쌌다. 이전 Read/Write 테스트 $0.33 대비 약 1.8배
- 원인: MCP tool 스키마 로드로 `cache_creation_input_tokens: 74726` (이전 37K의 2배)
- Playwright 는 MCP tool 이 20개 넘어 스키마가 크다. **MCP 를 많이 쓰는 자식 세션은 cache creation 토큰이 누적** → levelup loop 에서 ax-qa iter 당 $0.5 이상 상한 고려

### 4. duration

- `duration_ms: 21285` vs `duration_api_ms: 19353` — 차이 2초 (spawn + MCP 서버 준비 오버헤드)
- exp-01 Test 2 (Read 만) 의 10초 대비 2배. browser launch 가 추가 5~8초 소요 추정

## 핵심 발견

### 1. 자식 `claude -p` 에서 MCP tool 실 호출 가능 (확정)

**v0.2 F 의 핵심 가설 "Playwright/axe/Lighthouse 는 `claude -p` 자식에서 못 쓴다" 는 완전히 반박됨**.

- MCP 서버는 자식 세션이 자기 설정 체인으로 자동 로드 (exp-05 init event)
- MCP tool 은 `--allowedTools` 로 명시하면 permission 통과
- 실 호출 결과가 응답에 반영됨

### 2. MCP 사용은 비용 배수를 만든다

MCP tool 스키마 로드 = cache creation 토큰 1.5~2 배. levelup loop 관점에서 MCP 를 많이 쓰는 stage (ax-qa) 는 다른 stage 대비 iter 당 50~80% 더 비싸다. rubric 설계 시 반영.

### 3. 자식 MCP 서버는 독립 프로세스

이건 exp-06 에서 직접 증명한 건 아니지만 추론: 자식 `claude -p` 가 독립 subprocess 이므로 Playwright MCP 도 새로 spawn. 부모와 browser 인스턴스 공유 안 됨 (각 자식이 자기 browser 를 띄움).

**함의**: 병렬 자식 여러 개가 각자 MCP 를 띄우면 Playwright browser 인스턴스가 N개 동시 생성 → 시스템 리소스 부담. levelup loop 의 parallel 설계 시 상한 필요.

## 판정

**exp-06: ✅ 완전 성공**

ax-qa 의 구조적 재설계가 **불필요**. 다음 조합이면 ax-qa 가 Playwright/axe-core/Lighthouse 를 그대로 쓸 수 있다:

```python
subprocess.run([
  "claude", "-p", f"/team-ax:ax-qa {target} {fixture}",
  "--plugin-dir", "plugin",
  "--allowedTools",
    "Read", "Write", "Bash",
    "mcp__plugin_playwright_playwright__browser_navigate",
    "mcp__plugin_playwright_playwright__browser_snapshot",
    "mcp__plugin_playwright_playwright__browser_click",
    # ... 필요한 MCP tool 추가
  "--permission-mode", "acceptEdits",
  "--output-format", "stream-json", "--verbose",
])
```

## 결과 파일

- `sandbox/exp06-mcp-playwright.json`

## 함의 (v0.3 재설계)

1. **ax-qa 재설계 불필요** — v0.2 F 의 가장 큰 우려였는데, 플래그 두 개 추가로 해결.
2. **cost 모델링**: MCP-heavy 스킬은 1.5~2배 baseline cost. rubric 설정 시 threshold 조정 필요 (early stop 비용 민감도).
3. **병렬 ax-qa 제약**: 동시 N 개 자식이 각자 browser 띄우면 메모리 폭발. parallel cap = 2~3.
4. **MCP tool 이름 재현성**: `mcp__<plugin-name>__<server-name>__<tool-name>` 형식이 플러그인 버전에 따라 바뀔 수 있음 — team-ax 가 Playwright 를 직접 내장하지 않고 user MCP 에 의존하면 환경 간 이식성 문제. **team-ax 플러그인 내장 MCP 고려** (plugin.md 의 plugin 내장 MCP 섹션 참조).
