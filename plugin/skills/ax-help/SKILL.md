---
name: ax-help
description: "team-ax 플러그인 안내. 스킬 목록, 실행 순서, 현재 프로젝트 상태 표시. Use when: /ax-help, /ax, team-ax 뭐야, 어떻게 써."
---

# /ax-help

team-ax 플러그인 안내.

## 표시 내용

### 1. team-ax 소개

> IT 제품 제작 자동화 플러그인. 오너가 의도를 전달하면 define → build → qa → deploy까지 자동화.

### 2. 스킬 목록 + 실행 순서

```
/ax-define  →  /ax-build  →  /ax-qa  →  /ax-deploy
  (PM)         (개발팀)       (QA)       (배포)
```

| 스킬 | 역할 | 설명 |
|---|---|---|
| `/ax-define` | PM | scope 확정 — JTBD/Story Map/SLC/스펙 갱신 |
| `/ax-build` | 개발팀 | plan → 공통 기반 → 구현(병렬) → 오너 확인 → 머지 |
| `/ax-qa` | QA | 인벤토리 기반 통합 테스트 + 오너 게이트 |
| `/ax-deploy` | 배포 | 산출물 확인 → CHANGELOG → PR → 오너 승인 → 배포 |

**보조 스킬:**

| 스킬 | 설명 |
|---|---|
| `/ax-design` | 컴포넌트 단위 디자인 확정 (ax-build 안에서 자동 호출되거나 독립 실행) |
| `/ax-review doc` | 문서 리뷰 (codex 위임) |
| `/ax-review code` | 코드 리뷰 (codex 위임) |
| `/ax-execute` | 워커 프로토콜 엔진 (codex 전용). ax-build가 병렬 워커마다 호출. 단일 수동 실행도 동일 진입점 |
| `/ax-status` | statusline 설치/토글/상태 |
| `/ax-codex` | codex 스킬 동기화 관리 (`ax-review`/`ax-execute` → `~/.codex/skills/`) |
| `/ax-paperwork` | 문서-코드 정합성 점검 + in-place 갱신 |
| `/ax-clean` | 미사용 파일/고아 문서/QA잔재 탐지 + 휴지통 이동 |
| `/ax-help` | 이 안내 |

### 3. 현재 프로젝트 상태

자동 감지 로직:

```
versions/undefined/ 존재         → define 진행 중
versions/vX.Y.Z/ 존재            → define 완료
version/vX.Y.Z 브랜치 존재        → build 진행 중 또는 완료
versions/vX.Y.Z/qa-report.md 존재 → QA 완료
versions/vX.Y.Z/build-plan.md 존재 → build plan 수립됨
.ax/plan.json 또는 .ax/workers/ 존재 → 병렬 빌드 진행 중
.ax/workers/*/pid 살아있음         → 워커 live
```

**출력 예시:**
```
📍 현재 상태: build 진행 중

  define: ✅ 완료 (v1.9.0)
  build:  🔄 진행 중 (2/3 작업 완료)
  qa:     ⏳ 대기
  deploy: ⏳ 대기

  워커: 2개 활성 (.ax/workers/T1, T2 — 백그라운드 프로세스)
```

### 4. build 중 안전 작업 가이드

build가 병렬 진행 중일 때 (워커 프로세스 활성):

```
✅ 안전한 작업 (메인 세션에서):
  - BACKLOG.md 정리
  - 문서 수정 (CLAUDE.md, README.md 등 워커 whitelist 밖)
  - notes/ 작성
  - 스펙 리뷰

❌ 피해야 하는 작업:
  - 워커가 건드리는 파일 수정 (.ax/workers/*/inbox.md의 whitelist 참조)
  - git 커밋/푸시 (lead 일괄 커밋 규칙 위반)
  - version branch 조작 (빌드 상태 깨질 위험)
```

## 구현

1. `versions/` 디렉토리 스캔
2. `git branch` 확인
3. `.ax/plan.json` / `.ax/workers/` 존재 확인
4. `.ax/workers/*/pid` 파일이 가리키는 프로세스가 살아있는지 확인
5. qa-report.md / build-plan.md 존재 확인
6. 결과 조합 → 상태 출력
