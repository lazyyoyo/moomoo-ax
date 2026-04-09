# moomoo-ax

auto-research 루프로 단계별 최적화 스크립트를 만드는 엔진.

## 핵심 개념

- **루프가 개선하는 건 "산출물"이 아니라 "스크립트"** — PRD를 잘 쓰는 방법, 디자인을 잘 뽑는 방법 자체를 최적화
- **labs/에서 실험 → plugin/으로 승격** — 검증된 스크립트만 프로덕션에 편입
- **오너는 규칙(program.md)과 평가 기준(rubric.yml)만 정의** — 나머지는 루프가 자율 실행

## auto-research 매핑

| auto-research | moomoo-ax | 누가 관리 |
|---------------|----------|----------|
| program.md | `program.md` — 오너 규칙 | 오너 |
| train.py | `script.md` — 생성 스크립트 | AI (루프에서 개선) |
| prepare.py | `rubric.yml` — 평가 체크리스트 | 오너 (루프 안 불변) |
| results.tsv | `logs/` + Supabase | 자동 |

## 루프 흐름

```
script.md로 산출물 생성 → rubric으로 eval → 점수
  → 점수 > best → keep (script + 산출물 저장)
  → 점수 ≤ best → discard (실패 항목 → script 수정 피드백)
→ 종료: 점수 ≥ 임계값 or max iteration
```

## 디렉토리 구조

```
moomoo-ax/
├── loop.py              # 범용 오케스트레이터
├── judge.py             # 루브릭 → LLM Judge → 점수
├── db.py                # Supabase 로그 래퍼
├── labs/                # 실험 (루프 돌리는 곳)
│   └── {experiment}/
│       ├── program.md   #   오너 규칙 (불변)
│       ├── script.md    #   AI가 개선하는 스크립트
│       ├── rubric.yml   #   평가 기준 (불변)
│       ├── input/       #   입력 파일
│       ├── best/        #   최적 산출물 + script
│       └── logs/        #   iteration 로그
├── plugin/              # 프로덕션 (검증된 스킬)
│   ├── .claude-plugin/
│   ├── skills/
│   └── agents/
├── dashboard/           # Vercel 대시보드
├── versions/            # 버전별 plan + 기록
└── notes/               # 설계 논의
```

## 단계별 루프

| 단계 | input | output | eval |
|------|-------|--------|------|
| define | CPS/아이디어 | PRD | LLM Judge (루브릭) |
| design | PRD | 디자인 명세 + 코드 | LLM Judge + 시각 diff |
| implement | 디자인 명세 | 코드 | 정적 게이트 + LLM Judge |

## 버전 계획

| 버전 | 목표 |
|------|------|
| **v0.2** | 루프 엔진 + define 실험 + Supabase 로그 + 대시보드 |
| v0.3 | design 루프 + 시각 eval |
| v0.4 | implement 루프 + 정적 게이트 |
| v0.5~0.9 | 실전 적용 + 강화 |
| v1.0 | 출시 + 남편 공유 |

## 인프라

- **Supabase**: moomoo-ax (ap-northeast-2), project id: aqwhjtlpzpcizatvchfb
- **대시보드**: Vercel + Next.js (dashboard/)
- **GitHub**: https://github.com/lazyyoyo/moomoo-ax

## Gotchas

- rubric은 루프 안에서 불변. 변경은 meta-loop(버전 단위)에서만
- 루프 엔진(loop.py)은 범용. 단계별 차이는 program.md + rubric.yml로 표현
- subprocess.run으로 Claude 호출. tmux 없음
