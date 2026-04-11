# rnd/

**meta loop 코드.** Research & Development — 외부 트렌드를 하네스에 자동 편입하는 상위 엔진.

**v1.0까지는 비활성**. team-product 대체(v0.5)와 실전 적용(v0.6~) 완료 후 v1.x에서 본격 구현.

## 구조

```
rnd/
├── scraper/  # 외부 트렌드 수집 (6시간 주기)
├── gates/    # 5축 필터 + A/B 실측 게이트
└── evolver/  # 하네스 편입 / graveyard 관리
```

## 파이프라인 (v1.x 구현 예정)

```
[수집]   6시간마다 스크래핑
         GitHub trending · AI 연구자 repo/X · RSS
             ↓
[1차]    5축 필터 (7/10 이상)
         자동화↑ · 마찰↓ · HARD 전환 · 토큰 효율 · 측정 가능
             ↓
[2차]    실측 A/B
         git stash로 임시 적용 → harness 점수 측정
             ↓
[판정]   점수 올랐으면 keep, 떨어지면 discard
             ↓
[기록]   본 것은 영구 기록, 거부는 graveyard
```

## 핵심 원칙

- **2차 게이트가 본체**. 필터 통과 후 자동 머지가 아니라 실측 점수 상승 시에만 편입.
- **LLM 주관이 아니라 숫자로 판정**. 자동으로 거르고, 검증 실패 시 자동 폐기.

상세 설계: `PROJECT_BRIEF.md`의 "하네스 진화 파이프라인" 섹션.
