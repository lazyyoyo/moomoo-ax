# sprint-7 plan

**목표**: team-ax 플러그인 **v0.7.0** 배포 — (1) statusline v2 + `/ax-status` 스킬, (2) ax-build executor 엔진 토글(claude/codex), (3) ax-define Phase C 선택적 wireframe.html, (4) deploy-preflight 버그 fix.

> v0.6.0에서 만든 moomoo-ax 전용 statusline은 repo/branch/sprint/ver/wt만 표시한다. 실 사용 중 컨텍스트 소진과 quota 블록이 안 보여 체감이 약했다. 참고 구현(my-agent-office/statusline)의 사용량 가시화 + 토글 패턴을 이식하고, 다른 사용자(예: 남편 환경)도 한 방에 적용할 수 있도록 `/ax-status` 스킬로 묶는다. 추가로 build 엔진을 codex로 위임할 수 있는 토글과, define 산출 직후 화면 wireframe을 한 장 HTML로 보여주는 옵션을 더한다. rubato admin 도그푸딩에서 발견한 preflight 스크립트 버그 3종도 hotfix 성격으로 함께 수정한다(다른 ax-deploy 트랙 정책/worktree/Vercel/cleanup PR 이슈는 v0.8 ax-deploy v2 묶음으로 분리).

## 범위 (7건)

### 1. B-STATUSLINE-V2 — ax-statusline.sh v2

현 `plugin/scripts/ax-statusline.sh`를 확장.

**추가 표시:**
- **CTX** — stdin JSON `.context_window.used_percentage` + `.context_window.context_window_size` → `used_k/total_k` + 퍼센트 바
- **5H** — `/tmp/claude-usage-cache.json`의 `.five_hour.utilization` + `resets_at` → 남은 시간 표기
- **7D** — `.seven_day.utilization` + `resets_at`
- 색상: 임계치(≥50 노랑/마젠타, ≥80 빨강)
- stale (reset_at 과거) → `⚠ stale` 표기

**반응형 레이아웃:**
- `COLUMNS` 기반 L(≥60) / M(≥40) / S 모드
- 각 모드별 바 너비 15 / 10 / 5

**토글 키 (settings.json):**
- `.statusline.ctx` / `.statusline.5h` / `.statusline.7d` / `.statusline.branch` / `.statusline.plugin`
- 기본값: 전부 `true`
- `CLAUDE_STATUSLINE_OFF=1` — 전역 off (참고 구현과 동일)

**유지:**
- 기존 repo / branch(+dirty) / sprint / ver / worktree 표시는 그대로. 위치/순서만 v2 레이아웃에 맞춰 조정.

### 2. B-FETCHUSAGE — fetch-usage.sh 이식

quota API → 캐시 생성 스크립트. my-agent-office/statusline에서 이식.

**동작:**
- statusline.sh가 매 refresh마다 백그라운드로 `&` 실행 (fire-and-forget)
- API 호출 성공 시 `/tmp/claude-usage-cache.json` 갱신
- TTL: 캐시가 일정 시간 이상이면 재조회, 아니면 스킵
- 실패 시 기존 캐시 유지 (상태 표시만 stale 분기)

**고려:**
- 원본 스크립트 라이선스/귀속 표시 (참고 구현이 이미 오픈소스면 헤더에 출처 명시)
- 의존성: `jq`, `curl` — install 단계에서 체크

### 3. B-AXSTATUS — /ax-status 스킬

서브커맨드 기반 스킬. `plugin/skills/ax-status/SKILL.md`.

**서브커맨드:**
- `/ax-status install` — 래퍼 생성 + `~/.claude/settings.json`의 `statusLine.command`를 래퍼 경로로 교체 + 기존값은 `statusLine.backup`에 저장 + 토글 키 기본값 주입
- `/ax-status uninstall` — `statusLine.backup` 복원 (없으면 제거)
- `/ax-status toggle <ctx|5h|7d|branch|plugin>` — 해당 키 flip
- `/ax-status on` / `off` — `CLAUDE_STATUSLINE_OFF` 프로세스 환경 지침 출력 (터미널 재시작 필요)
- `/ax-status show` — 현재 `statusLine.command` 경로 + 토글 상태 + 래퍼 존재 여부 + fetch-usage 캐시 상태 출력

**가드레일:**
- settings.json 수정 전 원본 백업 (타임스탬프 suffix 파일)
- 권한 요청 없이 `rm` 금지 — 삭제 대신 `mv ~/.Trash/` (`uninstall` 포함)
- 플러그인 미설치 상태에서 install 호출 시 에러 안내

### 4. B-HUDWRAPPER — 버전 무관 래퍼

`~/.claude/hud/ax-statusline.sh` — `/ax-status install`이 생성.

**역할:**
- 글로벌 `statusLine.command`가 이 래퍼를 가리킴
- 래퍼가 런타임에 설치된 team-ax 플러그인 경로를 resolve (`~/.claude/plugins/installed_plugins.json` 조회)
- 실제 `ax-statusline.sh`로 exec
- 플러그인 미설치/미발견 시 조용히 0 exit (statusline 공란)

**이유**: 플러그인 업데이트 시 cache 경로가 `/cache/lazyyoyo/team-ax/<ver>/...`로 바뀌므로, 글로벌 settings에 고정 경로를 박으면 매번 깨짐.

### 5. B-CODEXEXEC — ax-build executor 엔진 토글

build 단계의 코드 작성 주체를 claude / codex 중 선택.

**토글:**
- 위치: 프로젝트 `.claude/settings.json` 또는 `.ax-brief.md` 헤더에 `executor.engine: claude | codex` (기본 `claude`)
- `claude`: 현재처럼 `executor` 에이전트가 메인 세션 안에서 직접 작성
- `codex`: codex CLI 위임. `ax-review` 스킬이 codex를 호출하는 패턴과 동일한 구조로 build 위임

**구현 방식 (확정):**
- **신규 `execute` 스킬 분리** — executor 에이전트 내용을 `plugin/skills/execute/SKILL.md`로 추출 + `install-local-skills.sh` 확장으로 `~/.codex/skills/execute/` 동기화 + codex에 주입. ax-build는 토글에 따라 메인 세션 executor 에이전트 또는 codex `execute` 스킬을 호출.
- 사유: ax-build 전체를 codex로 넘기면 오케스트레이터(워트리/tmux/머지)까지 이관 부담이 커지므로, 코드 작성 단계만 떼서 위임하는 분리안이 깔끔.

**고려사항:**
- ax-build 오케스트레이터(워크트리/tmux/머지 흐름)는 그대로 유지. executor 단계만 분기.
- backpressure / TDD 가드는 두 엔진 모두에서 적용되도록 SKILL.md/스킬에 포함.
- 산출물 인터페이스 동일 — 어느 엔진이든 동일한 git diff / 커밋 메시지 형태.

**영역 침범 가드 (rubato admin 도그푸딩 피드백):**

executor가 "작업 X만 구현" 지시받아도 인접 작업 파일을 함께 수정하는 사고 (TypeScript 타입 의존이 강제). rubato admin-v0.2.0 작업 B(timeseries API)에서 `types.ts` 손대다 작업 D 영역(`AdminUserRow.readingTaskCount`, `users/route.ts`, mockup 2개)을 미리 수정 → uncommitted로 남김. 신규 `execute` 스킬과 기존 `executor` 에이전트 양쪽에 다음 가드 추가:

- 입력 prompt에 **차단 파일 경로 명시** (작업 범위 밖 파일 변경 금지)
- 작업 완료 후 **`git status` self-check** — 범위 밖 파일 변경 발견 시 즉시 보고
- 영역 침범 발견 시 **즉시 중단 + 오너 보고 의무**
- 공유 파일(예: 타입 정의)은 **공통 기반 단계에서 미리 작업** — ax-build 오케스트레이터가 공유 파일 사전 수정 후 작업 트랙 분기

### 6. B-WIREFRAME — define Phase C 선택적 wireframe.html

`ax-define` Phase C 마지막 단계에 옵션 산출.

**산출:**
- `docs/define/<버전>/wireframe.html` — 단일 정적 HTML
- 화면 단위 박스 레이아웃 + 화면 간 이동 화살표/링크
- **디자인 없음** — 박스/라벨/주요 영역 구분만. 색상/타이포그래피/실제 컴포넌트 사용 금지.
- 목적: scope.md 확정 flow를 화면 기준으로 한눈에 검토

**구현 방향:**
- HTML/CSS만으로 구성 (의존성 없음, 브라우저에서 더블클릭으로 열림)
- 화면 카드 그리드 레이아웃 — 각 카드 = 한 화면, 내부에 영역 박스(헤더/콘텐츠/액션 등)
- 화면 간 이동: 카드 간 화살표 또는 링크(`<a href="#screen-id">`)로 점프
- scope.md의 Story Map / flow 정보를 입력으로 받아 **에이전트가 생성** (스크립트 아님 — scope.md 자유서술 해석에 LLM 필요)

**선택성:**
- Phase C 끝에서 오너에게 `wireframe.html을 생성할까요?` 게이트
- 기본은 생성 안 함 (스코프가 작거나 화면이 명확한 경우 불필요)
- 생성 시 scope.md 옆에 산출 → ax-design / ax-build 시 참고

**고려사항:**
- **에이전트: `ux-designer` 재사용 (확정)** — 본업이 "화면 단위 플로우 설계 + 컴포넌트 필요 목록 산출"이라 wireframe 시각화와 직결. ax-design 단계 외에 define Phase C에서도 호출 가능하도록 SKILL 모드 분기 필요 (예: `mode: wireframe-only` — 디자인 토큰/컴포넌트 다루지 않음)
- **scope.md 화면 정의 섹션 표준 보강 (sprint-7 포함 확정)** — 기존 scope.md 템플릿에 Story 별 "화면" 섹션 표준 추가 (예: `### 화면: <이름>` + 영역 리스트 + 다음 화면 링크). ux-designer가 이 표준 섹션을 입력으로 wireframe 생성. 표준 없이 자유 서술이면 결과 품질 들쭉날쭉.

### 7. B-PREFLIGHTFIX — deploy-preflight 버그 3종 수정

rubato admin-v0.2.0 도그푸딩에서 발견한 `plugin/scripts/deploy-preflight.sh` 버그.

**수정 대상:**

1. **spec 경로 자동 탐지** — 현재 `docs/specs/` 하드코딩이라 rubato처럼 `dev/docs/specs/` subdirectory 구조 미인지. `find . -path "*/docs/specs" -type d` 또는 동등 로직으로 자동 탐지.
2. **`grep -c` 다중 결과 처리** — line 48에서 `[[: 0\n0` syntax error. `grep -c`가 여러 파일/경로에 대해 다중 라인 결과를 반환해서 산술 비교 실패. 합산 또는 단일 호출로 수정.
3. **본 트랙 scope 한정 마커 검사** — 다른 도메인 spec의 ⏳ planned 잔재가 본 트랙 deploy를 차단함 (admin 트랙이 docs 정리 외 트랙인데 다른 도메인 마커 11건으로 FAIL). 본 트랙 scope에서 변경된 파일에만 마커 검사 적용.

**비범위 (v0.8 ax-deploy v2 묶음):**
- 트랙별 정책 분기 (track-type 메타) — B-TRACKTYPE
- worktree 환경 호환성 — B-WTHOST
- Vercel ignored build 인지 — B-VERCELIGN
- cleanup PR 패턴 명문화 — B-CLEANUPPR

## 비범위

- `ax-review pr` 타입 구현 — v0.8 이후
- Hook 기반 spec-lifecycle 자동 강제 (PreToolUse) — v0.8+
- 대시보드 연동 / 북극성 지표 — v0.8+
- 도그푸딩 실측 1회 — sprint-6에서 미뤄둔 항목, 별도 세션에서 진행 예정 (sprint-7 범위 밖)
- 의존성 그래프 기반 머지 순서 자동화 — v0.8+
- team-ax 자기 진화 (meta loop) — v1.0

## 성공 기준

**statusline / /ax-status:**
- [ ] statusline v2가 CTX/5H/7D 3행을 터미널 폭에 맞게 렌더
- [ ] `settings.json`의 토글 키를 변경하면 해당 행이 즉시 표시/숨김
- [ ] `/ax-status install` 실행 후 글로벌 `~/.claude/settings.json`의 `statusLine.command`가 `~/.claude/hud/ax-statusline.sh` 래퍼로 교체됨
- [ ] `/ax-status uninstall`로 기존값 복원
- [ ] `/ax-status toggle 7d` 실행 → 7D 행 on/off 반영
- [ ] 다른 사용자(깨끗한 환경)가 플러그인 설치 + `/ax-status install`만으로 전 기능 동작
- [ ] 플러그인 버전 bump 후에도 래퍼가 자동으로 새 경로 resolve

**executor 토글:**
- [ ] `executor.engine = claude` (기본)에서 기존 ax-build 동작 회귀 없음
- [ ] `executor.engine = codex`로 전환 시 codex가 빌드 수행 + 동일 산출물(커밋/diff) 형태
- [ ] backpressure / TDD 가드 두 엔진 모두에서 동작
- [ ] 영역 침범 가드 동작 — 차단 파일 명시 + git status self-check + 침범 시 보고

**wireframe:**
- [ ] `ax-define` Phase C 끝 게이트 — 오너 선택으로 wireframe.html 생성 분기
- [ ] 생성 시 단일 HTML 파일이 의존성 없이 브라우저에서 열림
- [ ] 화면 박스 + 화면 간 이동이 시각적으로 구분됨 (디자인 없음 가드)
- [ ] scope.md 템플릿에 화면 정의 표준 섹션 추가 + ux-designer가 표준 섹션을 입력으로 사용

**preflight 버그:**
- [ ] spec 경로 자동 탐지 — `docs/specs/` subdirectory 구조 인지
- [ ] `grep -c` 다중 결과 처리 수정 — syntax error 제거
- [ ] 본 트랙 scope 한정 마커 검사 — 다른 도메인 잔재가 deploy 차단하지 않음

## 상태

- [x] BACKLOG 수집
- [x] sprint-6 피드백 반영 (statusline v1 → v2 필요성 확인)
- [ ] 태스크 분해 (sprint-7-task.md)
- [ ] 구현
- [ ] 검증 (자체 환경 + 남편 환경)
- [ ] v0.7.0 태그 + 배포
