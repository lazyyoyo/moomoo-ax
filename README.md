# moomoo-ax

IT 제품 제작 자동화 Claude Code 플러그인 **team-ax** 배포 리포.

> 오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인.

상세 정의는 [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md) 참고 (SSOT).

## 제공 기능 (v0.8)

| 스킬 | 설명 |
|---|---|
| `/ax-define` | 제품 버전 스코프 결정 + 스펙 in-place 갱신 + plan/write/review 검증 + (선택) wireframe.html 산출 |
| `/ax-build` | 개발팀 — plan(파일 분할) → 공통 기반 → **codex 워커 N개 병렬 라운드 (단일 브랜치, 파일 whitelist 격리)** → lead 일괄 커밋 → QA |
| `/ax-execute` | (codex 전용) 워커 프로토콜 엔진. inbox 과제 1건 실행 + whitelist 가드 + TDD + result.json 출력. 단일/병렬 공통 진입점 |
| `/ax-design` | 컴포넌트 단위 디자인 확정 (ax-build 안에서 자동 호출 또는 독립 실행) |
| `/ax-qa` | 통합 테스트 + code review + PR → main |
| `/ax-deploy` | 산출물 확인 → CHANGELOG → PR → 오너 승인 → 배포 |
| `/ax-paperwork` | 문서-코드 정합성 점검 + in-place 갱신 |
| `/ax-clean` | 미사용 파일/고아 문서/QA잔재 탐지 + 휴지통 이동 |
| `/ax-review` | 범용 리뷰 (doc/code/pr 분기) |
| `/ax-status` | statusline 설치/토글/상태 — `install` / `uninstall` / `toggle <ctx\|5h\|7d\|branch>` / `show` |
| `/ax-codex` | codex 스킬 동기화 관리 — `install` / `uninstall` / `status` (`ax-review` / `ax-execute`를 `~/.codex/skills/`로) |
| `/ax-help` | 스킬 목록 + 실행 순서 + 현재 상태 |

### v0.8 전제 (ax-build 사용 시)

- **codex CLI + 로그인** — `npm install -g @openai/codex` + `codex login`
- **tmux 안에서 claude 기동** — ax-build는 tmux 윈도우에 워커 pane을 split하는 구조
- **`/ax-codex install` 1회** — codex에 ax-execute 스킬 동기화 (`~/.codex/skills/ax-execute/`)

자세한 사전 점검은 `bash plugin/scripts/ax-build-orchestrator.sh precheck`으로 검증 가능.

## statusline (v0.7)

CTX 사용량 / 5H·7D quota를 한눈에 보여주는 multi-row statusline. 글로벌 한 번 설치 후 어느 프로젝트에서나 작동.

```bash
# 설치 (글로벌 ~/.claude/settings.json statusLine 교체 + 백업 자동 생성)
/ax-status install

# 특정 행만 끄기
/ax-status toggle 7d

# 현재 상태
/ax-status show

# 원복
/ax-status uninstall
```

플러그인 버전이 올라도 래퍼가 자동 resolve하므로 재설치 불필요.

## 요구 사항

- [Claude Code](https://claude.com/claude-code) 설치
- GitHub 저장소 구조의 프로젝트 (`docs/specs/`, `BACKLOG.md` 등을 따르는 것이 권장)

## 다른 플러그인과의 충돌

team-ax는 기존 `team-design` / `team-product` 플러그인과 키워드가 겹쳐 의도치 않은 에이전트가 트리거될 수 있다. 대상 프로젝트에서 비활성화 권장 — [docs/guides/plugin-compatibility.md](./docs/guides/plugin-compatibility.md) 참고.

## 라이선스

[MIT](./LICENSE)
