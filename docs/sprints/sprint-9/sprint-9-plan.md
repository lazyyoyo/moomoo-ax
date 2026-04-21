# sprint-9 plan

**목표**: team-ax 플러그인 **v0.9.0** 배포 — v0.7.2 구조로 롤백해서 Ralph loop(태스크 단위 reviewer + REQUEST_CHANGES 재리뷰 + 2회 연속 시 오너 위임) 복원.

> **배경 — 왜 v0.8을 포기하는가**
>
> v0.7.2까지의 team-ax `ax-build`는 태스크 단위 Ralph loop가 **워커 스킬(ax-execute) 본문에 박혀 있던** 구조다. engine=claude든 codex든 워커는 태스크마다 `codex exec '$ax-review code <files>'` 호출 → APPROVE/REQUEST_CHANGES 파싱 → 재리뷰 → 동일 사유 2회 연속이면 오너 위임. 엔진 독립적으로 품질 게이트가 작동했다.
>
> v0.8은 "병렬 속도 + 토큰 절약"을 목표로 워커를 **codex 백그라운드 프로세스 + 파일시스템 프로토콜(`result.json`) + lead 일괄 커밋**으로 갈아엎었다. 이 과정에서 ax-execute의 reviewer 훅은 이식되지 않았고, ax-build 3-e는 whitelist 대조 + placeholder grep만 남았다. ax-review `code` 타입 체크리스트(7종)는 여전히 존재하나 SKILL.md 디스패치가 `stub` 표기로 퇴화해 호출되지 않는다.
>
> 결과: 태스크 단위 품질 게이트 부재, 자동 재작업 루프 부재, 모든 문제가 오너 인터럽트로 수렴. 남편 환경 실사용 체감 품질이 v0.7.2 대비 급락. v0.8의 병렬 아이디어(파일 whitelist 격리, codex 백그라운드 워커)는 폐기가 아니라 "Ralph loop를 설계 전제로 먼저 박고 그 위에 병렬을 얹는" 순서로 sprint-10+에서 재도입 검토한다.
>
> **의사 결정**: v0.8을 추가 패치하지 않는다. plugin/ 디렉토리 전체를 `v0.7.2` 태그 상태로 되돌리고, 버전만 앞으로 가도록 `v0.9.0`으로 전진. Claude Code는 버전 필드를 기준으로 업데이트를 감지하므로 사용자는 `/plugin update` 1회로 롤백 결과를 받는다.

## 범위 (3건)

### 1. B-ROLLBACK-V072 — plugin/ 디렉토리 v0.7.2 복원 + 버전 bump

`plugin/` 전체를 v0.7.2 태그 상태로 되돌린다.

**복원 방식:**
```bash
git checkout v0.7.2 -- plugin/
```

**버전 필드 bump (이 두 파일만 v0.9.0):**
- `.claude-plugin/marketplace.json` → `version`, `plugins[0].version` 둘 다 `0.9.0`
- `plugin/.claude-plugin/plugin.json` → `version` `0.9.0`

**함께 정리(v0.8 잔재):**
- `docs/guides/v0.7-to-v0.8-migration.md` — 의미 상실. 휴지통 이동 (`mv ~/.Trash/`)
- `docs/specs/parallel-dev-spec.md` — v0.8 모델 기준으로 재작성된 버전. v0.7.2 시점 구조로 복원 or 휴지통(v0.7.2 태그에 존재하던 버전을 `git checkout v0.7.2 -- docs/specs/parallel-dev-spec.md`로 회복). 태그 시점 존재 여부 확인 후 판단.
- `.ax/` 디렉토리 런타임 산출(`plan.json`, `workers/`, `inbox.md`, `result.json`) — v0.8 전용. `.gitignore` 유지한 채 실 산출은 남편/오너 로컬에서 각자 cleanup

**검증:**
- [ ] `git diff v0.7.2 HEAD -- plugin/` 결과 = 버전 필드 2곳 차이만
- [ ] `plugin/skills/ax-build/SKILL.md`에 `codex code review` / `APPROVE` / `REQUEST_CHANGES` / `2회 연속 REQUEST_CHANGES → 오너에게 위임` 라인 복원
- [ ] `plugin/skills/ax-execute/SKILL.md`에 `$ax-review code` 호출 규약 복원
- [ ] `plugin/skills/ax-review/SKILL.md`의 `code` 타입 표기가 **stub 아님** (실제 체크리스트 디스패치)
- [ ] `plugin/skills/ax-review/references/code-checklist.md` 존재(v0.4 7종 체크리스트)

### 2. B-V09-CHANGELOG — CHANGELOG 롤백 사유 명기

`CHANGELOG.md`에 v0.9.0 엔트리 추가.

**포함 내용:**
- 롤백 대상: v0.8.0 / v0.8.1 / v0.8.2 / v0.8.3 (4건) 일괄 무효화
- 롤백 사유: (1) reviewer 훅(ax-execute 내장 `$ax-review code` 호출) v0.8 재설계 중 유실, (2) 태스크 단위 자동 재작업 루프 부재, (3) 실측 품질 저하(남편 환경 재현)
- 복원 대상: v0.7.2의 ax-build/ax-execute/ax-review 3개 스킬 구조 (claude TUI 워커 + tmux worktree + 엔진 토글)
- 남편 환경 재사용 경로: `/plugin update` 후 `/ax-build`
- v0.8 구상의 장래: sprint-10+에서 "Ralph loop 우선 + 그 위에 병렬" 순서로 재검토

### 3. B-V09-BACKLOG-SYNC — BACKLOG done 이관 + v0.8 엔트리 무효화 주석

`BACKLOG.md` done 섹션에:

- 신규 엔트리 "sprint-9 — 플러그인 v0.9.0 롤백 릴리즈 (2026-04-21)" 추가
- 기존 엔트리 4건(v0.8.0 sprint-8, hotfix v0.8.1/v0.8.2/v0.8.3)에 **"⚠ v0.9.0에서 롤백됨"** 주석 1줄씩 추가 (엔트리 자체는 역사 기록으로 남김)
- inbox 상단 "v0.8.4+ 후보" 블록에 이미 붙인 경고 문구 유지

## 비범위

- **Ralph loop 개선 (자동 rework 태스크 append)** — sprint-10 범위. v0.7.2 기준 "동일 사유 2회 연속 REQUEST_CHANGES → 오너 위임"까지만 복원, 그 이상 자동화 안 함
- **ax-review pr 타입 구현** — 장기 inbox 유지, sprint-9 범위 아님
- **병렬 엔진 재도입** — sprint-11+ 검토. v0.8 codex 백그라운드/파일 whitelist 아이디어 중 살릴 것은 그때 선별
- **v0.8 코드 cherry-pick** — 없음. v0.8.1~v0.8.3 hotfix들은 codex 워커/pane 모델 종속이라 v0.7.2 claude 워커 구조에 적용 불가
- **파생 문서(v0.8 기준 spec)의 소급 정정** — 삭제/롤백만. 내용 재작성은 sprint-10에서 필요 범위만

## 성공 기준

**구조 복원:**
- [ ] `plugin/` diff가 버전 필드 2곳만 차이 (v0.7.2 대비)
- [ ] `plugin/skills/ax-build/SKILL.md` Ralph loop 4줄 복원 (codex review 호출 / APPROVE / REQUEST_CHANGES / 2회 연속 오너 위임)
- [ ] `plugin/skills/ax-execute/SKILL.md` reviewer 규약 복원
- [ ] `plugin/skills/ax-review/SKILL.md` `code` 타입이 stub이 아닌 실제 디스패치

**배포:**
- [ ] `hotfix/rollback-to-v0.7.2` 브랜치에서 PR 생성 → 오너 승인 → squash merge
- [ ] `v0.9.0` 태그 push
- [ ] marketplace.json/plugin.json 버전 `0.9.0`
- [ ] CHANGELOG v0.9.0 엔트리 + BACKLOG done 엔트리 머지됨

**실환경 검증:**
- [ ] 오너 환경 `/plugin update` → `/ax-build` 1회 완주 (작은 스코프)
- [ ] 남편 환경(my-agent-office) 동일 검증 — `claude -p` / `new-window -d` / `remain-on-exit on` 등 v0.7.2 hotfix 반영 확인
- [ ] 워커가 태스크 완료 시 `codex exec '$ax-review code …'` 실행되고 APPROVE/REQUEST_CHANGES 첫 줄이 콘솔 또는 `.ax-status`에 노출되는지 확인

**회귀 방지:**
- [ ] ax-define / ax-qa / ax-deploy / ax-design / ax-paperwork / ax-clean / ax-help / ax-status 기능 동작 유지 (sprint-7까지 커버)
- [ ] `ax-codex install`이 v0.7.2 경로로 정상 설치 (ax-review + ax-execute)

## 리스크

- **문서 공백**: v0.8 기반 외부 문서/안내가 프로젝트 리포 곳곳에 남을 가능성. sprint-9 PR에서 눈에 띄는 범위만 정리하고, 나머지는 sprint-10 paperwork로.
- **Claude Code 업데이트 체감**: 사용자 측에서 `/plugin update`가 v0.9.0을 제때 반영하지 않을 가능성. README/릴리즈 노트에 수동 리프레시 명령 병기.
- **v0.8에서 고친 환경 버그 잔존 가능성**: v0.7.2에도 없는 새로 발견된 환경 버그가 있었다면 롤백하면서 재발. 실환경 검증에서 체크.
- **sprint-10에서 뭘 할지 미확정**: 롤백만 하고 개선 방향 없으면 같은 실패 반복. sprint-9 PR과 별도로 sprint-10 준비 메모를 notes에 남김.
- **`docs/specs/parallel-dev-spec.md` 경합**: v0.7.2 시점 파일과 v0.8 재작성 본 둘 다 존재. 어느 쪽을 최종으로 쓸지 PR 리뷰에서 결정.

## 상태

- [x] 원인 진단 — Ralph loop 유실이 v0.8 재설계 유실임을 git blame으로 확정 (v0.7.0/v0.7.2 SKILL.md에 명시, 59fbd6c 커밋에서 증발)
- [x] 롤백 경로 합의 (v0.7.2 → v0.9.0 bump)
- [x] sprint-9-plan.md 작성 (본 문서)
- [x] plan + 롤백 단일 PR로 묶기 결정 (오너 지시)
- [x] `sprint-9/v0.9-rollback-plan` 브랜치에서 plan 커밋
- [x] `git checkout v0.7.2 -- plugin/ docs/specs/parallel-dev-spec.md`
- [x] v0.8 신설 파일 휴지통 (`docs/guides/v0.7-to-v0.8-migration.md`, `plugin/skills/ax-build/templates/worker-inbox.md.tmpl`)
- [x] 버전 필드 bump (marketplace.json + plugin.json → 0.9.0)
- [x] CHANGELOG v0.9.0 엔트리 + v0.8 계열 주석
- [x] BACKLOG done 이관 + v0.8 엔트리 주석
- [ ] PR 생성 → 오너 리뷰
- [ ] squash merge + v0.9.0 태그 push
- [ ] 실환경 검증 (오너 + 남편)
- [ ] sprint-9 retrospective + sprint-10 범위 합의
