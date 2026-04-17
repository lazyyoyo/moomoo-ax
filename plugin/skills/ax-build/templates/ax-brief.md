# .ax-brief — {작업명}

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

## 태스크
- [ ] {태스크 1} → 검증: {검증 방법}
- [ ] {태스크 2} → 검증: {검증 방법}

## 포트
{할당 포트}

## 완료 조건
- lint/test 통과
- codex code review APPROVE
- 커밋 완료
- dev server 띄우기 (포트 {포트})
- echo '{"status":"review-ready","port":{포트}}' > .ax-status
