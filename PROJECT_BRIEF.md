# moomoo-ax

자기 하네스를 진화시켜 IT 제품 제작을 자동화하는 시스템.

## 한 줄 미션

> **오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인.**

이 파이프라인을 담은 배포 제품이 **team-ax** (Claude Code 플러그인).

## 현재 단계

**team-ax 플러그인 제작에만 집중.** 그 외의 루프(사용자 product loop, 상위 meta loop, 대시보드, 하네스 자기 진화 등)는 전부 **장기 비전**으로 밀어둔다. 아래 "장기 비전" 섹션 참고.

현재 리포는 `plugin/` 하위 team-ax 제작 공간 + 정의 문서(이 파일)만 유지한다.

## 용어

| 용어 | 의미 |
|---|---|
| **moomoo-ax** | 이 프로젝트 전체. ax = AI Transformation |
| **team-ax** | 배포 제품. Claude Code 플러그인 (team-product/team-design 패밀리) |
| **오너 개입 횟수** | 북극성 지표. 의도 전달 이후 오너가 손대야 했던 횟수 |

## 북극성 지표

**오너 개입 횟수 (↓)**

team-product을 쓰며 체감한 진짜 병목 —

- design에서 "아 이거 아니라고 내가 하나씩 집어줄게"로 오너가 결국 다 함
- implement 자잘한 버그 수정도 오너 몫
- 의도 전달 이후에도 오너가 손을 뗄 수 없음

기대치에 맞으면 개입할 일이 없고, 개입이 없으면 횟수가 줄어든다. "기대치 충족"은 질적 지표, "개입 횟수"는 그것의 정량 대리지표. 보조 지표(단계별 토큰, 루브릭 점수, iteration 수)는 이 북극성을 설명하는 선들이다.

## 설계 원칙

### 1. 의도 캡처는 단 한 번

오너와의 대화는 초기 의도 수렴에만 쓴다. 이후 단계는 전부 자동이어야 한다. 지금 오너가 손대는 건 "원래는 자동이어야 하는데 안 돼서" 그런 것이다. 이걸 해소하는 게 moomoo-ax의 존재 이유.

### 2. 자동이되, 보인다

오너는 개입하지 않지만, 진행 상태와 산출물을 **언제든 관찰**할 수 있어야 한다. 무개입 ≠ 블랙박스.

### 3. 판단과 실행의 분리

같은 사람(yoyo)이 두 역할을 다 하기 때문에 **도구가 모드를 분리**해줘야 한다.

- **판단**: "이거 고쳐야겠다", "이 기준으로", "이건 폐기"
- **실행**: 결정된 대상/기준으로 루프 돌리기, iteration, 점수 산출

### 4. 실험 결과물 ≠ 프로젝트 정의

팀-ax를 자기 자신에 돌린 결과(dogfooding)가 생겨도, 그건 참고용이다. **`PROJECT_BRIEF.md`가 SSOT**. 실험 결과가 오너 승인 정의로 승격될 수는 있어도 둘은 같지 않다.

### 5. 구축 순서 — product → meta → levelup

"뭘 개선할지" 사전 정의 없이 levelup(플러그인 품질 루프)부터 돌리면 대상이 공허해진다. 배포 제품이 실제로 돌아야 → 개입 횟수/토큰 관찰이 의미 있어야 → levelup 개선 대상이 공허하지 않다.

### 6. Progressive Codification

자연어 스킬(`SKILL.md`)은 AI의 자의적 해석과 토큰 낭비의 원인. **절차적 결정론 step만 script/코드로 굳히고, 해석·판단·생성은 자연어**로 둔다. 검증 규칙을 AST로 뽑아내는 식의 과도한 코드화는 타깃이 아니다. 안정화된 단계를 코드로 굳혀가는 것이 하네스 자기 진화의 실체.

## 성공 기준 (v1.0)

- [ ] yoyo가 주요 작업에서 team-ax 기반으로 implement→preview 구간을 개입 없이 완주
- [ ] jojo가 자기 제품에 team-ax를 독립 사용
- [ ] 오너 개입 횟수가 초기 측정 대비 70% 이상 감소
- [ ] team-product을 대체해 모든 프로젝트에서 team-ax 사용
- [ ] 피드백 데이터가 누적·소화되는 주기가 확립
- [ ] 각 stage의 deterministic 규칙이 script로 추출되어 안정성·토큰 효율 개선 (Progressive Codification v1.0 완결형)

## 장기 비전

현재는 plugin-first라 미뤄두지만, 원래 설계의 바깥 레이어. **v1.0 이후 또는 상황 전환 시 다시 꺼낸다.**

- **product loop** — 사용자가 team-ax를 돌려 외부 제품을 만드는 루프. moomoo-ax의 외부 가치가 발생하는 곳.
- **meta loop** — levelup + product 양쪽을 지켜보고 하네스 자체를 진화시키는 상위 사이클. 대시보드가 이 루프의 구현체.
- **하네스 자기 진화** — 외부에서 좋은 패턴이 나오면 자동 흡수. 수집 → 필터 → A/B 실측 게이트 → 편입/폐기. 사람이 수동으로 "이거 써보자" 하지 않아도 업데이트되는 구조.
- **deploy 자동 구간 확장** — localhost → preview → production을 비용 순으로 점진 자동화.
- **피드백 채널 2종** — 산출물↔배포물 자동 diff(묵시), `/ax-feedback` CLI(명시).

## 기술 스택

| 영역 | 스택 |
|---|---|
| 배포 제품 | Claude Code plugin `team-ax` |
| 워커 | Claude CLI conductor + Codex worker (`codex exec`) |
| eval | LLM Judge (rubric 기반, "오너 기대치" 항목 포함) |
| 코드 호스팅 | GitHub (lazyyoyo/moomoo-ax) |
| (장기) 로그 / 대시보드 | Supabase (ap-northeast-2, `aqwhjtlpzpcizatvchfb`) + Next.js 16 / Vercel |

## 사용자

- **yoyo** — 오너 겸 주요 사용자 (rubato, rofan-world, dashboard, moomoo-ax 자체)
- **jojo** — kudos/sasasa에서 사용 (v1.0 전후로 본격 투입)

나쁜 산출물이 public 제품에 흘러가는 리스크 회피를 위해, 제작 초기 실전 접촉은 **private 제품 우선**.
