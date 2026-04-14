# moomoo-ax

자기 하네스를 진화시켜 IT 제품 제작을 자동화하는 시스템. 상세 정의는 `PROJECT_BRIEF.md`가 SSOT.

## 한 줄 미션

오너가 의도를 한 번 전달하면, 기대치에 맞는 결과물을 무개입으로 배포까지 가져가는 파이프라인.
배포 제품은 **team-ax** (Claude Code 플러그인).

## 3 레이어 (요약)

| 레이어 | 역할 | 트리거 | 사용자 |
|---|---|---|---|
| **meta loop** | 판단·모니터링·(v1.0 이후) 하네스 진화 | 대시보드 신호, 피드백, 오너 판단 | yoyo (오너) |
| **levelup loop** | team-ax 플러그인 제작/개선 | `python src/loop.py {target}` | yoyo (개발자) |
| **product loop** | team-ax 돌려서 실제 제품 만들기 | `/ax-autopilot` 또는 단일 stage | yoyo, jojo |

- **판단은 meta, 실행은 levelup.** 같은 사람이 하지만 도구가 모드를 분리해야 함.
- **대시보드는 meta loop의 구현체**, 독립 레이어 아님.

## 6 stage 메뉴 (product loop 전용)

`init → define → design → implement → qa → deploy`

- 고정 파이프라인이 아니라 상황별 서브셋 선택 (새 프로젝트/메이저/마이너/패치)
- levelup loop는 이 메뉴를 공유하지 않음 — 자체 흐름(개선 대상 식별 → 타겟 지정 → iteration → 빌드 → 배포)

## 북극성 지표

**오너 개입 횟수 (↓)**

- team-product의 진짜 병목: design/implement에서 오너가 "이거 아니야, 내가 할게"로 결국 다 함
- 보조 지표: 단계별 토큰, 루브릭 점수, iteration 수, 자동 diff 크기

## 핵심 설계 원칙

1. **의도 캡처는 단 한 번** — define 이후 design 포함 전부 자동이어야 함
2. **자동이되, 보인다** — 무개입 ≠ 블랙박스. 대시보드에서 진행 중인 stage와 산출물 실시간 관찰
3. **판단은 meta, 실행은 levelup**
4. **deploy는 비용 순 점진 확장** — localhost → preview → production
5. **실험 결과물 ≠ 프로젝트 정의** — `dogfooding/` 는 참고용, `PROJECT_BRIEF.md`가 SSOT
6. **하네스 자기 진화** — v1.0 이후 도입

## 피드백 채널

- **자동 diff 캡처** (묵시적) — 산출물과 최종 배포물의 diff를 자동 추적
- **`/ax-feedback`** (명시적) — 아무 때나 자유 입력, 백로그 누적

## 디렉토리 구조

```
moomoo-ax/
├── PROJECT_BRIEF.md      # SSOT — 오너 승인 정의
├── CLAUDE.md             # 이 파일 (실행 규칙 요약)
├── README.md
│
├── src/                  # levelup loop 엔진
│   ├── loop.py           #   오케스트레이터
│   ├── judge.py          #   rubric → LLM Judge → 점수
│   ├── claude.py         #   Claude CLI 래퍼
│   └── db.py             #   Supabase 로그
│
├── labs/                 # levelup loop 실험장 (team-ax 6 stage 대응)
│   ├── ax-init/
│   ├── ax-define/
│   ├── ax-design/
│   ├── ax-implement/
│   ├── ax-qa/
│   └── ax-deploy/
│       ├── program.md    #   오너 규칙 (불변)
│       ├── script.py     #   AI가 개선하는 스크립트
│       ├── rubric.yml    #   평가 기준 ("오너 기대치" 항목 포함)
│       ├── input/
│       ├── best/
│       └── logs/
│
├── plugin/               # 배포 제품 team-ax
│   ├── .claude-plugin/
│   │   └── plugin.json   #   name: team-ax
│   └── skills/
│       ├── ax-autopilot/ #   상위 오케스트레이터 (자동 구간 버전별 확장)
│       ├── ax-init/
│       ├── ax-define/
│       ├── ax-design/
│       ├── ax-implement/
│       ├── ax-qa/
│       └── ax-deploy/
│
├── rnd/                  # meta loop 코드 (research & development)
│   ├── scraper/          #   (v1.0 이후) 외부 트렌드 수집
│   ├── gates/            #   (v1.0 이후) 5축 필터 + A/B 게이트
│   └── evolver/          #   (v1.0 이후) 하네스 편입 / graveyard
│
├── dashboard/            # meta loop UI (Next.js, Vercel)
├── dogfooding/           # product loop 자기 적용 결과 (참고용)
├── versions/             # 버전별 plan + 기록
│   └── .archive/         #   폐기된 과거 버전
└── notes/                # 설계 논의
```

## 버전 계획 (요약)

| 버전 | 목표 |
|---|---|
| v0.1 | 3 레이어 골격 + levelup 1 cycle + 대시보드 MVP |
| v0.2 | (C') 패턴 정립 + 자동 diff + `/ax-feedback` |
| v0.3 | `team-ax/ax-implement` 1 stage 완성 + end-to-end PASS |
| v0.4 | 관찰 인프라 + Claude conductor / Codex executor+reviewer pilot + dogfooding |
| v0.5 | ax-qa + levelup smoke + planner/자동 판정 + 6 stage 확장, **team-product 대체 선언** |
| v0.6 | 실전 적용 + jojo 공유 (kudos/sasasa 시범) |
| v0.7~0.9 | 피드백 반영, 북극성 지표 70% 감소, 안정화 |
| v1.0 | 공식 출시 |
| v1.x+ | autopilot 구간 확장, 하네스 자기 진화, production 자동 배포 |

상세: `PROJECT_BRIEF.md` 버전 로드맵 섹션.

## 인프라

- **Supabase**: moomoo-ax (ap-northeast-2), project id: `aqwhjtlpzpcizatvchfb`
- **대시보드**: https://moomoo-ax.vercel.app (Vercel + Next.js 16, root: `dashboard/`)
- **GitHub**: https://github.com/lazyyoyo/moomoo-ax

## Gotchas

- **오너 작업 방식**: 선계획 후실행을 선호. 구현 전 최소 범위 / 비범위 / 성공 기준을 먼저 3~5줄로 합의하고 시작.
- **역할 분리**: Claude 는 conductor. stage 흐름 제어 / task 선택 / 결과 판정 / fix task 삽입만 맡고, 실제 구현/리뷰 worker 는 분리 가능하게 설계.
- **rubric은 루프 안에서 불변**. 변경은 meta loop(버전 단위) 판단으로만.
- **levelup loop 엔진(`src/loop.py`)은 범용**. 대상별 차이는 `labs/{target}/program.md + rubric.yml`로 표현.
- **subprocess.run으로 Claude CLI 호출**. 외부 의존성 최소화.
- **사용자**: yoyo (rubato, rofan-world, dashboard, moomoo-ax) / jojo (kudos, sasasa)
- **dogfooding ≠ PROJECT_BRIEF**. 자기 적용 결과물이 정의 문서를 덮어쓰지 않음.
