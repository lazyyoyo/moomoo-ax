# design-review — {제품 이름} {제품 버전명}

## 게이트 결과

### 게이트 ①② (코드)

```
{design-gate.sh 출력}
```

### 게이트 ③ (Playwright 스크린샷)

| 화면 | desktop | mobile | 상태 |
|---|---|---|---|
| {화면명} | screenshots/{화면}-desktop.png | screenshots/{화면}-mobile.png | PASS/FAIL |

### 게이트 ④ (Judge 체크리스트)

**고정 루브릭:**

| # | 질문 | 판정 |
|---|---|---|
| F1 | DS 토큰만 사용했는가? | Yes/No |
| F2 | 레이아웃 규칙 준수? | Yes/No |
| F3 | loading 상태? | Yes/No |
| F4 | error 상태? | Yes/No |
| F5 | empty 상태? | Yes/No |
| F6 | 브랜드 색상 일관? | Yes/No |
| F7 | 타이포 위계 3단계+? | Yes/No |
| F8 | slop 없음? | Yes/No |

**동적 루브릭:**

| # | 질문 | 판정 |
|---|---|---|
| D1 | {UX 기반 자동 생성 질문} | Yes/No |

## 오너 피드백 이력

### 프리뷰 1회차

- **판정**: 승인 / 리젝
- **피드백**: {오너 피드백}
- **대응**: {어느 단계로 복귀했는지}
