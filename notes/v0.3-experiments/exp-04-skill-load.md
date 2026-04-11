# exp-04 — Plugin & Skill Load via `--plugin-dir`

- 날짜: 2026-04-11
- 축: 3 (하이브리드 loop 검증)
- claude CLI: v2.1.101

## 목표

`--plugin-dir` 로 로컬 플러그인을 자식 `claude -p` 세션에 로드하고, 그 플러그인의 스킬을 슬래시 호출로 실행할 수 있는가?

## 설계

2 단계:

1. **깨끗한 canary plugin** (`exp04-plugin`) 을 sandbox 에 생성 — skill 로드/호출 기초 검증
2. **실존 team-ax 플러그인** 을 로드 — moomoo-ax 자체 플러그인 인식 여부

### canary plugin 구조

```
notes/v0.3-experiments/sandbox/exp04-plugin/
├── .claude-plugin/plugin.json    # name: exp04, version: 0.0.1
└── skills/echo-test/SKILL.md     # canary 스킬
```

SKILL.md 본문은 단순:
```
When invoked, output exactly:
EXP04_CANARY_OK args=$ARGUMENTS
```

## 테스트 & 결과

### Test A — 슬래시 호출 + 인자

```bash
claude --plugin-dir .../exp04-plugin \
  -p "/exp04:echo-test alpha-bravo" \
  --output-format json --permission-mode acceptEdits
```

결과:
- `is_error: false`, `num_turns: 1`
- `result`: ```` ```\nEXP04_CANARY_OK args=alpha-bravo\n``` ````
- cost: $0.366

**관찰**:
- ✅ `--plugin-dir` 로 로컬 플러그인 로드 성공
- ✅ `-p` 모드에서 슬래시 명령 `/exp04:echo-test` 작동
- ✅ `$ARGUMENTS` 바인딩: `alpha-bravo` 그대로 주입
- ⚠️ Claude 가 출력을 자발적으로 코드 펜스로 감쌈 (SKILL.md 에 지시 없음) — 자연어 해석 편차 존재

### Test B — 슬래시 호출, 인자 없음

```bash
claude --plugin-dir .../exp04-plugin \
  -p "/exp04:echo-test" \
  --output-format json --permission-mode acceptEdits
```

결과:
- `num_turns: 1`, `result`: ```` ```\nEXP04_CANARY_OK args=\n``` ````
- cost: $0.313

**관찰**: 인자 없으면 `$ARGUMENTS` 가 빈 문자열로 바인딩. 에러 없이 진행.

### Test C — 실존 team-ax 플러그인 로드 인식

```bash
claude --plugin-dir /Users/sunha/hq/projects/moomoo-ax/plugin \
  -p "Without invoking any skill, list all the skills you can see from the team-ax plugin. Return ONLY a JSON array of skill names." \
  --output-format json --permission-mode acceptEdits
```

결과:
- `num_turns: 1`
- `result`: `["ax-feedback","ax-implement"]`
- cost: $0.312

**관찰**:
- ✅ team-ax 플러그인이 `--plugin-dir plugin` 로 인식됨
- ✅ `SKILL.md` 가 있는 2개 스킬만 노출 (ax-feedback, ax-implement)
- ✅ `.gitkeep` 만 있는 빈 스킬 디렉토리 (ax-init/ax-design/ax-qa/ax-deploy/ax-autopilot) 는 자동 제외
- ⚠️ `.archive/ax-define` 도 제외 — `.archive/` prefix 가 skipped 되는지 별도 확인 필요 (부차적)

## 핵심 발견

### 1. `--plugin-dir` 는 실 동작한다

- 로컬 플러그인 (install 없이) 을 자식 세션에 세션 전용으로 로드
- `.claude-plugin/plugin.json` 의 `name` 이 네임스페이스 prefix (`exp04:`, `team-ax:`)
- SKILL.md 파일이 존재하는 스킬만 노출

### 2. `-p` 모드에서 슬래시 명령이 작동한다

```
-p "/plugin:skill-name arg1 arg2"
```

이 형태로 자식 세션에 즉시 스킬 invoke 가능. `num_turns: 1` 로 inline 로드 (별도 tool call turn 생성 안 함).

### 3. `$ARGUMENTS` 가 정상 바인딩

인자 있으면 그대로, 없으면 빈 문자열. `skill.md` 의 규약대로.

### 4. 자연어 해석 편차는 여전히 존재

SKILL.md 에 "코드 펜스로 감싸지 마라" 를 명시 안 하면, Claude 가 자체 판단으로 감쌈. **Progressive Codification 의 필요성을 재확인** — 자연어 rule 은 항상 해석 편차를 낳는다. deterministic 출력이 필요하면 스킬 본문에서 Bash 스크립트로 직접 출력 강제.

## 판정

**exp-04: ✅ 완전 성공**

v0.3 Path A (하이브리드: Python 하네스 + `--plugin-dir team-ax` + 자식 `claude -p` 에 슬래시 호출) 의 **핵심 빌딩 블록이 작동함**.

levelup loop 의 iteration 을 다음 형태로 작성 가능:

```python
subprocess.run([
  "claude", "-p", f"/team-ax:ax-implement {target} {iter_num}",
  "--plugin-dir", "plugin",
  "--allowedTools", "Read", "Write", "Edit", "Bash", "Grep", "Glob",
  "--permission-mode", "acceptEdits",
  "--output-format", "json",
])
```

이전 Python 래퍼의 단점(프롬프트 안에 모든 인스트럭션 삽입 + skill 파일 내용 수동 load)이 전부 제거됨.

## 결과 파일

- `sandbox/exp04-plugin/.claude-plugin/plugin.json`
- `sandbox/exp04-plugin/skills/echo-test/SKILL.md`
- `sandbox/exp04-testA-slash.json`
- `sandbox/exp04-testB-noargs.json`
- `sandbox/exp04-testC-teamax.json`

## 함의 (v0.3 재설계)

1. **plugin-dir 이 있으므로 team-ax 를 `.claude/` 에 설치하지 않아도 된다** — 개발 중인 team-ax 를 자식 세션에 매 iter 주입 가능. `/reload-plugins` 도 필요 없음 (매번 새 자식 세션).
2. **Progressive Codification 실현 가능**: SKILL.md 본문에 `` !`script.py` `` 로 deterministic 스크립트 실행 + `allowed-tools: Bash(scripts/*)` 로 permission 명시 → 자연어 해석 없이 rule 강제.
3. 다만 **SKILL.md 의 자연어 지시는 여전히 해석 편차를 낳는다** (Test A 의 코드 펜스). rubric/hard constraint 는 스크립트로 빼야 재현성 확보.
