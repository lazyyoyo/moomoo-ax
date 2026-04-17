---
name: ax-qa
description: "team-ax QA 스킬. 전체 머지 상태에서 통합 테스트 + code review + UX 플로우 검증. Use when: /ax-qa, QA, 통합 테스트, 품질 검증."
---

# /ax-qa

team-ax의 QA 스킬. **"이 버전의 모든 수정사항이 반영된 상태에서 정상 동작하는가"** 검증.

> ax-build 완료 후 실행. version branch에서 전체 머지 상태를 전제.

## 입력

- version branch (전체 머지 완료 상태)
- `versions/vX.Y.Z/scope.md`
- `versions/vX.Y.Z/build-plan.md`
- `flows/`

## 출력

- `versions/vX.Y.Z/qa-report.md` — 테스트 결과 + 판정
- QA 통과 시: PR 생성 (version/vX.Y.Z → main)

## 동작 순서

### 1. 정적 검증

```bash
# 전체 통과 확인
lint && typecheck && test && build
```

하나라도 실패 → QA FAIL → ax-build로 복귀.

### 2. Codex 통합 code review

전체 변경사항(version branch vs main)에 대해 Codex 리뷰.

```bash
codex exec '$ax-review code'
```

크로스커팅 이슈 점검:
- spec 정합
- DS 토큰 준수
- silent failure
- 보안
- 텍스트 하드코딩
- 반복 패턴

REQUEST_CHANGES → 수정 후 재리뷰.

### 3. UX 플로우 검증

flows/에 정의된 주요 플로우를 수동/자동 테스트.

- 각 화면 정상 렌더링
- 상태 변형 (loading/error/empty) 확인
- 화면 전환 정상

### 4. 판정

모든 검증 통과 → `versions/vX.Y.Z/qa-report.md` 작성:

```markdown
# QA Report — {제품} vX.Y.Z

## 정적 검증: PASS
## Code Review: APPROVE
## UX 플로우: PASS

## 판정: QA PASS
```

### 5. PR + main 머지

QA PASS 후:
1. PR 생성 (version/vX.Y.Z → main)
2. 오너 최종 승인
3. 머지 + 태그

## QA FAIL 시

qa-report.md에 실패 항목 기록 → ax-build 6단계(오너 확인)로 복귀 → 수정 후 재QA.

## 가드레일

- version branch 전체 머지 상태에서만 실행
- 정적 검증 실패 시 code review 스킵 (비용 절약)
- PR 생성은 QA PASS 후에만
