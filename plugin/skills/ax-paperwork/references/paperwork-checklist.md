# paperwork 점검 체크리스트

ax-paperwork 실행 시 사용하는 세부 체크리스트.

## 1. 인벤토리

- [ ] `docs/specs/**/*.md` 전수 조회 (파일 수, 마지막 수정일, 줄 수)
- [ ] `docs/ARCHITECTURE.md` 존재 + 섹션 목록
- [ ] `BACKLOG.md` 존재 + inbox/ready/done 개수
- [ ] `CHANGELOG.md` 존재 + 최신 버전
- [ ] `docs/flows/**/*.md` 존재 여부
- [ ] `docs/DESIGN_SYSTEM.md` 존재 여부
- [ ] `CLAUDE.md` / `AGENTS.md` / `README.md` 존재 여부

## 2. 코드-문서 불일치

### 2-A. spec → 코드

- [ ] spec 내 백틱 심볼 (`functionName`, `ClassName`) 추출
- [ ] 각 심볼을 `grep -r` 또는 `Grep`으로 코드에서 탐색
- [ ] 0건이면 "누락" 후보
- [ ] 라우트(`/path`) 명시 건도 동일 방식

### 2-B. 코드 → spec

- [ ] public export 목록 (`src/**/index.ts` 등)
- [ ] API 라우트 (`app/api/**/route.ts`, `pages/api/**.ts`)
- [ ] env 변수 (`process.env.*` 참조)
- [ ] spec 전체에서 해당 식별자 grep
- [ ] 0건이면 "문서화 누락" 후보

## 3. 중복

- [ ] 같은 제목/섹션이 여러 문서에 존재 (예: "설치", "환경 변수")
- [ ] 내용이 70% 이상 유사하면 중복 후보 (heuristic)
- [ ] SSOT 후보 지정 + 나머지는 링크화 제안

## 4. Stale

- [ ] 문서 마지막 수정 커밋 날짜
- [ ] 문서가 참조하는 코드 영역의 마지막 수정 커밋 날짜
- [ ] 코드가 30일 이상 더 최신이면 stale 후보

## 5. 참조 무결성

- [ ] 마크다운 `[text](path)` 내부 링크 → 파일 존재 확인
- [ ] 상대 경로가 repo 밖을 가리키면 경고
- [ ] 코드 블록 내 `path/to/file.ts` 형태 경로 → 존재 확인
- [ ] 외부 `http(s)://` 링크는 검증 제외

## 6. 리포트 포맷

- [ ] `paperwork-report.md` 상단에 요약 숫자
- [ ] 카테고리별 표 (A/B/C/D)
- [ ] 각 행에 "조치 제안" 컬럼 포함
- [ ] 오너 승인이 필요한 항목은 `❓` 마크
- [ ] 자동 처리 가능한 항목은 `🤖` 마크

## 7. 가드레일 체크

- [ ] 수정 대상이 `.md`만인지 확인 (코드 파일 제외)
- [ ] 삭제 대상은 `mv ~/.Trash/`로만 처리
- [ ] ax-build 병렬 활성 여부 확인 (`.ax/workers/` 존재 또는 `ax-workers` tmux 윈도우 시 중단 권고)
