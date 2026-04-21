---
last-updated: 2026-04-21 (sprint-9 신설 — v0.9.0 롤백 릴리즈)
---

# moomoo-ax 백로그

team-ax 플러그인 자체 개발의 인박스. 외부 제품의 BACKLOG는 각 제품 리포 안에 있다 (혼동 금지).

> **운영 규칙**
> - inbox: 아이디어 캡처. 스프린트 미배정.
> - ready: 다음 스프린트 후보로 정제된 항목 (sprint-N-plan 진입 대기).
> - done: 스프린트/hotfix 종료 시 이관. 스프린트 번호 or hotfix 버전 표기.

## ready

### sprint-9 — v0.9.0 롤백 릴리즈 (Ralph loop 복원)

**배경**: v0.7.2까지는 ax-build/ax-execute 안에 태스크 단위 Ralph loop(`$ax-review code` 호출 → APPROVE/REQUEST_CHANGES → 수정 후 재리뷰 → 동일 사유 2회 연속 시 오너 위임)가 명시·동작. v0.8 병렬 엔진 재설계 과정에서 워커 주체를 codex 백그라운드로 바꾸면서 **reviewer 훅이 이식되지 않고 유실**. 3-e에는 whitelist 대조 + placeholder grep만 남아 품질 게이트가 사라짐. 모든 문제는 오너 인터럽트로 수렴하고, 자동 재작업 루프 부재. 실사용(남편 환경) 체감 품질이 v0.7.2 대비 급락.

**방향**: v0.8 병렬 엔진을 더 패치하기보다 **v0.7.2로 plugin/ 디렉토리 통째 롤백 + 버전은 v0.9.0으로 전진**. v0.8의 codex 병렬 아이디어는 폐기가 아니라 sprint-10+에서 "Ralph loop를 먼저 박고 그 위에 병렬" 순서로 재도입 검토.

- **B-ROLLBACK-V072**: `plugin/` 전체를 `v0.7.2` 태그 상태로 복원 (`git checkout v0.7.2 -- plugin/`). `.claude-plugin/marketplace.json` + `plugin/.claude-plugin/plugin.json` 버전 필드만 `v0.9.0`으로 bump. v0.8 계열 코드/문서 전부 제거 (codex 워커, 파일 whitelist, inbox.md 템플릿, parallel-dev-spec v0.8, v0.7-to-v0.8-migration.md 등)
- **B-V09-CHANGELOG**: CHANGELOG에 v0.8 계열(0.8.0~0.8.3) 롤백 명기 — 사유는 "reviewer 루프 유실 + 자동 재작업 부재 + 실측 품질 저하". v0.9.0 = v0.7.2 구조 복귀. 남편 환경 재사용 경로 안내
- **B-V09-BACKLOG-SYNC**: BACKLOG done 섹션에 "sprint-9 — 플러그인 v0.9.0 롤백" 엔트리 추가 + v0.8 계열 done 엔트리들에 "v0.9.0에서 롤백됨" 주석

**v0.8 cherry-pick 범위**: 없음. v0.8.1~v0.8.3 hotfix들은 모두 codex 워커/pane 모델에 종속된 fix라 v0.7.2의 claude 워커 구조에 적용할 게 없음.

**후속 구상 (sprint-10+, 본 sprint 범위 아님)**:
- sprint-10 = v0.7.2 기반으로 Ralph loop 강화 (rework 태스크 자동 append로 오너 인터럽트 축소)
- sprint-11 = 병렬 엔진 재도입 검토 — ax-execute에 reviewer 훅이 박힌 상태에서 codex/claude 엔진 토글 유지하며 병렬화

## inbox

### v0.8.4+ 후보 (paperwork audit 결과 이관)

> **주의 (sprint-9 이후)**: 아래 항목들은 v0.8 계열 구조 기반. sprint-9 롤백 후엔 상당수가 무의미해짐 (ax-execute inbox 프로토콜, ax-build orchestrator v2 경로 등). sprint-9 머지 후 재평가 필요.

- B-SCRIPTS-RESOLVE: `plugin/scripts/...` 경로 systematic resolve — 현재 ax-build만 `$ORCH` 패턴 사용. 다른 스킬(ax-codex, ax-deploy, ax-clean, ax-design, ax-paperwork, ax-status, ax-review, ax-execute)은 여전히 `bash plugin/scripts/...` 직접 참조. 설치된 플러그인 cache 경로로 wrapper 인프라(ax-status hud-wrapper 패턴 차용) 또는 ax-build처럼 각 SKILL.md resolve 가이드 추가
- B-DESIGN-GATE-CODIFY: `ax-design` 7단계 게이트 자동 재작업 로직(keep/discard/루프 3회)이 SKILL.md 본문에 자연어로 기술됨 → `design-gate.sh` 결정론 로직 강화 (progressive codification)
- B-AXHELP-DEPRECATED: `ax-help` 보조 스킬 목록에서 deprecated 표기된 `executor` 에이전트 제외

### 사소한 일관성 (BACKLOG inbox 보관만)

- B-AXCODEX-REF: `ax-codex/SKILL.md` §참조 설명에 "rsync 대상은 ax-review / ax-execute 자체이며, 본 스킬은 경로 동기화만 담당" 명시
- B-AXSTATUS-SCOPE: `ax-status/SKILL.md` §도입부에 "~/.claude/ 및 ~/.claude/hud/ 책임 경계" 명확화
- B-AXHELP-TMUX: `ax-help` 상태 감지 로직에 tmux 유무 조건부 표기 (ax-build가 tmux 의존하지 않으므로)

### ax-codex

- B-AXCODEXCACHE: `ax-codex.sh`의 Claude 플러그인 캐시 경로 하드코딩 버그 — `CLAUDE_CACHE_BASE="$HOME/.claude/plugins/cache/lazyyoyo/team-ax"`로 하드코딩됐는데 실제 경로는 `moomoo-ax/team-ax` (marketplace name). install 시 "Claude 플러그인 캐시 없음 — skip"이 항상 발생. `.claude-plugin/marketplace.json`의 `name` 읽어서 동적 resolve. (install-local-skills.sh에서 상속된 버그, 기능 자체엔 영향 없음 — 캐시는 플러그인 시스템이 reload 시 갱신)

### statusline — my-agent-office 대비 누락 기능

my-agent-office `plugins/statusline/scripts/statusline.sh` 대비 `ax-statusline.sh`에 빠진 기능들. 각각 판단 후 필요한 것만 채택.

- B-SL-MODEL: **현재 모델명 표시** — stdin JSON의 `.model.id`를 파싱해 `opus4.6 / sonnet4.6 / haiku4.5` 등 short name으로 Line 1에 표시. (오너가 명시 요청)
- B-SL-FASTMODE: `fastMode` 토글 상태 표시 — `↯fast` 뱃지 (`settings.json .fastMode`)
- B-SL-EFFORT: `effortLevel` 표시 — `⚡lo/md/hi` 뱃지 (`settings.json .effortLevel`, 기본 high)
- B-SL-PLUGINSYNC: 설치된 플러그인 sync 상태 — `~/.claude/plugins/installed_plugins.json` 파싱 → 해당 owner의 플러그인 경로 존재 여부 집계 → `mao N/M ✓/⚠` 형태. team-ax는 `ax N/M`로 표시. 토글 키 `.statusline.plugin` 추가
- B-SL-PHASE: `.phase` 파일 연동 — `${SESSION_ROOT}/.phase` JSON의 `phase` 값(`done` 녹색 / `hotfix` 빨강 / 기타 청록) 읽어 branch row 앞에 표시. team-ax는 sprint/ver로 대체되는 면도 있으니 채택 여부 판단 필요
- B-SL-WT-BRANCH: worktree branch 이름 표시 — 현재 `wt:N`만 표시. my-agent-office는 1개면 `(+wt: branch)`, 2개 이상은 `(+wt: N trees)`. sprint-7에서 팀-ax는 `wt:N`으로 확정했으니 정책 재검토
- B-SL-PROJNAME: `/hq/projects/<name>/` 경로에서 프로젝트명만 뽑아 CWD 대신 표시 — team-ax는 현재 `📦 repo`로 이미 표시 중이라 겹칠 수 있음. 보류 판단 필요
- B-SL-SESSION-ROOT: session root fallback 체인 보강 — `.workspace.project_dir` → `.workspace.current_dir` → `$PWD` (team-ax는 `current_dir`만 봄)

## inbox (장기 후보)

### sprint-9+ 후보 — ax-deploy v2 묶음

- B-TRACKTYPE: ax-deploy 트랙별 정책 분기 — `scope.md §버전 메타`에 `track-type: product | admin | infra` 추가. admin/internal-tools는 (1) CHANGELOG 작성 강제 부적합(GitHub Release만 사용), (2) BACKLOG done 이관 강제 부적합(Release로 추적), (3) 제품 semver 기반 `/product-deploy` 부적합 → ax-deploy가 트랙 타입에 따라 분기
- B-WTHOST: ax-deploy 환경 호환성 — (1) `gh pr merge --squash --delete-branch` 시 "main is already checked out at <other-worktree>" 에러(머지는 정상이나 사용자 혼란), (2) main 워크트리가 다른 트랙 점유 중일 때 pull 차단 → 임시 worktree 패턴 가이드 + ax-deploy가 `git worktree list`로 환경 인지 + main checkout 실패 시 자동 안내
- B-VERCELIGN: ax-deploy Vercel "Ignored Build Step" 인지 — git push deploy를 모두 cancel하는 프로젝트에서 dashboard "Redeploy"가 빌드 skip → 6단계 실행 전 `vercel ls <project>` 최근 5건 status 검사. 모두 Canceled면 자동 배포 disabled 안내 + vercel CLI 직접 실행 절차로 분기
- B-CLEANUPPR: ax-deploy 후처리 cleanup PR 패턴 명문화 — 머지·태그·Release 완료 후 ⏳ planned 마커 제거 + build-plan 체크박스 [x] 처리는 별도 cleanup PR로 분리해야 함. 1단계 preflight가 차단 사유로 잡지만 처리 절차 안내 부족 → main 기반 임시 브랜치(`chore/<version>-cleanup`) → 마커 제거 + 체크박스 → push → squash merge 패턴 매뉴얼화 + 가능하면 자동화

### 장기

- [dogfood] team-ax 도그푸딩 실측 — v0.6 기준 define→build→qa→deploy 1회 완주 (sprint-6에서 릴리즈 직후로 미룸, 별도 세션 진행 예정)
- [feature] `ax-review pr` 타입 구현 — `references/pr-checklist.md` 본격 작성 + sandbox 정책 확정 (`workspace-read` 추정)
- [feature] Hook 기반 자동 강제 — spec-lifecycle 4종 장치를 PreToolUse 훅으로 차단 (현재는 에이전트 규칙 + review만)
- [feature] 의존성 그래프 기반 merge 순서 자동 관리 (deploy 단계)
- [infra] team-ax 자기 진화 — meta loop, 외부 패턴 자동 흡수 (PROJECT_BRIEF 장기 비전)
- [infra] 대시보드 연동 — 오너 개입 횟수 / 토큰 / iteration 등 북극성 지표 추적

## done

### hotfix v0.8.3 — 사고 기록·외부 제품·시간축 주석 제거 (2026-04-21)

PROJECT_BRIEF §6 "스킬 본문은 현재 규칙만" 원칙 재확립.

- 사고 기록 제거 (ax-execute 영역 침범 가드 도입부 / product-owner Why This Matters 사고 단락 / executor 가드 괄호 / ax-define 제품 예시 / spec-lifecycle 섹션 제목 / pr-checklist) — 개선된 규칙 본문은 유지
- references 학습 예시에서 외부 제품 이름 제거 (jtbd / slc / story-map / semver / docs-structure / templates/scope)
- pane→백그라운드 전환 잔재 9건 정리 (ax-help / ax-deploy / ax-paperwork / ax-clean 및 checklist / build-plan 템플릿 / ax-execute preamble / README)
- 구현 상태 시간축 주석 제거 (ax-review "v0.4 구현 / v0.1 stub" → "stub")
- ax-define / product-owner 가드레일 "(v0.1.1 신설/변경)" 주석 제거
- ax-deploy cleanup `$ORCH` resolve 패턴 통일

### hotfix v0.8.2 — 워커 모델 백그라운드화 + 8건 실검증 피드백 (2026-04-21)

- 워커 실행 모델 tmux pane split → 백그라운드 프로세스 + stdout.log/pid/exit_code 파일. tmux 의존 제거. pane 관리 복잡성(remain-on-exit 실패, pane id race 등) 자연 소멸
- ax-execute 동시 라운드 self-check 개선 — `.ax/plan.json` 모든 task whitelist 합집합 인지하여 타 워커 산출 파일 오판정 방지
- 타겟 기반 backpressure — 전역 lint/test 금지, 변경 파일 한정 `npx eslint` + test script 자동 폴백 (vitest/jest)
- planner glue 태스크 규칙 (`kind: glue`) — 경계 연결 작업 독립 분리로 파일 whitelist 격리 사각지대 해소
- lead 검증에 placeholder/TODO 스캔 훅 추가 (3-e 단계)
- ax-build 재개 모드 §2.5 명시 — version branch + plan.json + 일부 커밋 있을 때 미완료만 스폰
- SKILL.md 스크립트 경로 `$ORCH` resolve 가이드
- orchestrator `logs <task_id>` 서브커맨드 신설
- parallel-dev-spec 전면 재작성 (백그라운드 모델 + glue + 재개)

### hotfix v0.8.1 — 모델 하드코딩 제거 + 메인 window split + 시간축 주석 정리 (2026-04-21)

- `-c model=` 옵션 기본 제거 → codex CLI 기본값 사용 (`gpt-5-codex` 하드코딩으로 워커 즉사하던 이슈 해결)
- 별도 `ax-workers` window → 메인 window 수직 split (Ctrl-b w 전환 없이 한 화면 관찰) — v0.8.2에서 백그라운드 모델로 재구성됨
- 시간축 주석 1차 정리 — 이후 v0.8.3에서 원칙 재확립

### sprint-8 — 플러그인 v0.8.0 (2026-04-21)

ax-build 병렬 엔진 재설계. worktree 제거 + Codex 워커 + 파일 whitelist 격리 + 단일 브랜치. lead(Claude main)는 오케스트레이션만, 코드 작성은 전부 codex로 이관해 Claude 토큰 부담 완화 + tmux pane grid로 병렬 관찰성 확보.

- B-AXEXECUTE-AS-PROTOCOL: `plugin/skills/ax-execute/SKILL.md` 재작성 — 워커 프로토콜 엔진 (inbox 1건 실행 + whitelist 가드 + result.json 출력 + no-commit). v0.7의 `--allow/--block` 인자 및 stdout DONE/BLOCKED 계약 폐기
- B-FILE-WHITELIST-PLAN: planner 확장 — `.ax/plan.json` 스키마 + 파일 집합 기반 분할 규칙 + 자체 검증
- B-WORKER-INBOX: `plugin/skills/ax-build/templates/worker-inbox.md.tmpl` 신규 + `.ax-brief.md` deprecated
- B-ORCHESTRATOR-V2: `ax-build-orchestrator.sh` 6개 원시 커맨드 재작성 (precheck/init/prepare-window/spawn/status/cleanup). worktree 로직 제거, tmux pane tiled split 도입
- B-CODEX-WORKER-SPAWN: `codex exec '$ax-execute <inbox>'` 스폰 표준화. 기본 모델 `gpt-5-codex`
- B-WORKER-POLL / B-COMMIT-STRATEGY / B-ROUND-LOOP: lead 측 흐름 — 폴링/수렴/일괄 커밋/라운드 루프 (ax-build SKILL.md에 정의)
- B-WORKER-VISIBILITY-PANE: `ax-workers` 윈도우 tiled grid로 병렬 관찰성 확보
- B-CODEX-PRECHECK: 사전 점검 자동화 (tmux / codex / codex login / git / ax-execute 스킬)
- B-AXEXECUTE-REPOSITION: ax-execute를 단일/병렬 공통 진입점으로 재정의
- B-DOC-UPDATE: `parallel-dev-spec.md` 전면 재작성 + `v0.7-to-v0.8-migration.md` 신규 + AGENTS/README/CHANGELOG 반영
- B-PAPERWORK-V08: 릴리즈 직후 `/ax-paperwork` 실행 — v0.7 잔재 17건 일괄 갱신 (ax-design/ax-deploy/ax-help/ax-clean/ax-paperwork + ax-define 계열 + deprecated 표기 + 상태 문서)

**자연 해소 (v0.7.2 inbox 6건)** — 구조 변경으로 이슈 자체 소멸:

- B-AXBUILD-TRUST-DIALOG: 워커가 codex라 Claude trust dialog 무관
- B-AXBUILD-MCP-SHARE: codex는 MCP 호출 안 함
- B-AXBUILD-BRIEF-INJECT: inbox.md + ax-execute 스킬 분리 구조
- B-AXBUILD-CLAUDENATIVE: worktree 자체 제거로 `claude --worktree` 빌트인 검토 불필요
- B-AXBUILD-WORKER-VISIBILITY: tmux pane tiled grid로 해결
- B-AXBUILD-TMUX-NESTED: precheck에서 `$TMUX` 감지 처리

### hotfix v0.7.2 — ax-build 병렬 흐름 fix (2026-04-21)

남편분(my-agent-office) 재현 리포트에서 발견. v0.4부터 내재된 dead code를 실동작 상태로.

- B-AXBUILD-P-FLAG: `ax-build-orchestrator.sh`의 `claude -p` → `claude` (positional prompt) — `-p`는 "응답 1회 출력 후 종료" 모드라 워커가 MCP 부팅 후 조용히 종료. 기본 인터랙티브 TUI로 변경
- B-AXBUILD-NEWWINDOW-D: `tmux new-window` → `tmux new-window -d` — 자동 포커스 전환으로 오너 키 입력이 워커 stdin으로 새서 화면 깨짐 재현됨. `-d`로 메인 포커스 유지
- B-AXBUILD-TMUX-HARDERROR: tmux 밖에서 orchestrator 호출 시 WARN → ERROR(exit 1) 승격 — 무음 스킵이 버그 은폐의 원인이었음
- B-AXBUILD-REMAIN-ON-EXIT: 세션 레벨 `remain-on-exit on` 자동 설정 — 워커 비정상 종료 시 디버깅 흔적 유지
- B-AXBUILD-TMUX-PREREQ: SKILL.md 사전 점검에 "메인 세션이 tmux 안에서 기동" 전제 명시 추가 + §3-b 예시/설명 갱신

### hotfix v0.7.1 — ax-codex 스킬 + execute rename (2026-04-20)

- B-EXECUTERENAME: `execute` → `ax-execute` rename — `ax-` 프리픽스 통일. `plugin/skills/ax-execute/`, ax-build SKILL.md 호출부, AGENTS.md 업데이트
- B-AXCODEX: `/ax-codex` 스킬 신규 — ax-status 패턴. `install` / `uninstall` / `status` 서브커맨드. `~/.codex/skills/{ax-review,ax-execute}/` 동기화 + 구 `execute/` 휴지통 이동. 기존 `install-local-skills.sh` → `ax-codex.sh`로 흡수

### sprint-7 — 플러그인 v0.7.0 (2026-04-20)

statusline v2 + executor 엔진 토글 + define wireframe + preflight fix.

- B-STATUSLINE-V2: `ax-statusline.sh` v2 — CTX/5H/7D + 반응형 L/M/S + settings.json 토글 키 + stale 감지
- B-FETCHUSAGE: `fetch-usage.sh` 이식 — Anthropic OAuth quota 캐시(`/tmp/claude-usage-cache.json`, TTL 120s)
- B-AXSTATUS: `/ax-status` 스킬 + `ax-status.sh` 통합 엔진 — install/uninstall/toggle/on/off/show + 글로벌 settings.json statusLine 교체 + 백업 자동
- B-HUDWRAPPER: `templates/hud-wrapper.sh` 버전 무관 래퍼 — `installed_plugins.json` 런타임 resolve (플러그인 업데이트 시 재설치 불필요)
- B-CODEXEXEC: ax-build `executor.engine: claude | codex` 토글 — 신규 `/execute` 스킬 (executor 로직 이관 + codex 동기화). 영역 침범 가드 5종 (claude/codex 양쪽 적용)
- B-WIREFRAME: ax-define Phase C 13단계 wireframe.html 생성 게이트 — `ux-designer` 모드 분기(`wireframe-only`) + scope.md `§ 화면 정의` 표준 + 단일 정적 HTML 템플릿(디자인 없음 가드)
- B-PREFLIGHTFIX: `deploy-preflight.sh` 버그 3종 fix (rubato admin 도그푸딩) — spec 경로 자동 탐지 + `grep -c` 다중 결과 안전 처리 + 본 트랙 scope 한정 마커 검사 + macOS bash 3.2 호환

### sprint-6 — 플러그인 v0.6.0 (2026-04-18)

문서/디렉토리 품질 관리 + 환경 정리.

- B-AXPAPERWORK: `ax-paperwork` 스킬 — 문서-코드 정합성 탐지 + 중복/stale/참조깨짐 + in-place 갱신 + 오너 게이트
- B-AXCLEAN: `ax-clean` 스킬 — 미사용 파일/고아 문서/QA잔재 탐지 + 휴지통 이동 (`mv ~/.Trash/`, `rm` 금지)
- B-STATUSLINE: moomoo-ax 전용 statusline — repo/branch/sprint/version/worktree 표시, 프로젝트 `.claude/settings.json`에 등록
- B-PLUGINCONFLICT: team-design/team-product 충돌 해소 가이드 — `docs/guides/plugin-compatibility.md`, README 링크

### sprint-5 — 플러그인 v0.5.0 (2026-04-18)

전 사이클 완성 + 도그푸딩 피드백 반영.

- B-AXDEPLOY: `ax-deploy` 스킬 — 산출물 확인 → CHANGELOG → PR → preview → 오너 승인 → 머지+태그 → 배포 → BACKLOG 정리 → 잔재 정리. 워크트리/독립 트랙 지원.
- B-AXQAV2: `ax-qa` 강화 — product-qa 수준 (인벤토리 + Playwright + Visual + Viewport + 접근성 + 성능 + 오너 게이트)
- B-TMUXFIX: tmux 세션 자동 생성 수정 — .ax-brief.md 존재 확인 + tmux 세션 밖 감지 + 절대 경로
- B-AXHELP: `ax-help` 스킬 — 스킬 목록 + 실행 순서 + 프로젝트 상태 자동 감지 + 안전 작업 가이드
- B-SPEEDUP: ax-build 속도 개선 — 파일 경로만 전달 + 작업 단위 diff + 동일 사유 2회 오너 위임 + stub 사전 체크

### sprint-4 — 플러그인 v0.4.0 (2026-04-17)

ax-build + ax-qa + ax-review code. 개발팀 역할 전체 사이클.

- B-AXBUILD: `ax-build` 스킬 — 7단계 플로우 (plan → 공통 기반 → 실행 → 오너 확인 → 머지 → 최종 확인 → QA). Phase B를 ax-define에서 이동.
- B-ORCHESTRATOR: `ax-build-orchestrator.sh` — version branch + 워크트리 + tmux 세션 + 머지 자동화
- B-PLANNER: `planner` 에이전트 — gap 분석 + 실행 전략(워크트리 여부) 결정
- B-EXECUTOR: `executor` 에이전트 — TDD + backpressure 구현
- B-AXQA: `ax-qa` 스킬 — 통합 테스트 + code review + PR→main
- B-AXREVIEWCODE: `ax-review code` 타입 — stub → 7종 체크리스트 구현
- B-DESIGNMOD: ax-design SKILL.md 수정 — ax-build 호출 시 워크트리 실행 가능
- B-DEFINEMOD: ax-define SKILL.md 수정 — Phase B 제거 (scope 확정까지만)
- BACKLOG inbox 8건 해소: tmux 세션 관리, 디자인 통합, 스펙 변경 전파, Story 분리 기준, DS 순차성, 포트 할당, 빌드→QA 흐름

### sprint-3 — 플러그인 v0.3.0 (2026-04-16)

ax-design 스킬 신규 구현. 컴포넌트 단위 오너 확정 → 조합 패러다임.

- B-AXDESIGN: `ax-design` 스킬 — 8단계 플로우 (DS 토큰 확인 → 오너 인터뷰 → UX 플로우 → Story별 분기 → 컴포넌트 확정 → 전체 구성 → 게이트 → 프리뷰)
- B-UXDESIGNER: `ux-designer` 에이전트 — UX 플로우 설계 + 컴포넌트 필요 목록 산출
- B-DESIGNBUILDER: `design-builder` 에이전트 — DS 위에서 컴포넌트 개발 + 전체 구성
- B-DSGATE: `ds-completeness-check.sh` + `design-gate.sh` — DS 토큰 완성도 + DS 준수 린트 + 레이아웃 규칙
- B-CHECKEVAL: CheckEval 동적 체크리스트 — UX 기반 Yes/No 자동 생성 + 실패→재작업 자동 변환
- B-HOOKS: UserPromptSubmit DS 자동 주입 + PostToolUse DS 린트 훅
- B-REFS: references 8종 이식 (team-design) + reference-readme-template 부분 태깅 확장

### sprint-2 — 플러그인 v0.2.0 (2026-04-16)

Phase B 인프라 + 버전 전략 재설계 + 병렬 개발 설계.

- B-PHASEB: `phase-b-setup.sh` — Phase A 산출물 커밋 → 폴더 승격 → version branch → Story별 worktree 생성. `ax-define/SKILL.md` Phase B 단계 구현.
- B-VERSTRAT: 버전 전략 재설계 — "JTBD 분리 → 복수 버전" 폐기, minor(Story 분해) + patch(hotfix) 이원 체계. `jtbd.md`, `slc.md`, `semver.md`, `scope.md` 템플릿 갱신.
- B-DOCCHECK: `doc-checklist.md` diff 기준을 version branch 기점으로 변경.
- B-PARSPEC: `docs/specs/parallel-dev-spec.md` — v0.3 Build 오케스트레이션 설계 (파일 의존성/머지 순서/Story별 태스크 계획).

### hotfix v0.1.2 — ax-review doc 평가 대상 한정 (2026-04-16)

yoyowiki v0.1.1 도그푸딩에서 발견. working tree diff에 §수정 계획 밖 잔재가 섞이면 FAIL 오판이 남.

- B-DOCSCOPE: `doc-checklist.md` 검증 입력에 "평가 대상 한정 규칙" 추가 — §수정 계획에 명시된 파일에만 체크리스트 적용, 나머지는 판정하지 않음. `SKILL.md` doc 동작 3번 스텝에도 동일 규칙 명시.

### hotfix v0.1.1 — Phase A 구조 개선 (2026-04-15)

yoyowiki 도그푸딩에서 발견된 버그 3종 수정. sprint 밖 hotfix 진행.

- B-AUQGUARD: `product-owner` 에이전트에 `AskUserQuestion` 미가용 하드 가드 추가 — 실패 시 질문 목록만 작성하고 즉시 중단, 자체 추론 금지. (yoyowiki에서 에이전트가 6개 질문 전부 자답한 사고 대응)
- B-INTERVIEWRT: Phase A 2단계를 B안으로 구조 변경 — 서브에이전트가 interview.md에 질문 목록만 작성 → 메인 세션이 AskUserQuestion 호출 → 답을 다음 Task 호출 입력으로 전달. 작성/인터뷰 엔진 분리 유지.
- B-PHASEAFILE: Phase A 산출물 6개 → 3개로 축소 — `intake.md` / `interview.md` / `scope.md`만 유지. `jtbd.md` / `story-map.md` / `slc.md`는 폐지하고 scope.md 해당 섹션으로 단계별 in-place 기록. (downstream이 읽는 건 scope.md 한 장뿐)

### sprint-1 — 플러그인 v0.1.0 (2026-04-15)

- B-AXDEFINE: `ax-define` 스킬 — Phase A(intake/interview/JTBD/Story Map/SLC/semver) + Phase C(plan/write/review). references 6종 + scope.md 템플릿. 에이전트 2개(`product-owner`, `analyst`)
- B-AXREVIEW: `ax-review` 스킬 — 범용 리뷰 (codex 위임). doc 타입 구현 + code/pr stub
- B-INSTALL: `plugin/scripts/install-local-skills.sh` — Codex `~/.codex/skills/ax-review/` + Claude 플러그인 캐시 동기화
- B-AGENTS: 루트 `AGENTS.md` 신설 — Claude/Codex 호출 규약 정리
