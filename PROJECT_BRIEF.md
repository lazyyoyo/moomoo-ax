# moomoo-ax

자기 하네스를 진화시켜 IT 제품 제작을 자동화하는 시스템.

## 한 줄 미션

> **오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인.**

이 파이프라인을 담은 배포 제품이 **team-ax**이다.
moomoo-ax는 team-ax를 만드는 공장(levelup loop) + 그 공장을 스스로 진화시키는 상위 엔진(meta loop)까지 포함한다.

## 용어 정리

| 용어 | 의미 |
|---|---|
| **moomoo-ax** | 이 프로젝트 전체. ax = AI Transformation (최상위 개념) |
| **team-ax** | 배포 제품. Claude Code 플러그인 (team-product/team-design 패밀리) |
| **meta loop** | 관측·판단·진화를 담당하는 최상위 사이클 |
| **levelup loop** | team-ax 플러그인을 만들고 개선하는 내부 사이클 |
| **product loop** | 사용자가 team-ax를 돌려 제품을 만드는 사이클 |

## 북극성 지표

**오너 개입 횟수 (↓)**

team-product을 쓰며 체감한 진짜 병목은 이거였다:

- design에서 "아 이거 아니라고 내가 하나씩 집어줄게"로 오너가 결국 다 함
- implement 자잘한 버그 수정도 오너 몫
- 결과적으로 의도 전달 이후에도 오너가 손을 뗄 수 없음

기대치에 맞으면 개입할 일이 없고, 개입이 없으면 횟수가 줄어든다.
즉 "기대치 충족"은 질적 지표, "개입 횟수"는 그것의 정량 대리지표. 모든 보조 지표(단계별 토큰, 루브릭 점수, iteration 수)는 이 북극성을 설명하는 선들이다.

## 3 레이어

### 레이어 1 — product loop (사용자의 루프)

team-ax를 돌려서 실제 제품을 만드는 루프. moomoo-ax의 **외부 가치**가 발생하는 곳.

| 항목 | 내용 |
|---|---|
| 사용자 | yoyo (rubato, dashboard, rofan-world, moomoo-ax…), jojo (kudos, sasasa…) |
| 트리거 | `/ax-autopilot "의도"` 또는 단일 stage 호출 (`/ax-define`, `/ax-implement` …) |
| 단위 | 6 stage 메뉴 (아래 참조) |
| 산출물 | 외부 프로젝트의 strategy, 디자인, 코드, 배포물 |
| 성공 기준 | 기대치에 맞는 결과물이 오너 개입 없이 배포까지 감 |

### 레이어 2 — levelup loop (team-ax 제작/개선)

product loop가 쓰는 team-ax 플러그인을 만들고 개선하는 루프. moomoo-ax의 **내부 공장**.

| 항목 | 내용 |
|---|---|
| 사용자 | yoyo (moomoo-ax 개발자) |
| 트리거 | `python src/loop.py {target}` 또는 meta loop의 지시 |
| 단위 | plugin 1개 × 개선 대상(script / prompt / rubric) |
| 산출물 | 검증된 `plugin/skills/ax-*/` |
| 성공 기준 | rubric 점수 수렴 + **rubric에 "오너 기대치" 평가 항목 포함** |

**levelup loop의 흐름** (product loop의 6 stage와는 별개의 규칙):

1. 개선 대상 식별 — meta loop 지시 or rubric 점수 낮은 plugin
2. 타겟 지정 — script.py / prompt / rubric 중 무엇을 건드릴지
3. iteration — labs/에서 돌리기 → rubric 평가 → best 갱신
4. 빌드 — `plugin.json` 버전 bump → `plugin/skills/`에 복사
5. 배포 — 커밋 → marketplace 재설치

### 레이어 3 — meta loop (판단·모니터링·진화)

levelup loop과 product loop 양쪽을 지켜보고, 하네스 자체를 진화시키는 **상위 사이클**.

| 항목 | 내용 |
|---|---|
| 사용자 | yoyo (moomoo-ax 오너) |
| 입력 | 내부 신호(대시보드, 개입 횟수, 피드백 백로그) + 외부 신호(기술 트렌드 스크래핑, v1.0 이후) |
| 출력 | 개선 지시, 하네스 편입, 버전 결정, 폐기 결정 |
| 구현체 | 대시보드 (관측 UI) + 피드백 수집 + (v1.0 이후) 스크래퍼 + A/B 게이트 |
| 성공 기준 | levelup loop + product loop 양쪽의 성공을 담보 |

**대시보드는 meta loop 안에 있다**. 독립 레이어가 아니라 meta loop의 물리적 구현체이자 UI.

## 관계도

```
       ┌──── meta loop ────┐
       │  관측·판단·진화    │
       │                   │
       │  ▸ 내부 신호       │  ← 대시보드, 개입 횟수, 피드백
       │  ▸ 외부 신호       │  ← 기술 트렌드 자동 스크래핑 (v1.0 이후)
       └───────────────────┘
         ↑ 점수/피드백        ↓ 개선 지시
       ┌───────────────────┐
       │   levelup loop    │
       │  labs/ → plugin/  │
       └───────────────────┘
         ↑ 사용 로그         ↓ team-ax 배포
       ┌───────────────────┐
       │   product loop    │
       │   외부 프로젝트    │
       └───────────────────┘
```

양방향 순환 — meta가 두 하위 루프 모두를 지켜보고 각각에 개입한다.

## 6 stage 메뉴 (product loop 전용)

product loop가 쓰는 단위. 고정 템플릿이 아니라 **상황에 따라 서브셋을 고르는 메뉴**. levelup loop는 이 메뉴와 다른 흐름으로 돈다(위 레이어 2 참조).

| stage | 역할 |
|---|---|
| init | 프로젝트/리포 초기화, 환경 세팅 |
| define | 오너 의도 캡처 → 스펙 확정 |
| design | UX/UI/아키텍처 결정 |
| implement | 코드 작성 |
| qa | 검증, 버그 수정 루프 |
| deploy | 배포 (localhost → preview → production) |

**상황별 진입점 예시**:

| 상황 | 파이프라인 |
|---|---|
| 새 프로젝트 | init → define → design → implement → qa → deploy |
| 메이저 기능 | define → design → implement → qa → deploy |
| 마이너 기능 | define(경량) → [design 필요 시] → implement → qa → deploy |
| 패치 | implement → qa → deploy |

## 설계 원칙

### 1. 의도 캡처는 단 한 번

오너와의 대화는 init/define 구간에서 의도를 수렴하는 데만 쓴다. **define 이후는 design 포함 전부 자동**이어야 한다.

지금 design에서 오너가 손대는 건 "원래는 자동이어야 하는데 안 돼서" 그런 것이다. 이걸 해소하는 게 moomoo-ax의 존재 이유 — 수동 개입을 기본값으로 받아들이면 안 된다.

### 2. 자동이되, 보인다

오너는 개입하지 않지만, **대시보드에서 현재 진행 중인 stage와 각 stage의 산출물을 실시간으로 볼 수 있다**. 무개입 ≠ 블랙박스.

대시보드는 단순 메트릭 뷰가 아니라 "프로젝트 진행 관찰" 기능을 기본 탑재한다. 오너가 원할 때 열어보면 어떤 프로젝트에서 어느 stage가 돌고 있고 산출물은 뭔지 바로 확인 가능.

### 3. 판단은 meta, 실행은 levelup

같은 사람(yoyo)이 두 역할을 다 하기 때문에 **도구가 모드를 분리**해줘야 한다.

- **판단 (meta loop)**: "지금 design이 개입 많이 받고 있네 → 고쳐야겠다", "이번엔 이 rubric으로", "이 버전은 폐기"
- **실행 (levelup loop)**: 결정된 대상/기준으로 루프 돌리기, iteration, 점수 산출, best 갱신, plugin 승격

### 4. deploy는 비용 순으로 점진 확장

preview 환경도 공짜가 아니다. 매 iteration마다 preview에 올리면 비용이 급증한다. 그래서 단계별로 자동 구간을 넓힌다:

```
초기:  implement → localhost 확인 → preview deploy
            ↓ (개입 횟수가 극도로 줄면)
중기:  implement → preview deploy (localhost 건너뜀)
            ↓ (안정기)
후기:  implement → preview → production (v1.0 이후)
```

### 5. 실험 결과물 ≠ 프로젝트 정의

- `dogfooding/` — product loop를 자기 자신에 돌린 실험 결과. 참고용.
- `PROJECT_BRIEF.md` — 오너가 쓰고/승인한 프로젝트 정의. SSOT.

dogfooding이 PROJECT_BRIEF와 얼마나 가까운지가 **meta loop의 자기 점검 지표** 중 하나. 실험 결과가 오너 승인 정의로 승격될 수는 있어도, 둘은 같지 않다.

### 6. 하네스는 스스로 진화한다 (v1.0 이후)

meta loop는 궁극적으로 "이미 있는 걸 관측"만 하지 않고, **외부에서 좋은 게 나오면 자동으로 흡수**한다. 사람이 수동으로 "이 기술 써보자" 하지 않아도 하네스가 알아서 업데이트된다.

단, v1.0까지는 이 기능을 보류한다. **team-product 대체가 먼저다**. 하네스 진화 파이프라인 설계는 아래 섹션에 기록하되, v1.x에서 구현.

## 피드백 채널

### 1. 자동 diff 캡처 (묵시적)

team-ax가 뽑은 산출물과 최종 배포물의 diff를 자동 추적.
"오너가 어디를 뜯어고쳤는가" = 가장 정직한 품질 신호. meta loop의 개선 우선순위 입력.

### 2. `/ax-feedback` (명시적)

오너가 아무 때나 호출해서 자유 입력: "design 단계에서 이게 불편했다, 고쳐라".
피드백 백로그에 누적되고 meta loop가 정리/분류한다. 하루 1회가 아니라 **상시 수집**.

## 하네스 진화 파이프라인 (v1.0 이후 구현)

장기 비전으로 설계만 기록해둔다.

```
[수집]  6시간마다 스크래핑
        GitHub trending · AI 연구자 repo/X · RSS
            ↓
[1차 필터]  5축 점수 (7/10 이상만 통과)
        자동화↑ · 마찰↓ · HARD 전환 · 토큰 효율 · 측정 가능
            ↓
[2차 게이트]  실측 A/B
        git stash로 임시 적용 → harness 점수 측정
            ↓
[판정]  점수 올랐으면 keep, 떨어지면 discard
            ↓
[기록]  본 것은 영구 기록, 거부는 graveyard
```

**핵심은 2차 게이트다.** 필터 통과 후 자동 머지가 아니라, 실측 harness 점수가 올라간 경우에만 편입한다. LLM 주관 개입 없이 숫자로 판정 — "다 먹는" 구조가 아니라 "거르고 검증 실패 시 자동 폐기" 구조.

## 디렉토리 구조

```
moomoo-ax/
├── PROJECT_BRIEF.md      # 프로젝트 정의 (SSOT, 오너 승인)
├── CLAUDE.md             # 실행 규칙, 파이프라인 흐름
├── README.md             # 외부 독자용
│
├── src/                  # levelup loop 엔진
│   ├── loop.py
│   ├── judge.py
│   ├── claude.py
│   └── db.py
│
├── labs/                 # levelup loop 실험장 (team-ax 6 stage 대응)
│   ├── ax-init/
│   ├── ax-define/
│   ├── ax-design/
│   ├── ax-implement/
│   ├── ax-qa/
│   └── ax-deploy/
│       ├── program.md
│       ├── script.py
│       ├── rubric.yml    # ← "오너 기대치" 평가 항목 포함
│       ├── input/
│       ├── best/
│       └── logs/
│
├── plugin/               # 배포 제품 team-ax
│   ├── .claude-plugin/
│   │   └── plugin.json   # name: team-ax
│   └── skills/
│       ├── ax-autopilot/ # 상위 오케스트레이터 (자동 구간은 버전별 확장)
│       ├── ax-init/
│       ├── ax-define/
│       ├── ax-design/
│       ├── ax-implement/
│       ├── ax-qa/
│       └── ax-deploy/
│
├── rnd/                  # meta loop 코드 (research & development)
│   ├── scraper/          #   외부 트렌드 수집 (v1.0 이후)
│   ├── gates/            #   5축 필터 + A/B 게이트 (v1.0 이후)
│   └── evolver/          #   하네스 편입 / graveyard (v1.0 이후)
│
├── dashboard/            # meta loop UI (Next.js, Vercel)
│
├── dogfooding/           # product loop를 자기 자신에 돌린 결과 (참고용)
│
├── versions/             # 버전별 계획/회고
│   ├── v0.1/
│   └── .archive/         # 폐기된 과거 버전 (구 v0.1, v0.2)
│
└── notes/                # 설계 논의
```

## 버전 로드맵

기존 v0.1, v0.2는 `versions/.archive/`로 이동하고 **새 v0.1**부터 시작한다.

**핵심 전환 (v0.2~)**: **(C') Progressive Codification** 패턴으로 전환.
team-product 의 자연어 SKILL.md 를 seed 로 포팅 → levelup loop 가 개선. 단, **improve 대상은 SKILL.md 자체 + deterministic 규칙의 script 추출** 둘 다. 자연어 스킬은 AI 자의적 해석 + 토큰 낭비의 원인이므로, 안정적 단계는 코드로 굳혀가는 게 하네스 자기 진화의 실체.

**핵심 순서 전환 (v0.3~)**: **product → meta → levelup**. v0.2 E 에서 "뭘 개선할지" 사전 정의 없이 SKILL.md 를 압축만 하니 공허했다. 배포 제품인 product loop 가 실제로 돌아야 → 개입 횟수 / 토큰 관찰이 의미 있어야 → levelup 개선 대상이 공허하지 않다. PROJECT_BRIEF 의 3 레이어 정의는 유지. 구축 순서만 이렇게.

**현재 우선순위 (v0.5~)**: team-product 대체를 더 빨리 진행하기 위해 순서를 다시 좁힌다.

1. **`ax-implement` 실전 사용성** — plan 이 없는 실프로젝트에서도 바로 implement stage 를 돌릴 수 있어야 한다
2. **`ax-define` 기본 문서 초안 Codex 작성** — `spec`, `ARCHITECTURE`, `DESIGN_SYSTEM`, `plan` 기본 문서를 Codex worker 가 먼저 만든다
3. 그 다음에 `ax-qa` 와 나머지 stage 를 붙인다

즉 v0.5~v0.6 의 초점은 "6 stage를 빨리 다 채운다" 가 아니라, **실제 다른 제품 작업이 지금 당장 돌아가게 하는 두 stage (`implement`, `define`) 를 먼저 실전형으로 만든다** 이다.

**v1.0까지 — team-product 대체와 실전 적용**

| 버전       | 목표                                                                                                                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **v0.1** | 3 레이어 골격 + levelup loop 1 cycle 완주 + 대시보드 관측 MVP                                                                                                                                                        |
| v0.2     | (C') 패턴 정립 + R5 fix + `improve_target` 추상화 + post-commit hook + `/ax-feedback` CLI + 구조 결함 실증 2건                                                                                                        |
| v0.3     | **순서 전환** — product loop 의 `team-ax/ax-implement` 1 stage 완성 (skill + scripts 4 + agents 3 + 드라이버 + 격리 fixture + end-to-end 수동 PASS). 관찰 인프라 / dogfooding / levelup smoke 는 v0.4 이월                     |
| v0.4     | **관찰 인프라 + Codex executor+reviewer pilot + 첫 dogfooding close** — Supabase `product_runs` + 대시보드 카드 + implement stage 의 executor / reviewer 를 Codex worker 로 제한 편입 + `dashboard/` 첫 dogfooding 1건. 속도는 known issue 로 수용. |
| v0.5     | **implement 실전 사용성 우선** — planner/plan bootstrap 을 포함해 `ax-implement` 를 plan 없는 실프로젝트에서도 바로 쓰게 하고, subtree/dirty baseline/rerun 규칙까지 실전 기준으로 hardening                                                                 |
| v0.6     | **define 기본 문서 Codex 작성** — `ax-define` 에서 기본 문서 초안(`spec`, `ARCHITECTURE`, `DESIGN_SYSTEM`, `plan`) 을 Codex worker 가 작성하고, Claude 는 의도 수렴 / 승인 포인트만 담당                                                                  |
| v0.7     | `ax-qa` 포팅 + levelup smoke + planner / 자동 판정 정비 + ax-design + ax-init + ax-deploy 포팅 → 6 stage 전부, `ax-autopilot` 오케스트레이터 (implement → localhost → preview), **team-product 대체 선언**                       |
| v0.8     | jojo 피드백 반영 → levelup 반복                                                                                                                                                                                |
| v0.9     | 북극성 지표(오너 개입 횟수) 70% 감소 달성 + 안정화 + 문서 정리                                                                                                                                                              |
| **v1.0** | 공식 출시                                                                                                                                                                                                   |

**v1.x+ — 자율 진화 단계**

| 버전 | 목표 |
|---|---|
| v1.x | autopilot 구간 확장 (implement→ → design→ → define→) |
| v1.x | autopilot localhost 건너뛰고 preview 직행 |
| v1.x | 하네스 진화 — 스크래퍼 + 1차 필터 |
| v1.x | 2차 게이트 (A/B 실측) — meta loop 자율 동작 |
| v1.x | production deploy 자동화 |

## 성공 기준 (v1.0)

- [ ] yoyo가 haru/rubato/rofan-world/dashboard 작업을 `/ax-autopilot`으로 수행하고, implement→preview 구간을 개입 없이 완주
- [ ] jojo가 kudos/sasasa를 `/ax-autopilot`으로 독립 사용 중
- [ ] 오너 개입 횟수가 v0.1 첫 측정 대비 70% 이상 감소
- [ ] team-product을 대체해 모든 프로젝트에서 team-ax 사용
- [ ] meta loop 대시보드에서 3 레이어 건강 상태 + 프로젝트 진행 관찰이 한 화면에서 가능
- [ ] 자동 diff 캡처와 `/ax-feedback` 두 채널에서 피드백 데이터가 누적되고 meta loop가 주기적으로 소화
- [ ] 각 stage SKILL.md 의 deterministic 규칙이 script 로 추출되어 토큰 효율과 실행 안정성이 자연어 대비 향상 ((C') 패턴의 v1.0 완결형)

## 기술 스택

| 영역 | 스택 |
|---|---|
| levelup loop 엔진 | Python (`src/loop.py`, `judge.py`, `claude.py`) |
| 워커 | Claude CLI conductor + Codex worker (`codex exec`) |
| eval | LLM Judge (rubric 기반, 가중치 점수, "오너 기대치" 포함) |
| 로그 / 데이터 | Supabase (ap-northeast-2, project id: aqwhjtlpzpcizatvchfb) |
| 대시보드 | Next.js 16 + shadcn/ui + recharts (Vercel 배포) |
| rnd 스크래퍼 | Python (cron/systemd timer, 6시간 주기, v1.0 이후) |
| 배포 제품 | Claude Code plugin `team-ax` |
| 코드 호스팅 | GitHub (lazyyoyo/moomoo-ax) |

## 사용자

- **yoyo** — moomoo-ax 오너 + haru/rubato/rofan-world/dashboard/moomoo-ax에서 product loop 사용자
- **jojo** — kudos/sasasa에서 product loop 사용자 (v0.6부터 시범, v1.0에서 정식)

두 사람의 프로젝트 진행 상황, 토큰 소비량, 오너 개입 횟수를 대시보드에서 추적한다.

### 실험 vs 공개 제품

team-ax 개발 초기(v0.2~0.5) 의 실전 접촉은 **private 제품 우선**으로 진행한다. 나쁜 산출물이 public 제품에 흘러가는 리스크 회피.

- **haru** (`~/hq/projects/journal/`) — yoyo + 남편 2인 사용. private. **v0.2 ax-implement 첫 케이스 적용지**.
- **rubato** — public. 안정화 이후 v0.5+ 에서 본격 투입.
- **rofan-world / dashboard / moomoo-ax (dogfooding)** — 중간 단계에서 선택적.
