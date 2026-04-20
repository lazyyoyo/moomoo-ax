# sprint-7 태스크

## T0. B-FETCHUSAGE — fetch-usage.sh 이식

quota API → 캐시 생성 스크립트. 다른 작업의 전제.

- [ ] 참고 구현 확인 — `~/.claude/plugins/marketplaces/my-agent-office/plugins/statusline/scripts/fetch-usage.sh` 위치/라이선스 확인
- [ ] `plugin/scripts/fetch-usage.sh`로 이식 — 출처/귀속 헤더 포함
- [ ] 캐시 경로 고정 — `/tmp/claude-usage-cache.json`
- [ ] TTL 로직 — 최근 N초 내 갱신 시 스킵
- [ ] 실패 시 기존 캐시 유지 (덮어쓰기 금지)
- [ ] 의존성 체크 — `jq`, `curl` 없을 시 조용히 0 exit
- [ ] 실행권한 chmod +x

## T1. B-STATUSLINE-V2 — ax-statusline.sh v2

현 v1 확장. fetch-usage.sh 완료 후 작업.

- [ ] stdin JSON에서 `.context_window.used_percentage` / `.context_window.context_window_size` 파싱
- [ ] `fetch-usage.sh` 백그라운드 호출 + 캐시 읽기
- [ ] 반응형 레이아웃 — `COLUMNS` 기반 L(≥60) / M(≥40) / S 모드
- [ ] 바 너비 분기 — 15 / 10 / 5
- [ ] 임계치 색상 — ≥50 노랑/마젠타, ≥80 빨강
- [ ] stale 감지 — `resets_at` 과거 시 `⚠ stale` 표기
- [ ] 남은 시간 표기 — `resets_at` → `Xh Ym`
- [ ] 토글 키 파싱 — `jq`로 `~/.claude/settings.json`의 `.statusline.{ctx,5h,7d,branch,plugin}` 읽기 (기본 true)
- [ ] `CLAUDE_STATUSLINE_OFF=1` 전역 off 유지
- [ ] 기존 repo/branch(+dirty)/sprint/ver/worktree 표시 유지 + v2 레이아웃 통합
- [ ] 기본값 동작 검증 — 캐시 없을 때 CTX만 표시

## T2. B-HUDWRAPPER — 버전 무관 래퍼

`~/.claude/hud/ax-statusline.sh` 생성 로직. T3 install 서브커맨드가 호출.

- [ ] 래퍼 템플릿 작성 — `plugin/scripts/templates/hud-wrapper.sh`
- [ ] 런타임 resolve — `~/.claude/plugins/installed_plugins.json` 읽어 team-ax 설치 경로 조회
- [ ] resolve 실패 시 조용히 0 exit (statusline 공란)
- [ ] 찾은 경로의 `scripts/ax-statusline.sh`로 stdin/stdout 그대로 exec
- [ ] 실행권한 chmod +x

## T3. B-AXSTATUS — /ax-status 스킬

`plugin/skills/ax-status/SKILL.md`. T0/T1/T2 완료 후 통합.

- [ ] 스킬 스캐폴딩 — SKILL.md + references/ax-status-guide.md
- [ ] 서브커맨드 라우팅 — `install` / `uninstall` / `toggle` / `on` / `off` / `show`
- [ ] `install` 플로우
  - [ ] 플러그인 설치 여부 확인 — 미설치 시 에러 + 설치 안내
  - [ ] `~/.claude/hud/` 디렉토리 확보
  - [ ] 래퍼 생성 (T2 템플릿 사용)
  - [ ] `~/.claude/settings.json` 백업 — `settings.json.bak-YYYYMMDD-HHMMSS`
  - [ ] 기존 `statusLine`을 `statusLine.backup`으로 이동
  - [ ] `statusLine.command`를 래퍼 경로로 설정
  - [ ] 토글 키 기본값 주입 (없을 때만)
- [ ] `uninstall` 플로우
  - [ ] `statusLine.backup` 있으면 `statusLine`으로 복원, 없으면 제거
  - [ ] 래퍼 파일 `mv ~/.Trash/`
  - [ ] 토글 키는 유지 (재설치 대비) — 또는 옵션으로 정리
- [ ] `toggle <key>` — settings.json의 `.statusline.<key>` flip + 현재값 출력
- [ ] `on` / `off` — `CLAUDE_STATUSLINE_OFF` 안내 (셸 rc 수정 권장)
- [ ] `show` — 현재 래퍼 경로 / 토글 상태 / 래퍼 존재 여부 / 캐시 존재 여부 + TTL 출력
- [ ] 가드레일 — `rm` 금지, 백업 누락 시 중단
- [ ] references/ax-status-guide.md — 사용 예시 + 트러블슈팅

## T4. 검증

- [ ] 본인 환경 — `/ax-status install` → statusline 3행 표시 확인
- [ ] 토글 — `/ax-status toggle 7d` → 7D 숨김 확인
- [ ] 재설치 — `/ax-status uninstall` → `/ax-status install` 라운드트립 정상
- [ ] 플러그인 버전 bump 시뮬레이션 — 래퍼가 새 경로 resolve
- [ ] 남편 환경 — 플러그인 설치 + `/ax-status install`만으로 동작
- [ ] 기존 `.claude/settings.json` 프로젝트 레벨 설정과 충돌 확인 (글로벌이 덮어쓰는지, 아니면 프로젝트 우선인지)

## T5. B-CODEXEXEC — ax-build executor 엔진 토글

claude / codex 분기.

- [ ] 토글 키 정의 — `executor.engine: claude | codex`, 위치 결정(`.claude/settings.json` vs `.ax-brief.md`)
- [ ] `plugin/skills/execute/SKILL.md` 신규 — executor 에이전트 로직 이관 (TDD 흐름, backpressure, 작업 단위 diff/커밋 규약)
- [ ] `install-local-skills.sh` 확장 — `~/.codex/skills/execute/` 동기화 (ax-review 동기화 패턴과 동일)
- [ ] codex 호출 wrapper — ax-review 패턴(`codex run ...` 등) 참고
- [ ] `claude` 분기 — 기존 executor 에이전트 호출 흐름 유지 (회귀 없음)
- [ ] `codex` 분기 — codex CLI에 `execute` 스킬 주입 + 입력(파일 경로/태스크 명세) 전달 + 산출 회수
- [ ] backpressure / TDD 가드 — 두 엔진에 공통 적용되도록 명시 (SKILL.md + executor 에이전트 둘 다)
- [ ] 산출물 인터페이스 표준화 — 어느 엔진이든 git diff / 커밋 메시지 형태 동일
- [ ] 오케스트레이터(워크트리/tmux/머지) 그대로 유지 — executor 단계만 분기
- [ ] ax-build SKILL.md 갱신 — engine 토글 동작 명시 + execute 스킬 연결
- [ ] 회귀 테스트 — `claude` 기본 동작 변경 없음 확인
- [ ] **영역 침범 가드** (rubato admin 도그푸딩 피드백) — claude/codex 양쪽 적용
  - [ ] 입력 prompt에 차단 파일 경로 명시 (작업 범위 밖 파일 변경 금지)
  - [ ] 작업 완료 후 `git status` self-check — 범위 밖 파일 변경 발견 시 즉시 보고
  - [ ] 영역 침범 발견 시 즉시 중단 + 오너 보고 의무
  - [ ] 공유 파일(타입 정의 등)은 ax-build 오케스트레이터의 공통 기반 단계에서 미리 처리 → 각 트랙은 인접 영역 미수정

## T6. B-WIREFRAME — define Phase C 선택적 wireframe.html

UI wireframe 정적 HTML 생성.

- [ ] **생성 주체** — `ux-designer` 에이전트 재사용 (확정). `mode: wireframe-only` 분기 추가 — 디자인 토큰/컴포넌트 다루지 않고 화면 박스 + 이동만 산출
- [ ] `ux-designer` SKILL/agent 정의 갱신 — define Phase C에서도 호출 가능하도록 entry point 확장 + 모드 파라미터 처리
- [ ] **scope.md 화면 정의 표준 보강** (sprint-7 포함 확정)
  - [ ] 기존 scope.md 템플릿 확인 — `plugin/skills/ax-define/templates/scope.md.tmpl` 등
  - [ ] Story 별 "화면" 섹션 표준 추가 (예: `### 화면: <이름>` + 영역 리스트 + 다음 화면 링크)
  - [ ] ax-define Phase C에서 화면 섹션 채우기 가이드 + 검증
  - [ ] ux-designer가 표준 섹션을 입력으로 사용하도록 연결
- [ ] HTML 템플릿 작성 — `plugin/skills/ax-define/templates/wireframe.html.tmpl`
  - [ ] 화면 카드 그리드 레이아웃 (CSS grid)
  - [ ] 카드 내부 영역 박스 (헤더/콘텐츠/액션)
  - [ ] 화면 간 이동 — 화살표 또는 `<a href="#screen-id">` 링크
  - [ ] **디자인 가드** — 색상/타이포/실제 컴포넌트 사용 금지, 박스/라벨만
  - [ ] 의존성 없음 — 단일 HTML, 브라우저 더블클릭으로 열림
- [ ] 생성 로직 — scope.md 파싱 → 화면 노드 + edge 추출 → 템플릿 채움
- [ ] Phase C 끝 게이트 — `wireframe.html을 생성할까요?` 오너 확인. 기본 미생성
- [ ] 산출 경로 — `docs/define/<버전>/wireframe.html` (또는 scope.md 옆 위치 결정)
- [ ] ax-define SKILL.md 갱신 — Phase C 게이트 추가
- [ ] 산출 검증 — 샘플 scope.md → 생성된 wireframe.html을 브라우저에서 확인

## T7. B-PREFLIGHTFIX — deploy-preflight 버그 3종 수정

rubato admin-v0.2.0 도그푸딩 피드백.

- [ ] 현재 `plugin/scripts/deploy-preflight.sh` 코드 검토 + 버그 3종 재현
- [ ] **버그 1: spec 경로 자동 탐지** — `docs/specs/` 하드코딩 제거 → `find . -path "*/docs/specs" -type d` 또는 동등 로직. rubato의 `dev/docs/specs/` 같은 subdirectory 구조 인지
- [ ] **버그 2: `grep -c` 다중 결과 처리** — line 48 `[[: 0\n0` syntax error 제거. 다중 라인 결과 합산 또는 단일 호출로 수정
- [ ] **버그 3: 본 트랙 scope 한정 마커 검사** — 다른 도메인 spec의 ⏳ planned 잔재 무시. 본 트랙 scope에서 변경된 파일에만 마커 검사 적용
- [ ] 회귀 테스트 — 기존 정상 케이스(rubato 메인/yoyowiki 등) 동작 확인

## T8. 릴리즈

- [ ] plugin.json + marketplace.json 버전 bump (0.6.0 → 0.7.0)
- [ ] CHANGELOG.md 업데이트 — statusline v2 + /ax-status + executor 토글 + wireframe + preflight 버그 fix 섹션
- [ ] README 업데이트 — /ax-status 사용법 + executor 엔진 토글 + wireframe 옵션 추가
- [ ] BACKLOG.md inbox 해소 항목 → done 이관 (sprint-7)
- [ ] 프로젝트 레벨 `.claude/settings.json` 정리 — 글로벌 설치로 대체됐으므로 `statusLine` 제거 여부 결정
- [ ] 커밋 + PR + 태그 (`v0.7.0`)

## 검증 기준

### statusline v2

| # | 기준 | PASS 조건 |
|---|---|---|
| S1 | CTX 표시 | stdin JSON 기반 퍼센트/바/used_k-total_k 렌더 |
| S2 | 5H/7D 표시 | 캐시 존재 시 바/퍼센트/남은시간 렌더 |
| S3 | 반응형 | COLUMNS 변화 시 L/M/S 레이아웃 전환 |
| S4 | 토글 | settings.json 키 off → 해당 행 사라짐 |
| S5 | stale | resets_at 과거 시 `⚠ stale` 표기 |

### /ax-status

| # | 기준 | PASS 조건 |
|---|---|---|
| X1 | install | 글로벌 settings.json statusLine 교체 + 백업 생성 |
| X2 | uninstall | 백업 복원 + 래퍼 휴지통 이동 |
| X3 | toggle | 특정 행만 on/off 즉시 반영 |
| X4 | show | 현재 상태 요약 정확 |
| X5 | 가드레일 | `rm` 없이 `mv ~/.Trash/`로만 삭제 |

### 래퍼

| # | 기준 | PASS 조건 |
|---|---|---|
| W1 | resolve | installed_plugins.json에서 team-ax 경로 찾기 |
| W2 | 버전 변경 내성 | 플러그인 업데이트 후에도 재설치 없이 동작 |
| W3 | 폴백 | 플러그인 미설치 시 조용히 0 exit |

### executor 엔진 토글

| # | 기준 | PASS 조건 |
|---|---|---|
| E1 | 회귀 | `executor.engine = claude` 기본 동작 변경 없음 |
| E2 | codex 분기 | `executor.engine = codex` 시 codex가 빌드 수행 + 동일 산출물 |
| E3 | 가드 | backpressure / TDD 가드가 두 엔진 모두 적용 |
| E4 | 신규 스킬 | `plugin/skills/execute/` 존재 + `~/.codex/skills/execute/` 동기화 동작 |

### wireframe

| # | 기준 | PASS 조건 |
|---|---|---|
| F1 | 게이트 | Phase C 끝 오너 확인 후에만 생성 |
| F2 | 단일 HTML | 의존성 없이 브라우저 더블클릭으로 열림 |
| F3 | 화면 단위 | 화면 박스 + 화면 간 이동이 시각적으로 구분 |
| F4 | 디자인 가드 | 색상/타이포/실제 컴포넌트 미사용 (박스/라벨만) |
| F5 | 화면 표준 | scope.md 템플릿에 화면 정의 섹션 표준 + ux-designer가 입력으로 사용 |

### preflight 버그

| # | 기준 | PASS 조건 |
|---|---|---|
| P1 | 경로 자동 탐지 | `dev/docs/specs/` 등 subdirectory 구조 인지 |
| P2 | syntax 정상 | `[[: 0\n0` syntax error 사라짐 |
| P3 | 트랙 한정 | 본 트랙 변경 파일만 ⏳ 마커 검사, 다른 도메인 잔재 무시 |
| P4 | 회귀 | 기존 정상 케이스(yoyowiki 등) 동작 변경 없음 |

---

**의존 순서**: T0 → (T1, T2 병렬) → T3 → T4 → T5/T6/T7 (병렬) → T8

- T0 (fetch-usage): T1의 캐시 의존성 선행
- T1 (statusline v2) / T2 (래퍼 템플릿): 서로 독립, 병렬 가능
- T3 (/ax-status): T0/T1/T2 산출물을 조립
- T4: 본인 + 남편 환경 실측
- T5 (executor 토글) / T6 (wireframe) / T7 (preflight fix): statusline 묶음과 독립, 서로도 독립 — 3개 병렬 가능
- T8: 릴리즈
