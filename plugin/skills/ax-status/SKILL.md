---
name: ax-status
description: "team-ax statusline 설치/토글/상태 확인 스킬. 글로벌 ~/.claude/settings.json statusLine 교체 + 토글 키 관리. Use when: /ax-status, statusline 설정, statusline 토글, statusline 끄기/켜기, ctx/5h/7d 표시, 다른 PC에 statusline 적용."
---

# /ax-status

team-ax statusline의 설치/토글/상태 확인 스킬. **글로벌** `~/.claude/settings.json`의 `statusLine.command`를 team-ax 래퍼로 교체하고, 행별 토글(ctx/5h/7d/branch)을 관리한다.

> **역할 경계**
> - statusline 자체 렌더는 `plugin/scripts/ax-statusline.sh`가 담당
> - quota 캐시는 `plugin/scripts/fetch-usage.sh`가 담당
> - 이 스킬은 **설치/토글/관찰**만 담당 (렌더 아님)

## 입력 / 출력

| 구분 | 내용 |
|---|---|
| **입력** | 서브커맨드 (`install` / `uninstall` / `toggle <key>` / `on` / `off` / `show`) |
| **출력** | `~/.claude/settings.json` 변경 (백업 자동 생성), `~/.claude/hud/ax-statusline.sh` 래퍼 생성/제거, 상태 출력 |

## 동작 — 단일 진입점

모든 서브커맨드는 `plugin/scripts/ax-status.sh`로 위임한다.

```bash
bash plugin/scripts/ax-status.sh <subcommand> [args]
```

team-ax 플러그인이 cache에 설치된 상태라면 직접:

```bash
bash ~/.claude/plugins/cache/<owner>/team-ax/<version>/scripts/ax-status.sh <subcommand>
```

스킬은 사용자가 `/ax-status <subcommand>` 형태로 호출하면 위 명령을 실행해 결과를 그대로 보여준다.

## 서브커맨드

### `/ax-status install`

글로벌 `~/.claude/settings.json`의 `statusLine.command`를 team-ax 래퍼로 교체.

**동작:**
1. `~/.claude/plugins/installed_plugins.json`에서 `team-ax@<marketplace>` 설치 경로 확인 — 없으면 중단(설치 안내).
2. `~/.claude/hud/ax-statusline.sh` 래퍼 생성 (template: `plugin/scripts/templates/hud-wrapper.sh` 복사).
3. `~/.claude/settings.json`을 `settings.json.bak-YYYYMMDD-HHMMSS`로 백업.
4. 기존 `statusLine`이 있으면 `statusLineBackup` 키로 보존, 없으면 그대로 진행.
5. `statusLine.command`를 `~/.claude/hud/ax-statusline.sh`로 교체.
6. 토글 키 기본값(`statusline.{ctx,5h,7d,branch} = true`) 주입 (이미 있으면 보존).

**유의:** Claude Code 세션 재시작 후 적용된다.

### `/ax-status uninstall`

원상복구. 기존 statusLine으로 되돌리고 래퍼 제거.

**동작:**
1. settings.json 백업.
2. `statusLineBackup`이 있으면 `statusLine`으로 복원, 없으면 `statusLine` 키 제거.
3. 래퍼 파일은 `rm` 금지 — `mv ~/.Trash/ax-statusline.sh.<timestamp>`.
4. 토글 키(`statusline`)는 유지 (재설치 대비).

### `/ax-status toggle <key>`

특정 행 on/off. `key ∈ {ctx, 5h, 7d, branch}`.

**동작:**
1. settings.json 백업.
2. `statusline.<key>` 값 flip (true ↔ false).
3. 새 값 출력.

statusline은 다음 refresh부터 즉시 반영 (재시작 불필요).

### `/ax-status on` / `/ax-status off`

전역 off 환경변수 안내. `CLAUDE_STATUSLINE_OFF=1` 이 설정되면 statusline이 즉시 0 exit한다.

- `off`: `export CLAUDE_STATUSLINE_OFF=1` 안내 (영구 적용은 셸 rc 추가).
- `on`: `unset CLAUDE_STATUSLINE_OFF` 안내.

특정 행만 끄려면 `toggle` 사용. 전역 off는 statusline 전체를 끈다.

### `/ax-status show`

현재 상태 요약 (인자 없이 호출 시 기본 동작).

**출력:**
- 래퍼 존재 여부 (`~/.claude/hud/ax-statusline.sh`)
- team-ax 설치 경로 (`installed_plugins.json` 기준)
- 글로벌 `statusLine.command` 현재 값
- 토글 4종 현재 값 (`ctx / 5h / 7d / branch`)
- quota 캐시 존재 + 최근 갱신 시각
- 전역 off 활성 여부

## 가드레일

1. **settings.json 수정 전 항상 백업** — `settings.json.bak-YYYYMMDD-HHMMSS`.
2. **`rm` 금지** — 래퍼 제거는 `mv ~/.Trash/`. (CLAUDE.md 규칙)
3. **team-ax 미설치 시 install 거부** — 명확한 에러 + 설치 안내.
4. **의존성(`jq`) 없으면 명확히 에러** — `brew install jq` 안내.
5. **글로벌 ~/.claude만 만짐** — 프로젝트 `.claude/settings.json`은 손대지 않음 (글로벌이 우선 적용됨).

## 참조

- `plugin/scripts/ax-status.sh` — 실행 엔진 (모든 서브커맨드)
- `plugin/scripts/ax-statusline.sh` — statusline 렌더 (CTX/5H/7D)
- `plugin/scripts/fetch-usage.sh` — quota API 캐시 갱신
- `plugin/scripts/templates/hud-wrapper.sh` — 래퍼 템플릿 (버전 무관 resolver)
