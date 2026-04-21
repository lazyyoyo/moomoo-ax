---
name: ax-deploy
description: "team-ax 배포 스킬. 산출물 최종 확인 → CHANGELOG → PR → preview → 오너 승인 → 머지+태그 → 배포 → 정리. Use when: /ax-deploy, 배포, deploy, 릴리즈."
---

# /ax-deploy

team-ax의 배포 스킬. QA 통과 후 마지막 단계. **배포해도 되는 상태인가** 확인 후 실행.

> **역할 경계**
> - ax-qa = "제대로 동작하는가" (코드/동작 검증)
> - ax-deploy = "배포해도 되는가" (문서/상태 정리 + 실제 배포)

## 입력

- version branch (QA 통과 상태)
- `versions/vX.Y.Z/qa-report.md` (QA PASS 전제)

## 실행 위치

version branch. **원본 repo 세션 제약 없음.**
- 표준 흐름은 version branch에서 실행
- 독립 트랙이 필요하면 별도 version branch 또는 별도 리포 사용

## 동작 순서

### 1단계 — 산출물 최종 확인

배포 차단 사유가 있는지 체크. **1건이라도 실패하면 deploy 중단.**

| 체크 | 방법 | 실패 시 |
|---|---|---|
| `⏳ planned` 마커 잔존 | `docs/specs/` 전체에서 `⏳ planned` grep | 마커 제거 후 재실행 |
| scope.md 섹션 완성도 | 8섹션 모두 채워졌는지 확인 | 누락 섹션 채우기 |
| build-plan.md 태스크 완료 | `- [ ]` 미완료 항목 존재 여부 | 미완료 태스크 처리 |
| DS 프리뷰 페이지 최신화 | 신규 컴포넌트가 DS 프리뷰에 등록됐는지 | DS 갱신 |
| 미커밋 파일 | `git status` clean 확인 | 커밋 또는 정리 |

검증: `bash plugin/scripts/deploy-preflight.sh`

### 2단계 — CHANGELOG 작성

`CHANGELOG.md`에 이번 버전 내용 추가.

- scope.md §Story Map + build-plan.md에서 변경 내용 추출
- semver 판정 기록
- 날짜 + 버전 태그

### 3단계 — PR 생성

version branch → main PR 생성 (아직 없으면).

```bash
gh pr create --title "release: vX.Y.Z" --body "..."
```

### 4단계 — preview + 오너 확인

PR 생성 후 오너가 최종 동작을 눈으로 확인.

- localhost 또는 Vercel preview 서버 띄우기
- 오너에게 URL 안내 + 확인 요청 (AskUserQuestion)
- **승인 없이 머지 금지**

### 5단계 — main 머지 + 태그

오너 승인 후:

```bash
gh pr merge --merge
git tag -a vX.Y.Z -m "release: vX.Y.Z — {한 줄 설명}"
git push origin vX.Y.Z
```

### 6단계 — 배포 실행

프로젝트별 배포 명령 실행. 프로젝트 CLAUDE.md 또는 `package.json` scripts에서 배포 방법 확인.

- Vercel: `vercel --prod` 또는 git push 트리거
- 기타: 프로젝트별 배포 스크립트

### 7단계 — BACKLOG done 이관

이번 버전에서 해소된 BACKLOG inbox 항목을 done 섹션으로 이동.

### 8단계 — 잔재 정리

- Playwright 스크린샷 (루트에 방치된 `.png` 파일)
- 임시 파일 (`.ax/` 디렉토리 — `.ax/plan.json`, `.ax/workers/*/`). `.gitignore`에 있으면 자동 정리, 아니면 `mv ~/.Trash/`
- 워커 pane이 남아있으면 정리:
  ```bash
  bash plugin/scripts/ax-build-orchestrator.sh cleanup
  ```
- **version branch 삭제** (main 머지 완료 후):
  ```bash
  git branch -d version/vX.Y.Z
  git push origin --delete version/vX.Y.Z
  ```
- `reference/vX.Y.Z-*/` → `reference/archive/`로 이동

## 가드레일

1. **QA PASS 전제** — qa-report.md가 PASS가 아니면 deploy 시작 금지.
2. **산출물 체크 실패 시 중단** — 1건이라도 실패하면 배포 진행 금지.
3. **오너 승인 없이 머지 금지** — preview 보고 승인 받아야 함.
4. **CHANGELOG 누락 금지** — CHANGELOG 작성 없이 태그 생성 금지.
5. **version branch에서 실행** — 원본 repo 세션 제약 없음. 독립 트랙은 별도 브랜치 또는 별도 리포로 분리.

## 참조

- `plugin/scripts/deploy-preflight.sh` — 산출물 최종 확인 스크립트
- `../ax-qa/SKILL.md` — QA (선행 단계)
