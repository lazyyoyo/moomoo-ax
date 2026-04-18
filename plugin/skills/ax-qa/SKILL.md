---
name: ax-qa
description: "team-ax QA 스킬. 인벤토리 기반 체계적 검증 — 정적/동적/시각/접근성/성능 + 오너 게이트. Use when: /ax-qa, QA, 통합 테스트, 품질 검증."
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
- `.ax/screenshots/` — QA 스크린샷 (`.gitignore` 추가)

## 동작 순서

### 1단계 — QA 인벤토리 작성

**인벤토리 없이 테스트 시작 금지.**

flows/ + specs/ 기준으로 테스트 목록을 체계적으로 작성.

| 카테고리 | 내용 |
|---|---|
| happy-path | 각 화면의 정상 흐름 |
| off-happy-path | 에러, 빈 상태, 권한 없음, 네트워크 끊김 |
| 엣지 케이스 | 중복 요청, 대량 데이터, 긴 텍스트, 특수문자 |
| viewport | Desktop(1600x900) + Mobile(390x844) |

### 2단계 — 정적 검증

```bash
lint && typecheck && test && build
```

하나라도 실패 → QA FAIL → ax-build로 복귀.

### 3단계 — Codex 통합 code review

전체 변경사항(version branch vs main)에 대해 Codex 리뷰.

```bash
codex exec '$ax-review code'
```

- spec 정합 / DS 준수 / silent failure / 보안 / 텍스트 하드코딩 / 반복 패턴
- REQUEST_CHANGES → 수정 후 재리뷰

### 4단계 — Functional QA (동적 검증)

Playwright MCP로 인벤토리의 각 시나리오를 유저 입력 시뮬레이션.

- 화면 전환, 폼 입력, 버튼 클릭 등 실제 동작 검증
- off-happy-path 시나리오 포함 (에러/빈 상태/권한 없음)

### 5단계 — Visual QA

실제 데이터 상태에서 스크린샷 촬영 + 시각 검증.

- 레이아웃 깨짐, 오버플로우, 텍스트 잘림 탐지
- Desktop + Mobile 둘 다 캡처
- **스크린샷 저장 경로: `.ax/screenshots/`** (루트 방치 금지)

### 6단계 — Viewport 검증

Desktop(1600x900) + Mobile(390x844) 둘 다 테스트.

- 반응형 breakpoint 정상 동작
- 모바일에서 터치 타겟 크기 적절

### 7단계 — 접근성 (a11y)

axe-core로 접근성 검증.

- WCAG 기준 대비율
- alt text, ARIA 라벨
- 키보드 네비게이션

### 8단계 — 성능

Lighthouse 실행.

- Performance / Accessibility / Best Practices / SEO 점수
- 심각한 성능 이슈 (LCP > 4s 등) 시 FAIL

### 9단계 — 오너 수동 사용성 테스트

오너용 태스크 시나리오 제공. **편향 없는 표현, 답을 유도하지 않음.**

```
❌ "왼쪽 상단 메뉴에서 설정을 클릭하세요"
✅ "프로필 사진을 변경해보세요"
```

오너 수행 결과 기록 → 피드백 분류 (버그/UI/UX/기능 누락/OK).

### 10단계 — 판정 + 오너 게이트

**qa-report.md 작성:**

```markdown
# QA Report — {제품} vX.Y.Z

## 정적 검증: PASS/FAIL
## Code Review: APPROVE/REQUEST_CHANGES
## Functional QA: PASS/FAIL ({통과}/{전체} 시나리오)
## Visual QA: PASS/FAIL
## Viewport: PASS/FAIL
## 접근성: PASS/FAIL (axe-core 점수)
## 성능: PASS/FAIL (Lighthouse 점수)
## 오너 사용성: {피드백 요약}

## 판정: QA PASS / QA FAIL
```

**QA PASS 후 오너 게이트:**
1. 서버 띄우기 (기본 포트)
2. 오너에게 URL 안내 + 최종 동작 확인 요청 (AskUserQuestion)
3. 오너 OK → ax-deploy로 넘기기
4. 오너 수정 요청 → 수정 후 해당 단계 재검증

**QA FAIL:** qa-report.md에 실패 항목 기록 → ax-build로 복귀.

## 가드레일

1. **인벤토리 먼저** — 인벤토리 없이 "이것저것 눌러보기" 금지.
2. **코드 수정 금지** — 발견한 이슈는 qa-report.md에 기록만.
3. **off-happy-path 필수** — happy path만 테스트하면 FAIL.
4. **스크린샷 실제 확인** — 실제 렌더링 상태에서만 캡처.
5. **수동 테스트 중립** — 답을 유도하지 않는 시나리오.
6. **Viewport 둘 다** — Desktop + Mobile 필수.
7. **스크린샷 경로** — `.ax/screenshots/`에만 저장.
8. **오너 게이트 필수** — QA PASS 후 서버 띄우고 오너 확인 없이 deploy 금지.

## 참조

- `../ax-build/SKILL.md` — 선행 단계
- `../ax-deploy/SKILL.md` — 후속 단계
- `../ax-review/SKILL.md` — code review (Codex 위임)
