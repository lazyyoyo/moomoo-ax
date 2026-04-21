# moomoo-ax

IT 제품 제작 자동화를 위한 Claude Code 플러그인 **team-ax** 개발 리포. 상세 정의는 `PROJECT_BRIEF.md`가 SSOT.

## 현재 단계

**plugin-first.** `plugin/` 하위에서 team-ax 플러그인만 만든다. meta/levelup/대시보드 등 상위 레이어는 이 단계에서 다루지 않는다 (PROJECT_BRIEF 참조).

## 스프린트 운영

moomoo-ax는 **스프린트 단위**로 돌린다. 각 스프린트는 **작업 범위 + 목표 버전명**을 명시한다.

- 문서 위치: `docs/sprints/sprint-N/sprint-N-plan.md`
- 스프린트 종료 시 해당 버전의 team-ax 플러그인을 배포한다.

### 진행 중

| 스프린트 | 목표 | 상태 |
|---|---|---|
| sprint-7 | team-ax **v0.7** 배포 — statusline v2 + executor 엔진 토글 + wireframe + preflight fix | 완료 (2026-04-20), hotfix v0.7.1/v0.7.2 포함 |
| sprint-8 | team-ax **v0.8** 배포 — ax-build 병렬 엔진 재설계 (worktree 제거 + Codex 워커 + 파일 whitelist) | plan 확정 (2026-04-21) |

## 디렉토리

```
moomoo-ax/
├── PROJECT_BRIEF.md       # SSOT
├── CLAUDE.md              # 이 파일
├── LICENSE, .env.example
├── .claude-plugin/        # 루트 marketplace.json
├── docs/
│   └── sprints/           # 스프린트별 plan/report
├── notes/                 # 논의·리서치 기록
└── plugin/                # team-ax 플러그인
    ├── .claude-plugin/    # plugin.json
    ├── agents/
    ├── skills/
    ├── hooks/
    └── scripts/
```

## 작업 규칙

- **선계획 후실행.** 범위 / 비범위 / 성공 기준을 3~5줄로 먼저 합의.
- **즉시 반영 금지.** 오너가 말한 내용을 바로 코드에 반영하지 않는다. 모든 작업은 BACKLOG inbox 또는 스프린트 계획에 먼저 넣고, PR을 생성하여 머지한다. 핫픽스도 동일.
- 커밋·주석·문서는 한글. 변수·함수명은 영문.
- 키·토큰 하드코딩 금지. `.env`만.
- 파일 삭제는 `rm` 대신 `mv ~/.Trash/`.

## 인프라

- GitHub: https://github.com/lazyyoyo/moomoo-ax
- Supabase (ap-northeast-2): `aqwhjtlpzpcizatvchfb` — 현재 미사용, 후속 단계에서 연결
