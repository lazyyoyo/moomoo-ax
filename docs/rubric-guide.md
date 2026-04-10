# Rubric 작성 가이드

## 구조

```yaml
items:
  - question: "Yes/No로 답할 수 있는 구체적 질문"
    priority: critical | high | medium | low
```

## Priority 기준

| priority | 의미 | No일 때 | 가중치 | 예시 |
|----------|------|---------|--------|------|
| **critical** | 이게 없으면 산출물 자체가 무의미 | 즉시 0점 | - | "문제 정의가 존재하는가?" |
| **high** | 핵심 품질 요소 | 큰 감점 | 3 | "성공 지표가 측정 가능한가?" |
| **medium** | 있으면 좋은 요소 | 보통 감점 | 2 | "Out of Scope이 명시되어 있는가?" |
| **low** | 부가적 품질 | 작은 감점 | 1 | "문서 형식이 일관적인가?" |

## 점수 계산

```
critical 항목 1개라도 No → 0.0 (나머지 무시)
그 외: (Yes 항목 가중치 합) / (전체 가중치 합)
```

## 좋은 질문 작성법

### Yes/No로 명확히 답할 수 있어야 함

```yaml
# 좋음
- question: "타겟 유저가 구체적 페르소나로 정의되어 있는가?"

# 나쁨 (모호)
- question: "유저 정의가 충분한가?"
```

### 산출물에서 확인 가능한 것만

```yaml
# 좋음
- question: "Core Job Statement가 'When/I want/so I can' 형식인가?"

# 나쁨 (주관적)
- question: "Job Statement가 설득력 있는가?"
```

### "지어내지 않았는가" 류는 피한다

LLM Judge가 판단하기 어려움. 대신 구조적 요건으로 바꾼다.

```yaml
# 나쁨
- question: "입력에 없는 정보를 지어내지 않았는가?"

# 좋음
- question: "Competing Solutions이 시드에 언급된 도구/대안을 포함하는가?"
```

### critical은 최소한으로

산출물의 존재 의미를 결정하는 항목만. 보통 1~2개.

```yaml
# critical 적합: 핵심 구조 존재 여부
- question: "Core Job Statement가 존재하는가?"
  priority: critical

# critical 부적합: 품질 판단
- question: "Job Map이 6단계 모두 채워져 있는가?"
  priority: high  # critical이 아님
```
