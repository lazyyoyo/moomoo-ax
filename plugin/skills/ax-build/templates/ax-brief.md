# .ax-brief — {작업명}

> **⚠ DEPRECATED (v0.8)**: v0.7까지 워크트리 기반 병렬 워커의 공유 지시서로 사용. v0.8은 워커별 `.ax/workers/<task_id>/inbox.md`로 대체. 새 포맷은 `worker-inbox.md.tmpl` 참조. 이 파일은 legacy 참조용으로 당분간 유지, v0.9에서 제거 예정.


## 작업 내용
{작업 설명}

## 디자인
{필요 — ax-design 실행 / 불필요 — 바로 구현 / DS 조합}

## 입력 파일
- versions/{버전}/scope.md
- versions/{버전}/build-plan.md
- flows/{기능명}.md
- docs/specs/{스펙}.md
- DESIGN_SYSTEM.md

## 영역 (영역 침범 가드 발동 조건)

executor.engine=claude/codex 양쪽 모두 이 섹션을 반드시 사용한다. codex 위임 시 `--allow` / `--block` 인자에 그대로 전달된다.

### 허용 영역
- {수정 가능한 파일/디렉토리 글롭}

### 차단 영역
- {다른 트랙이 점유 중인 파일/디렉토리}
- {공통 기반에서 처리되어야 할 공유 파일 — 본 작업에서 만지지 않음}

## 태스크
- [ ] {태스크 1} → 검증: {검증 방법}
- [ ] {태스크 2} → 검증: {검증 방법}

## 포트
{할당 포트}

## 완료 조건
- lint/test 통과
- `git status --porcelain`에 차단 영역 변경 0건 (영역 침범 가드)
- codex code review APPROVE
- 커밋 완료
- dev server 띄우기 (포트 {포트})
- echo '{"status":"review-ready","port":{포트}}' > .ax-status
