# clean 탐지 체크리스트

ax-clean 실행 시 사용하는 세부 탐지 규칙.

## A. 불필요한 파일

### A-1. 미사용 컴포넌트

- [ ] `src/components/**/*.tsx` 각 파일의 default export 이름 추출
- [ ] 전체 코드에서 `import ... from '{경로}'` 또는 `import '{경로}'` grep
- [ ] 0건이면 후보 (단, stories/tests는 참조로 인정 안 함 — 실사용 기준)
- [ ] 라우트 페이지(`app/**/page.tsx`)는 제외 (파일 기반 라우팅)

### A-2. 고아 시안/디자인

- [ ] `design/`, `figma/`, `assets/mockups/` 디렉토리
- [ ] spec에서 파일명 grep → 0건이면 후보

### A-3. 빈 디렉토리

- [ ] `find . -type d -empty -not -path './.git/*' -not -path './node_modules/*'`

### A-4. 캐시/잔재

- [ ] `.DS_Store` (macOS)
- [ ] `.turbo/`, `coverage/`, `.next/`, `dist/`, `build/` (gitignore 대상인데 실수 커밋된 경우)
- [ ] `*.log`, `npm-debug.log*`
- [ ] `.cache/`

## B. 관리 안 되는 문서

### B-1. 고아 spec

- [ ] `docs/specs/**/*.md` 각 파일명 추출
- [ ] `BACKLOG.md`, `CHANGELOG.md`, 다른 `docs/**/*.md`, 코드 주석에서 grep
- [ ] 0건이면 후보

### B-2. 오래된 flows

- [ ] `docs/flows/**/*.md` 파일이 참조하는 라우트
- [ ] 현재 코드의 라우트 목록과 diff
- [ ] flows에 있는데 라우트 없음 → 후보

### B-3. 미정리 versions

- [ ] `versions/v*/` 중 `git tag` 존재 + 60일 이상 경과
- [ ] CHANGELOG에 release 기록 있음
- [ ] → archive 후보 (즉시 이동은 아님)

### B-4. 미아카이브 레퍼런스

- [ ] `reference/v*/` 중 해당 버전이 release 완료
- [ ] `reference/archive/`로 이동 권고

## C. QA/디자인 잔재

### C-1. 루트 스크린샷

- [ ] repo 루트의 `*.png`, `*-snapshot.png`, `screenshot-*.png`
- [ ] `.ax/screenshots/`로 이동 제안 또는 삭제

### C-2. 임시 파일

- [ ] `.ax/workers/*/` 디렉토리 잔재 (build 완료 후)
- [ ] `HANDOFF.md` (처리 완료 후 잔존)

### C-3. env 백업

- [ ] `.env.bak`, `.env.old`, `.env.*.backup`, `.env.local.old`
- [ ] 모두 휴지통 이동 후보 (민감 정보 포함 가능 — 즉시 git 커밋 금지)

### C-4. 빌드 아티팩트

- [ ] `dist/`, `build/`, `.next/`, `out/`
- [ ] git-tracked이면 `git rm -r --cached` 후 `.gitignore` 추가 제안

## 후처리

- [ ] `.gitignore` 갱신 제안 항목 수집
- [ ] `.ax/screenshots/` 디렉토리 생성 + `.gitignore`에 추가
- [ ] 휴지통 이동 이력은 `clean-report.md` 하단에 타임스탬프 포함 기록

## 가드

- [ ] `git ls-files`에 있는 파일은 오너 명시 승인 필요
- [ ] `versions/` 전체는 기본 보호 (archive 이동만 허용)
- [ ] `.git/`, `node_modules/`, `.next/cache/`는 스캔 제외
- [ ] `.ax/workers/` 존재 또는 워커 프로세스 살아있을 시 중단
