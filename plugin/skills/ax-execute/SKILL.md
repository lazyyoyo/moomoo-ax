---
name: ax-execute
description: "team-ax 코드 구현 스킬 (codex 위임). 모든 워커의 공통 프로토콜 엔진 — inbox.md 과제 한 건 실행 + 파일 whitelist 가드 + TDD + backpressure + 영역 침범 가드 + result.json 출력. 단일 수동 실행과 ax-build 병렬 워커 양쪽의 진입점. Use when: ax-build 병렬 빌드 워커, codex execute, /ax-execute."
argument-hint: "<inbox.md 파일 경로>"
---

# /ax-execute

team-ax의 **코드 구현 + 워커 프로토콜 엔진**. inbox.md 과제 한 건을 실행하고 result.json을 내놓는 것이 전부다. 단일 수동 호출도, ax-build의 N개 병렬 워커도 같은 진입점.

> **역할 경계**
> - `/ax-build` = 오케스트레이터 (plan / inbox 생성 / 워커 스폰 / 폴링 / 커밋 / 머지)
> - `/ax-execute` = **한 태스크 실행** (워커 프로토콜 엔진)
> - `/ax-review code` = 검증 (read-only, codex 위임)
>
한 태스크 분량만 실행한다. 커밋은 lead(ax-build 오케스트레이터)가 일괄로 한다.

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | inbox.md 파일 경로 1개. inbox 안에 태스크 지시 + 파일 whitelist + result.json 저장 경로가 모두 들어있다 |
| **출력** | (1) 코드 변경 (uncommitted — 워커는 커밋하지 않는다), (2) `result.json` 파일 (스키마 고정) |

stdout은 보조 로그. lead가 공식적으로 읽는 것은 **result.json** 뿐.

## 인자 파싱

```
$ARGUMENTS = "<inbox.md 경로>"
```

- inbox.md 경로 필수. 단일 태스크 분량이어야 한다.
- `--allow` / `--block` 인자는 v0.7에서 쓰였으나 **v0.8에서 폐기**. whitelist는 inbox.md 내부에서 읽는다.

## 동작 순서

1. **inbox 파싱** — 태스크 ID / 제목 / 지시 / **파일 whitelist** / `result.json` 저장 경로 / (옵션)힌트
2. **필수 필드 검증** — 누락 시 `result.json.status = error` + notes에 사유 기록 후 즉시 종료
3. **컨텍스트 로딩** — inbox가 지시한 spec + 기존 코드만. 전체 리포 스캔 금지
4. **whitelist 사전 확인** — 허용 경로를 명시적으로 로그 출력. 이 밖의 파일은 편집하지 않음
5. **테스트 먼저 작성** (TDD) — 가능한 경우
6. **구현** — whitelist 안에서만
7. **backpressure** — `lint + typecheck + unit + build` 모두 통과 확인
8. **`git status` self-check** — `--porcelain` 결과를 whitelist와 대조. 범위 밖 변경 발견 시 `result.json.status = error` + notes에 해당 파일 목록
9. **result.json 작성** (아래 스키마 준수)
10. **종료** — 커밋/푸시 **금지**

## result.json 스키마

```json
{
  "task_id": "T1",
  "status": "done | blocked | error",
  "summary": "1-2 문장 한글",
  "files_touched": ["src/a.ts", "src/b.ts"],
  "notes": "optional — blocker 사유 / 발견한 버그 / 스펙 불일치 / 오너 개입 필요 등"
}
```

**status 의미:**

| 값 | 의미 |
|---|---|
| `done` | 태스크 완료. backpressure 통과. whitelist 안에서만 변경. |
| `blocked` | 외부 의존성 / 스펙 모호 / 오너 답변 필요 등 작업 진행 불가. `notes`에 사유. 변경분은 그대로 두고 종료(lead가 판단) |
| `error` | whitelist 위반 / 필수 필드 누락 / 복구 불가 에러. `notes`에 사유 |

**files_touched** — 실제로 수정/추가/삭제한 파일 전부. lead가 `git status --porcelain` 결과와 이 목록을 대조해 2중 가드.

## 워커 preamble (강제 문구)

워커는 다음을 **절대** 하지 않는다:

- NEVER spawn sub-agents / use Task tool — 이 세션 안에서만 작업
- NEVER run tmux orchestration — tmux는 lead가 관리
- NEVER `git commit` / `git push` — 커밋은 lead가 일괄
- NEVER edit files outside whitelist — 필요하면 blocked로 보고
- NEVER `git reset` / `git checkout -- ...` / `git stash` — 변경분을 임의로 되돌리지 않음 (lead/오너 판단)

## 영역 침범 가드 (필수)

rubato admin-v0.2.0 도그푸딩에서 발견된 사고 — 워커가 "작업 X만"이라는 지시를 받고도 TypeScript 타입 의존 등으로 인접 작업의 파일을 함께 수정해 다른 트랙의 변경분을 uncommitted로 남겼다.

본 스킬의 가드:

1. **whitelist 명시 의무** — inbox.md에 whitelist가 없으면 `status: error` + notes "whitelist 미명시"
2. **사전 인지** — 작업 시작 전 whitelist를 stdout에 출력
3. **사후 self-check** — 작업 완료 후 반드시 `git status --porcelain`을 whitelist와 대조
4. **침범 시** — `status: error` + notes에 범위 밖 변경 파일 목록 + **변경분은 되돌리지 않음**. lead/오너가 판단
5. **공유 파일 사전 처리 원칙** — 여러 태스크가 공유하는 파일(타입 정의 등)은 본 스킬에서 만지지 않음. ax-build 오케스트레이터의 **공통 기반 단계에서 미리 처리**되어야 함. 필요한데 처리 전이면 `status: blocked` + notes "공유 파일 미처리"

## 제약

1. **TDD** — 테스트 먼저 작성 → 구현 → 통과 확인
2. **placeholder/stub 금지** — 모든 기능 완전 구현. `// TODO: implement later` 금지
3. **텍스트 하드코딩 금지** — i18n/copy 경유
4. **보안 하드코딩 금지** — 키/토큰/시크릿은 환경 변수
5. **민감정보 로그 출력 금지**
6. **`.env` 파일 읽기 금지** — 변수명만 `.env.example`에서 확인
7. **backpressure** — lint + typecheck + unit + build 통과 전 `status: done` 금지
8. **커밋 금지** — lead가 담당 (v0.7 breaking change)
9. **DS 토큰만 사용** (FE 작업 시) — 하드코딩 색상/간격/폰트 금지
10. **발견한 버그** — 해결하거나 notes에 기록 (무시 금지)
11. **스펙 불일치** — 즉시 `status: blocked` + notes "스펙 불일치: <요지>"
12. **read-only 도구만 사용한 경우는 done 금지** — 코드 변경이 0건이면 `status: blocked` + notes "변경 없음 (이유 명시)"

## Failure Modes To Avoid

- **과잉 엔지니어링** — 불필요한 헬퍼/유틸/추상화. 직접 변경
- **범위 확장** — "여기 있는 동안" 인접 코드 수정. whitelist 가드로 차단됨
- **조기 완료** — 검증 전 `status: done` 선언. 항상 fresh 출력 확인
- **stub 남기기** — `// TODO: implement later`. 완전히 구현
- **임의 revert** — 침범을 되돌려 "깨끗하게" 만들기. 금지. 보고만

## 호출 예시

### ax-build 병렬 워커 (자동)

lead가 각 워커마다 다음과 같이 스폰:

```bash
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  -s workspace-write \
  '$ax-execute .ax/workers/T1/inbox.md'
```

모델은 codex CLI 기본값(`~/.codex/config.toml`의 `model`)을 사용. `AX_CODEX_MODEL` env 또는 orchestrator spawn 3번째 인자로 오버라이드 가능 (지정 시 `-c model=<값>` 주입).

### 단일 수동 호출

병렬 불필요한 단건 작업에 오너가 직접 호출:

```bash
codex exec '$ax-execute path/to/some-inbox.md'
```

동일 진입점. inbox 하나당 태스크 하나.

### Claude 세션에서 (슬래시 커맨드)

Claude 세션에 이 스킬이 캐시돼 있으면 `/ax-execute <inbox 경로>`로도 호출 가능. 내부 동작은 동일.

## inbox.md 필수 구조

inbox.md는 `plugin/skills/ax-build/templates/worker-inbox.md.tmpl` 포맷을 따른다. 최소 필드:

- **task_id** — 태스크 식별자
- **title** — 태스크 제목
- **instructions** — 구체 지시
- **whitelist** — 편집 허용 파일/디렉토리 글롭 목록
- **result_path** — `result.json` 저장 경로 (lead가 폴링)
- (옵션) **hints** — 참고 파일, 관련 spec, 기존 패턴

필수 필드 누락 시 워커는 즉시 `status: error`로 종료.

## Final Checklist

- [ ] inbox.md 필수 필드 전부 존재
- [ ] whitelist 안에서만 변경 (`git status --porcelain` 대조 완료)
- [ ] 테스트 먼저 작성 / 통과
- [ ] placeholder/stub 없는가?
- [ ] 텍스트/보안 하드코딩 없는가?
- [ ] lint + typecheck + unit + build 통과?
- [ ] **커밋/푸시 하지 않았는가?**
- [ ] result.json 작성 완료 (스키마 준수)
- [ ] files_touched가 실제 변경 파일과 일치

## 참조

- `../ax-build/SKILL.md` — 오케스트레이터 (lead 측 흐름)
- `../ax-build/templates/worker-inbox.md.tmpl` — inbox 포맷
- `../ax-build/references/backpressure-pattern.md` — backpressure 패턴
- `../ax-build/references/security-rules.md` — 보안 규칙
- `../ax-codex/SKILL.md` — codex 스킬 동기화 (`install` / `status`)
- `../ax-review/SKILL.md` — 검증 단계 (codex 위임, 작성 ≠ 검증)

## 설치

`/ax-codex install`로 `~/.codex/skills/ax-execute/`에 동기화하면 codex가 `$ax-execute`로 발견.

```bash
bash plugin/scripts/ax-codex.sh install
```
