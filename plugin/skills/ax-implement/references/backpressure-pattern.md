# Backpressure 패턴

Ralph Playbook 차용.

## 원칙

- **테스트 통과해야 커밋**: lint + typecheck + unit + build 통과 전 다음 태스크 금지
- **Fresh context per task**: 태스크마다 새 컨텍스트. 이전 태스크 발견 사항은 AGENTS.md 파일로 전달
- **plan 상태 갱신**: 완료/발견사항 기록. ⏳→✅
- **Capture the why**: 문서에 의도 기록 (왜 이렇게 구현했는지)

## 실행 흐름

```
태스크 선택 (plan 우선순위)
  ↓
구현 (executor 또는 design-engineer)
  ↓
자체 검증: lint + typecheck + unit + build
  ├─ 통과 → 커밋 + plan 갱신
  └─ 실패 → 수정 → 재검증 (통과까지 반복)
  ↓
다음 태스크
```

## 태스크별 커밋 규칙

- 태스크 하나 = 커밋 하나
- 커밋 없이 다음 태스크 진행 금지
- 태스크 완료 = 커밋 + plan.md 상태 갱신 (둘 다 안 하면 완료 아님)

## AGENTS.md 운영 학습 사항

- AGENTS.md는 에이전트가 다음 에이전트에게 전하는 운영 노하우
- CLAUDE.md(오너→에이전트 규칙)와 별개
- fresh context라서 이전 태스크 발견 사항을 파일로 전달해야 함
- 빌드/테스트 명령, 학습 사항 누적
- **운영 전용** — 진행 상태/진척도 넣지 마라
- **60줄 이하** 유지. 초과 시 요약
- major 버전 시작 시 정리 (코드에 없는 패턴은 삭제)
