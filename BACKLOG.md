---
last-updated: 2026-04-21
---

# moomoo-ax 백로그

team-ax 플러그인 자체 개발의 인박스. 외부 제품(rubato, rofan-world 등)의 BACKLOG는 각 제품 리포 안에 있다 (혼동 금지).

> **운영 규칙**
> - inbox: 아이디어 캡처. 스프린트 미배정.
> - ready: 다음 스프린트 후보로 정제된 항목 (sprint-N-plan 진입 대기).
> - done: 스프린트/hotfix 종료 시 이관. 스프린트 번호 or hotfix 버전 표기.

## inbox

### ax-build 병렬 흐름 관련 (v0.7.2 이후 후속)

- B-AXBUILD-TRUST-DIALOG: **첫 워크트리 진입 시 "trust this folder?" 다이얼로그가 자동화를 차단** — v0.7.2 실검증(2026-04-21)에서 발견. `claude -p`는 trust dialog를 자동 skip했으나 `-p` 제거로 부활. 각 워크트리 첫 실행 때 오너가 `1` 입력해야 진행됨 → 진짜 병렬 자동화 안 됨. 해결 후보: (a) 워크트리 생성 후 `claude` 호출 전에 trust 레지스트리(`~/.claude/…`)에 경로 등록, (b) `--dangerously-skip-permissions` 또는 유사 플래그 재검토(의미상 다르지만 효과는 유사할 수 있음), (c) tmux send-keys로 `1 Enter` 자동 주입
- B-AXBUILD-TMUX-NESTED: SKILL.md 사전 점검 / 릴리즈 노트에 "이미 tmux 안인 경우 새 세션 만들지 말고 기존 세션 사용" 분기 추가 — owner가 `tmux new-session -s ax-build`를 시도했다가 "sessions should be nested with care" 경고 받음
- B-AXBUILD-CLAUDENATIVE: Claude CLI 빌트인 `--worktree --tmux` 활용 검토 — `claude --help`에 `-w/--worktree [name]`, `--tmux` 플래그 존재 (iTerm2 native panes 우선, `--tmux=classic` 옵션). 현재 우리 orchestrator가 직접 git worktree + tmux new-window를 쓰는데 빌트인으로 위임 가능 여부 분석. 단 branch 네이밍(`version/vX.Y.Z-<name>`) / `.ax-status` 초기화 / 포트 할당 등 커스텀 훅 지점 유지 방법 필요
- B-AXBUILD-BRIEF-INJECT: `.ax-brief.md` 주입 방식 재설계 — 현재 positional prompt로 "Read .ax-brief.md and follow" 지시만 주입. brief 내용을 Claude가 Read 도구로 읽는 2-step 구조. 옵션 재검토: (A) `claude "$(cat .ax-brief.md)"` 내용 직접 주입(escape 문제), (B) `--append-system-prompt` 활용, (C) CLAUDE.md/hook으로 자동 참조
- B-AXBUILD-MCP-SHARE: 병렬 워커 MCP 중복 부팅 이슈 — 워커 N개마다 MCP 서버 전체 스폰(남편분 환경 7개). 워커별 축소된 `.mcp.json` 지정 가능한지 / 부모-자식 MCP 공유 옵션 있는지 조사. 성능 이슈지 기능 버그 아님

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

## ready

## inbox (장기 후보)

### sprint-8 후보 — ax-deploy v2 묶음 (rubato admin 도그푸딩 피드백)

- B-TRACKTYPE: ax-deploy 트랙별 정책 분기 — `scope.md §버전 메타`에 `track-type: product | admin | infra` 추가. admin/internal-tools는 (1) CHANGELOG 작성 강제 부적합(GitHub Release만 사용), (2) BACKLOG done 이관 강제 부적합(Release로 추적), (3) 제품 semver 기반 `/product-deploy` 부적합 → ax-deploy가 트랙 타입에 따라 분기
- B-WTHOST: ax-build/ax-deploy worktree 환경 호환성 — (1) `gh pr merge --squash --delete-branch` 시 "main is already checked out at <other-worktree>" 에러(머지는 정상이나 사용자 혼란), (2) main 워크트리가 다른 트랙 점유 중일 때 pull 차단 → 임시 worktree 패턴(`git worktree add /tmp/<name> main` → pull → `.vercel/` 복사 → vercel --prod → worktree remove) 가이드 + ax-deploy가 `git worktree list`로 환경 인지 + main checkout 실패 시 자동 안내
- B-VERCELIGN: ax-deploy Vercel "Ignored Build Step" 인지 — git push deploy를 모두 cancel하는 프로젝트(rubato 등)에서 dashboard "Redeploy"가 빌드 skip → 6단계 실행 전 `vercel ls <project>` 최근 5건 status 검사. 모두 Canceled면 자동 배포 disabled 안내 + vercel CLI 직접 실행 절차로 분기
- B-CLEANUPPR: ax-deploy 후처리 cleanup PR 패턴 명문화 — 머지·태그·Release 완료 후 ⏳ planned 마커 제거 + build-plan 체크박스 [x] 처리는 별도 cleanup PR로 분리해야 함(rubato admin-v0.2.0 PR #17). 1단계 preflight가 차단 사유로 잡지만 처리 절차 안내 부족 → main 기반 임시 브랜치(`chore/<version>-cleanup`) → 마커 제거 + 체크박스 → push → squash merge 패턴 매뉴얼화 + 가능하면 자동화

### 장기

- [dogfood] team-ax 도그푸딩 실측 — v0.6 기준 define→build→qa→deploy 1회 완주 (sprint-6에서 릴리즈 직후로 미룸, 별도 세션 진행 예정)
- [feature] `ax-review pr` 타입 구현 — `references/pr-checklist.md` 본격 작성 + sandbox 정책 확정 (`workspace-read` 추정)
- [feature] Hook 기반 자동 강제 — spec-lifecycle 4종 장치를 PreToolUse 훅으로 차단 (현재는 에이전트 규칙 + review만)
- [feature] 의존성 그래프 기반 merge 순서 자동 관리 (deploy 단계)
- [infra] team-ax 자기 진화 — meta loop, 외부 패턴 자동 흡수 (PROJECT_BRIEF 장기 비전)
- [infra] 대시보드 연동 — 오너 개입 횟수 / 토큰 / iteration 등 북극성 지표 추적

## done

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
