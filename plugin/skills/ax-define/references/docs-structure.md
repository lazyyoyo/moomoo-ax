# 제품 문서 구조 — BACKLOG / scope / CHANGELOG 3-문서

team-ax가 적용되는 **각 제품 리포** 안에서 사용하는 3-문서 구조. ROADMAP은 제거.

## 세 문서 책임 분리

| 파일 | 책임 | 시점 | 주체 |
|---|---|---|---|
| `BACKLOG.md` | **인박스 전용** — 버전 미배정 아이디어. (`[next]`·`[future]` 우선순위 태그 가능) | 모든 시점 | 누구나 (`/backlog add`) |
| `versions/vX.Y.Z/scope.md` | **버전별 SSOT** — JTBD + Story Map + SLC + 수정 계획/로그/리뷰 | 사이클 진행 중 | `product-owner` (Phase A) → `analyst` (Phase C) |
| `CHANGELOG.md` | **배포 완료 기록** — Keep a Changelog 포맷, 유저·외부 대상 | 배포 후 | (deploy 단계 — 후속 스프린트) |

> **플러그인 v0.1에서는** scope.md가 `versions/undefined/scope.md`에 머문다 (Phase B 폴더 승격은 v0.2 도입). CHANGELOG는 작성 대상이 아니다.

## 항목 생애 흐름

```
BACKLOG.md (inbox)
   │  ← 아이디어 캡처만. 버전 미배정.
   │
   │ define Phase C write — analyst가 채택 항목을 inbox에서 제거
   ▼
versions/vX.Y.Z/scope.md (또는 versions/undefined/scope.md)
   │  ← 해당 버전의 JTBD + Story Map + 수정 계획/로그/리뷰
   │  ← build 중에는 태스크 상태(planned/in-progress/done)만 in-place 갱신
   │
   │ deploy 단계 (후속 스프린트)
   ▼
CHANGELOG.md
      ← 해당 버전 블록 추가 (Added/Changed/Fixed/Removed/Security)
      ← scope.md는 versions/vX.Y.Z/에 아카이브로 잔존
```

## ROADMAP 제거 근거

team-product 레퍼런스(rubato)에서 다음 문제가 확인됨:

1. **이중 유지** — BACKLOG.md ↔ ROADMAP.md가 같은 항목을 두 번 적어 동기화 부담.
2. **삼중 동기화** — ROADMAP.md ↔ CHANGELOG.md도 과거 버전 기록이 겹쳐, 한 항목이 세 문서에 동시 존재.
3. **무용성** — define / plan / build / qa / deploy 어느 단계에서도 ROADMAP을 1차 입력으로 읽지 않았다. 역할이 BACKLOG(미래)와 CHANGELOG(완료)로 자연 분산.
4. **전략 메타 혼입** — ROADMAP에 "유료화 경계", "PMF 가설" 같은 전략 메모가 끼어 들어가 product lifecycle 문서로서의 단일 책임이 깨졌다.

> **처방** — ROADMAP 제거. 전략 메타는 상위 문서(`PROJECT_BRIEF.md` 또는 `strategy/`)로 이관. product lifecycle 문서는 BACKLOG / scope / CHANGELOG 3개로 끝.

## CHANGELOG 포맷 (개념만)

Keep a Changelog 포맷 — https://keepachangelog.com/

```markdown
## [1.7.0] - 2025-XX-XX

### Added
- 마이페이지: 프로필 카드 / 테마 변경 / 비밀번호 변경

### Changed
- 정렬 기준을 등록일 → 우선순위로 변경

### Fixed
- 책 추가 시 표지 누락 (#123)
```

> **CHANGELOG는 define 범위 밖.** 플러그인 v0.1에서는 작성·갱신하지 않는다. deploy 단계 도입 시(후속 스프린트) `analyst` 또는 deploy 전담 에이전트가 책임진다.

## 단계별 상태 전환 규칙 (요약)

| 대상 | 전환 | 타이밍 | 주체 |
|---|---|---|---|
| `BACKLOG.md` inbox 항목 | **제거** (이번 버전 채택) | define Phase C write | `analyst` |
| `docs/specs/` `⏳ planned` 마커 | **추가** | define Phase C write | `analyst` |
| `scope.md` §수정 로그 | **체크 (`- [x]`)** | define Phase C write | `analyst` |
| `scope.md` §리뷰 판정 | **`APPROVE`** | define Phase C review | `ax-review doc` 스킬 (codex 위임) |
| `scope.md` 태스크 상태 | `planned → in-progress` | build 진입 시 | (후속 스프린트) |
| `scope.md` 태스크 상태 | `in-progress → done` | build 태스크 완료 시 | (후속 스프린트) |
| `docs/specs/` `⏳ planned` 마커 | **제거** | deploy (배포 성공 후) | (후속 스프린트) |
| `CHANGELOG.md` 해당 버전 블록 | **신규 추가** | deploy (배포 성공 후) | (후속 스프린트) |
| `scope.md` 최종 상태 | **아카이브** | deploy (배포 성공 후) | (후속 스프린트) |

> 플러그인 v0.1 범위는 위 표의 `define` 줄만. 나머지 줄은 **규칙으로 확정만** 하고 구현은 후속 스프린트.

## 참고

- 이전 단계: `spec-lifecycle.md`
- 외부 표준: https://keepachangelog.com/
