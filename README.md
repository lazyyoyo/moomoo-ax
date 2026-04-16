# moomoo-ax

IT 제품 제작 자동화 Claude Code 플러그인 **team-ax** 배포 리포.

> 오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인.

상세 정의는 [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md) 참고 (SSOT).

## 제공 기능 (v0.1)

| 스킬 | 설명 |
|---|---|
| `/ax-define` | 제품 버전 스코프 결정 + 스펙 in-place 갱신 + plan/write/review 검증 |
| `/ax-review` | 범용 리뷰 (doc/code/pr 분기 — v0.1은 doc 타입만 구현) |

## 요구 사항

- [Claude Code](https://claude.com/claude-code) 설치
- GitHub 저장소 구조의 프로젝트 (`docs/specs/`, `BACKLOG.md` 등을 따르는 것이 권장)

## 라이선스

[MIT](./LICENSE)
