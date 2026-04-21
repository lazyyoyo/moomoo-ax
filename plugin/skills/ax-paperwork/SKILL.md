---
name: ax-paperwork
description: "team-ax 문서 품질 관리. 코드-문서 정합성 탐지 + 중복/구식/참조깨짐 점검 → 수정 계획 → in-place 갱신. Use when: /ax-paperwork, 문서 정합성, 문서 최적화, spec 점검, 문서 리팩토링."
---

# /ax-paperwork

team-ax의 문서 품질 관리 스킬. **코드와 문서가 어긋났는가**를 자동으로 탐지하고 오너 승인 후 in-place로 갱신.

> **역할 경계**
> - ax-review doc = 단일 문서의 체크리스트 리뷰 (codex 위임)
> - ax-paperwork = 프로젝트 전체의 문서-코드-문서 간 정합성 점검 + 수정 계획 실행

## 입력

- 프로젝트 루트 (`docs/specs/`, `docs/ARCHITECTURE.md`, `BACKLOG.md`, `CHANGELOG.md`, `docs/flows/`, `docs/DESIGN_SYSTEM.md` 등)
- 코드 트리 (`src/`, `app/`, `components/` 등 프로젝트별)

## 출력

- `paperwork-report.md` — 발견 사항 + 수정 계획 + 오너 게이트
- 오너 승인 시 각 문서에 in-place 반영 (PR은 별도)

## 동작 순서

### 1단계 — 인벤토리 스캔

점검 대상 문서를 전수 스캔해서 표로 정리.

| 대상 | 파일 패턴 | 체크 항목 |
|---|---|---|
| 스펙 | `docs/specs/**/*.md` | 마지막 수정일, ⏳/✅ 마커, 참조 심볼 목록 |
| 아키텍처 | `docs/ARCHITECTURE.md` | 모듈/레이어 목록, 기술 스택 |
| 백로그 | `BACKLOG.md` | inbox/ready/done 섹션 상태 |
| 변경 이력 | `CHANGELOG.md` | 최신 버전 vs 태그 일치 |
| UX 플로우 | `docs/flows/**/*.md` | 현재 화면/라우트와 매칭 |
| 디자인 시스템 | `docs/DESIGN_SYSTEM.md` | 토큰/컴포넌트 목록 |

검증: `bash plugin/scripts/paperwork-inventory.sh` (프로젝트 루트에서 실행)

### 2단계 — 코드-문서 불일치 탐지

**A. spec에 있는데 코드에 없는 것 (누락/미구현)**

- spec이 언급하는 심볼/파일/라우트/API → 코드 grep으로 존재 확인
- 없으면 "누락 — spec 제거 또는 구현 필요"로 플래깅

**B. 코드에 있는데 spec에 없는 것 (은닉 기능)**

- 공개 API, 라우트, UI 컴포넌트, env 변수 중 spec 무언급 항목
- 있으면 "문서화 누락"으로 플래깅

### 3단계 — 중복 문서 식별

- 같은 주제가 2곳 이상 기술된 경우 (예: `CLAUDE.md`와 `README.md`에 동일한 설치 절차)
- SSOT를 한 곳으로 지정 + 나머지는 링크로 축약 제안

### 4단계 — 오래된 내용 플래깅

- 최근 `git log --since=30 days ago -- <doc>`과 대조
- 문서 마지막 수정일이 관련 코드 변경보다 훨씬 전이면 **stale 후보**
- 오너가 확인 후 refresh 또는 삭제

### 5단계 — 참조 무결성

- 마크다운 내부 링크 (`[text](path)`) 경로 존재 여부
- 코드 블록 안의 파일 경로가 실제 존재하는지
- 외부 URL은 검증 제외 (속도 이슈)

### 6단계 — 리포트 생성

`paperwork-report.md`를 다음 구조로 생성:

```
# Paperwork Report ({날짜})

## 요약
- 전체 문서 수: N
- 불일치: A건, 중복: B건, stale: C건, 깨진 참조: D건

## A. 코드-문서 불일치
### A-1. spec에 있는데 코드 없음
| spec | 심볼 | 조치 제안 |
|...|

### A-2. 코드에 있는데 spec 없음
| 파일 | 심볼 | 조치 제안 |
|...|

## B. 중복
## C. Stale 후보
## D. 참조 깨짐

## 수정 계획
- 각 항목별로 "문서 수정" / "스펙 추가" / "삭제" 중 하나를 제안
- 오너 승인 필요 항목은 ❓ 마크
```

### 7단계 — 오너 게이트

- 리포트 제출 후 AskUserQuestion으로 각 카테고리별 처리 방침 확인
- "모두 자동 수정" / "항목별 확인" / "리포트만" 선택지 제공

### 8단계 — in-place 갱신

오너 승인 항목만 적용:

- 문서 수정은 Edit 도구로 최소 변경
- 코드 수정은 **범위 밖** (ax-paperwork는 문서만 건드림)
- 코드 변경이 필요하면 BACKLOG inbox에 이관 후 ax-build로 넘김

### 9단계 — 요약 + 후속 이관

- 처리된 항목 수 / 이관된 항목 수 집계
- 처리 안 된 항목은 BACKLOG inbox에 "문서: {주제}"로 남김

## 가드레일

1. **문서만 수정** — 코드 파일(`.ts`/`.tsx`/`.py` 등)은 건드리지 않음. 코드 변경이 필요하면 BACKLOG 이관.
2. **삭제는 오너 승인 필수** — 문서 삭제는 `mv ~/.Trash/`로만, 오너 명시 승인 없이 실행 금지.
3. **대량 일괄 수정 금지** — 10건 이상의 수정은 카테고리별로 나눠서 승인받음.
4. **외부 URL 검증 제외** — 네트워크 호출로 속도 악화 방지.
5. **ax-build 중 실행 금지** — `.ax/workers/` 존재 또는 워커 프로세스 살아있으면 코드-문서 동기화가 부정확. ax-build 종료 후 실행.

## 참조

- `references/paperwork-checklist.md` — 점검 항목 상세
- `../ax-review/SKILL.md` — 문서 단건 리뷰 (doc 타입, codex 위임)
- `../ax-clean/SKILL.md` — 파일/디렉토리 정리 (문서 내용이 아니라 파일 존재 자체 점검)
