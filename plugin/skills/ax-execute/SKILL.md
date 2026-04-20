---
name: ax-execute
description: "team-ax 코드 구현 스킬 (codex 위임 가능). TDD + backpressure + 태스크 단위 커밋 + 영역 침범 가드. ax-build 3단계에서 executor.engine=codex 토글 시 호출. Use when: ax-build 코드 구현, codex execute, $ax-execute."
argument-hint: "<task-spec 파일 경로> [--allow <파일|디렉토리>] [--block <파일|디렉토리>]"
---

# /ax-execute (또는 codex `$ax-execute`)

team-ax의 **코드 구현** 단계를 떼어낸 스킬. 작성 엔진이 claude이든 codex이든 동일한 규칙/가드 아래 동작하도록 분리.

> **역할 경계**
> - `/ax-build` = 오케스트레이터 (plan / 공통 기반 / 워크트리 / 머지)
> - `/ax-execute` = **코드 구현만** (한 태스크 분량)
> - `/ax-review code` = 검증 (read-only, codex 위임)

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | 태스크 명세 파일(`.ax-brief.md` 또는 `versions/vX.Y.Z/build-plan.md`의 한 태스크), 허용/차단 파일 경로, 관련 spec, 기존 코드 |
| **출력** | 변경된 코드 + 테스트 + 태스크 단위 git 커밋 + stdout 결과 요약(첫 줄 `DONE` 또는 `BLOCKED: {이유}`) |

## 인자 파싱

```
$ARGUMENTS = "<task-spec 경로> [--allow <경로>...] [--block <경로>...]"
```

- `task-spec 경로` 필수. 단일 태스크 분량이어야 함 (여러 태스크 한꺼번에 X).
- `--allow`: 변경 허용 파일/디렉토리 목록 (글롭 가능). 누락 시 task-spec에 명시된 영역만.
- `--block`: 명시적 차단 파일/디렉토리. allow보다 우선.

## 동작 순서

1. **task-spec 파싱** — 현재 태스크 / 관련 spec / 허용·차단 영역 / DoD 추출
2. **컨텍스트 로딩** — 관련 spec + 기존 코드만 (전체 리포 스캔 금지)
3. **차단 파일 사전 확인** — `--block` + spec에 명시된 침범 금지 영역 인지
4. **테스트 먼저 작성** (TDD)
5. **구현** — 허용 영역 안에서만
6. **backpressure** — `lint + typecheck + unit + build` 모두 통과 확인
7. **`git status` self-check** — 차단 영역 변경분 발견 시 즉시 중단 + `BLOCKED` 보고
8. **태스크 단위 커밋** — `feat(<task>): ...` 또는 task-spec 지정 메시지
9. **stdout 결과 요약**:
   ```
   DONE
   - changed: <files>
   - commit: <sha> "<msg>"
   - tests: <added/passed>
   - notes: <bug/스펙 불일치 발견 시 한 줄>
   ```
   또는
   ```
   BLOCKED: <한 줄 이유>
   - {차단 사유 / 미해결 의존 / 스펙 모호 등}
   ```

## 영역 침범 가드 (필수)

rubato admin-v0.2.0 도그푸딩에서 발견된 사고 — executor가 "작업 X만"이라는 지시를 받고도 **TypeScript 타입 의존 등으로 인접 작업의 파일을 함께 수정**해 다른 트랙의 변경분을 uncommitted로 남김.

이를 막기 위해 본 스킬은:

1. **차단 파일 경로 명시 의무** — task-spec / `--block` 인자에 차단 경로가 없으면 수행 거부 (`BLOCKED: 차단 영역 미명시`).
2. **변경 전 사전 인지** — 작업 시작 전 차단 영역을 명시적으로 출력.
3. **사후 self-check** — 작업 완료 후 반드시 `git status --porcelain` 결과를 차단 경로와 대조.
4. **침범 시 즉시 중단** — 차단 영역에 변경 발견되면 작업을 커밋하지 않고 `BLOCKED: 영역 침범` 보고. 변경된 파일을 **임의로 되돌리지 않음** (오너가 결정).
5. **공유 파일 사전 처리 원칙** — 여러 태스크가 공유하는 파일(타입 정의 등)은 본 스킬에서 만지지 않음. ax-build 오케스트레이터의 **공통 기반 단계에서 미리 처리**되어야 함. 그렇지 않으면 `BLOCKED: 공유 파일 미처리`.

## 제약

1. **TDD** — 테스트 먼저 작성 → 구현 → 통과 확인.
2. **placeholder/stub 금지** — 모든 기능 완전 구현. `// TODO: implement later` 금지.
3. **텍스트 하드코딩 금지** — i18n/copy 경유.
4. **보안 하드코딩 금지** — 키/토큰/시크릿은 환경 변수.
5. **민감정보 로그 출력 금지**.
6. **`.env` 파일 읽기 금지** — 변수명만 `.env.example`에서 확인.
7. **backpressure** — lint + typecheck + unit + build 통과 전 다음 태스크 금지.
8. **태스크 완료 = 커밋** — 커밋 없이 종료 금지.
9. **DS 토큰만 사용** (FE 작업 시) — 하드코딩 색상/간격/폰트 금지.
10. **발견한 버그** — 해결하거나 stdout `notes`에 기록 (무시 금지).
11. **스펙 불일치** — 즉시 `BLOCKED: 스펙 불일치` 보고.
12. **read-only 도구만 사용한 경우는 DONE 금지** — 코드 변경이 0건이면 `BLOCKED: 변경 없음 (이유 명시)` 보고.

## Failure Modes To Avoid

- **과잉 엔지니어링** — 불필요한 헬퍼/유틸/추상화. 직접 변경.
- **범위 확장** — "여기 있는 동안" 인접 코드 수정. 차단 영역 가드로 차단됨.
- **조기 완료** — 검증 전 "DONE" 선언. 항상 fresh 출력 확인.
- **stub 남기기** — `// TODO: implement later`. 완전히 구현.

## 호출 예시

### codex에서 직접 (executor.engine=codex)

```bash
codex exec '$ax-execute .claude/worktrees/work-a/.ax-brief.md --allow src/admin/timeseries/ --block src/admin/users/'
```

### Claude executor 에이전트가 동일 규칙 적용 (executor.engine=claude)

`plugin/agents/executor.md`도 본 스킬과 동일 제약/가드를 따름. ax-build 3단계가 `executor.engine` 값에 따라 둘 중 하나를 호출.

## Final Checklist

- [ ] task-spec / 차단 영역 명시 확인
- [ ] 테스트 먼저 작성
- [ ] 변경이 허용 영역 안에만 있는가? (`git status` self-check)
- [ ] placeholder/stub 없는가?
- [ ] 텍스트/보안 하드코딩 없는가?
- [ ] lint + typecheck + unit + build 통과?
- [ ] 태스크 단위 커밋 완료?
- [ ] stdout 첫 줄이 `DONE` 또는 `BLOCKED: {이유}` 인가?

## 참조

- `../ax-build/SKILL.md` — 오케스트레이터 (engine 토글)
- `../ax-build/references/backpressure-pattern.md` — backpressure 패턴
- `../ax-build/references/security-rules.md` — 보안 규칙
- `../../agents/executor.md` — claude 분기 에이전트 (동일 규칙)
- `../ax-review/SKILL.md` — 검증 단계 (codex 위임, 작성 ≠ 검증)
- `../ax-codex/SKILL.md` — codex 스킬 동기화 (`install` / `status`)

## 설치

`/ax-codex install`로 `~/.codex/skills/ax-execute/`에 동기화하면 codex가 `$ax-execute`로 발견.

```bash
bash plugin/scripts/ax-codex.sh install
```
