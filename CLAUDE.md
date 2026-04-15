# moomoo-ax

IT 제품 제작 자동화를 위한 Claude Code 플러그인 **team-ax** 개발 리포. 상세 정의는 `PROJECT_BRIEF.md`가 SSOT.

## 현재 단계

**plugin-first.** `plugin/` 하위에서 team-ax 플러그인만 만든다. meta/levelup/대시보드 등 상위 레이어는 이 단계에서 다루지 않는다 (PROJECT_BRIEF 참조).

## 디렉토리

```
moomoo-ax/
├── PROJECT_BRIEF.md       # SSOT
├── CLAUDE.md              # 이 파일
├── LICENSE, .env.example
├── .claude-plugin/        # 루트 marketplace.json
└── plugin/                # team-ax 플러그인
    ├── .claude-plugin/    # plugin.json + marketplace.json
    ├── agents/
    ├── skills/
    ├── hooks/
    └── scripts/
```

## 작업 규칙

- **선계획 후실행.** 범위 / 비범위 / 성공 기준을 3~5줄로 먼저 합의.
- 커밋·주석·문서는 한글. 변수·함수명은 영문.
- 키·토큰 하드코딩 금지. `.env`만.
- 파일 삭제는 `rm` 대신 `mv ~/.Trash/`.

## 인프라

- GitHub: https://github.com/lazyyoyo/moomoo-ax
- Supabase (ap-northeast-2): `aqwhjtlpzpcizatvchfb` — 현재 미사용, 후속 단계에서 연결
