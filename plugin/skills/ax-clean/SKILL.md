---
name: ax-clean
description: "team-ax 디렉토리 정리 스킬. 미사용 파일/고아 문서/QA잔재 탐지 → 오너 승인 → 휴지통 이동. Use when: /ax-clean, 정리, 잔재 제거, 디렉토리 최적화, 미사용 파일."
---

# /ax-clean

team-ax의 디렉토리/파일 정리 스킬. **이 파일 아직 필요한가?** 자동 탐지 + 오너 승인 후 휴지통으로 이동.

> **역할 경계**
> - ax-paperwork = 문서 내용의 정합성
> - ax-clean = 파일/디렉토리 존재 자체의 필요성

## 입력

- 프로젝트 루트
- 선택적 대상 경로 (`--scope docs/` 등)

## 출력

- `clean-report.md` — 탐지 결과 + 정리 제안
- 오너 승인 시 `mv ~/.Trash/`로 이동 (영구삭제 금지)

## 동작 순서

### 1단계 — 탐지 스캔

`bash plugin/scripts/clean-scan.sh`로 후보 목록 생성.

**A. 불필요한 파일**

| 유형 | 판정 기준 |
|---|---|
| 미사용 컴포넌트 | 파일 경로를 import/참조하는 곳이 0건 |
| 고아 시안 | `.figma`/`design/` 파일 중 spec 참조 없음 |
| 빈 디렉토리 | 파일이 0개인 디렉토리 |
| 캐시 잔재 | `.DS_Store`, `.turbo/`, `coverage/`, 기타 gitignore된 잔재 |

**B. 관리 안 되는 문서**

| 유형 | 판정 기준 |
|---|---|
| 고아 spec | `docs/specs/` 내 파일이 다른 문서/코드에서 참조되지 않음 |
| 오래된 flows | `docs/flows/` 중 현재 라우트/화면과 매칭되지 않음 |
| 미정리 versions | 60일 이상 경과한 `versions/v*` 중 release 완료분 |
| 미아카이브 레퍼런스 | `reference/v*/` 중 archive로 이동 안 된 완료분 |

**C. QA/디자인 잔재**

| 유형 | 판정 기준 |
|---|---|
| 루트 스크린샷 | 루트의 `*.png`, `*-snapshot.png` — `.ax/screenshots/`로 이동 또는 삭제 |
| 임시 파일 | `.ax-status`, `.ax-brief.md` (build 완료 후에도 남음) |
| `.env` 백업 | `.env.bak`, `.env.old`, `.env.*.backup` |
| 빌드 아티팩트 | repo에 실수 커밋된 `dist/`, `build/`, `.next/` |

### 2단계 — 리포트 생성

`clean-report.md`:

```
# Clean Report ({날짜})

## 요약
- 탐지 후보: N건 (A:N_a / B:N_b / C:N_c)
- 예상 회수 용량: M MB

## A. 불필요한 파일
| 경로 | 크기 | 판정 | 조치 제안 |
|...|

## B. 관리 안 되는 문서
## C. QA/디자인 잔재

## 정리 계획
- 즉시 삭제 (휴지통 이동) 가능
- 오너 확인 필요
- 보류 (근거 필요)
```

### 3단계 — 오너 게이트

AskUserQuestion으로 카테고리별 승인:

- "A 전체 승인" / "항목별 확인" / "A 건드리지 말기"
- B, C 각각 동일

### 4단계 — 휴지통 이동

오너 승인 항목만:

```bash
mkdir -p ~/.Trash/ax-clean-{날짜}
mv {파일} ~/.Trash/ax-clean-{날짜}/
```

- **`rm` 금지** — CLAUDE.md 규칙
- git-tracked 파일은 `git rm` 후 커밋 대신 **일단 보류** (오너 재확인)

### 5단계 — 후처리

- `.gitignore` 추가 제안 (캐시 잔재 재발 방지)
- `.ax/screenshots/` 디렉토리 생성 + `.gitignore` 등록 (QA 스크린샷 정책)
- 회수 용량 / 이동 파일 수 집계

### 6단계 — 요약 + 후속 이관

- 보류된 항목은 `BACKLOG.md` inbox에 "clean: {파일}" 형태로 남김
- 정리 결과를 `clean-report.md` 하단에 "완료" 섹션으로 추가

## 가드레일

1. **삭제 금지, 이동만** — 모든 정리는 `mv ~/.Trash/`로. `rm -rf` 금지.
2. **git-tracked 보호** — `git ls-files`에 있는 파일은 오너 명시 승인 없이 이동 금지.
3. **대량 이동 확인** — 50건 이상 이동 시 오너 재확인 (카테고리별 분할 승인).
4. **ax-build 중 실행 금지** — `.claude/worktrees/` 활성이면 중단 권고 (워크트리 깨질 위험).
5. **versions/ 삭제 금지** — release 완료된 versions도 기록. 정리는 별도 archive 정책 (v0.7+).

## 참조

- `references/clean-checklist.md` — 탐지 규칙 상세
- `plugin/scripts/clean-scan.sh` — 탐지 스캔 스크립트
- `../ax-paperwork/SKILL.md` — 문서 내용 정합성 (파일 존재는 여기서)
