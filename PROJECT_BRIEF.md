# moomoo-ax — Project Brief

## 한 줄 요약

auto-research 루프로 단계별 최적화 스크립트를 만들고, 검증된 스크립트를 plugin으로 배포하여 team moomoo의 IT 제품 제작을 자동화하는 엔진.

## 무엇을 만드는가

단일 업무(CPS, PRD 작성, 디자인, 구현)에 대해 "생성 → 평가 → 스크립트 개선" 루프를 자동으로 돌려서, **그 업무를 잘 수행하는 스크립트**를 만드는 시스템.

루프가 개선하는 건 "이번 산출물"이 아니라 **"산출물을 잘 만드는 방법(스크립트)"** 자체. 검증된 스크립트는 plugin에 편입되어 다른 프로젝트(rubato, rofan-world 등)에서 재사용.

## 왜 만드는가

- 바이브 코딩으로 빠르게 만들 수 있지만, 품질은 오너가 직접 리뷰해야 함
- 리뷰 → 피드백 → 재작업 루프가 오너 시간을 가장 많이 잡아먹음
- "평가 기준을 정의하고 루프를 돌리면" 오너 개입 없이 품질이 수렴할 수 있음
- 스크립트가 자산화되면 프로젝트마다 같은 시행착오를 반복하지 않음
- 이 제품 자체가 자체 개선 사이클(meta-loop)을 내장 — 쓸수록 더 좋아지는 도구

## 핵심 원리 (auto-research에서)

1. **수정 범위를 좁힌다** — 한 번에 스크립트 1개만 수정
2. **eval이 숫자다** — 체크리스트 → 합산 점수. gradient가 있어야 개선 방향을 알 수 있음
3. **반복이 빠르다** — 문서 생성 ~30초, 코드 생성 ~1분
4. **하네스(rubric)가 불변** — 평가 기준은 루프 안에서 안 변함

## 아키텍처 — 3 레이어

레이어를 명확히 분리. 각 레이어는 다른 도구 / 다른 목적.

### 레이어 1: 루프 엔진 (script 개선)

**목적**: script.py를 rubric 기반으로 반복 개선
**도구**: `src/loop.py`, `src/judge.py`, `src/claude.py`, `src/db.py`
**사용처**: `labs/` 안에서만
**산출물**: `labs/{stage}/best/script.py` — 검증된 최종 스크립트

```bash
python src/loop.py seed-gen
```

### 레이어 2: 실행 (script 1회 실행)

**목적**: 검증된 script를 프로젝트에 적용해서 산출물 생성
**도구**: `plugin/skills/ax-define/` 스킬 (Claude Code 슬래시 커맨드)
**사용처**: 모든 프로젝트 (moomoo-ax 포함)
**산출물**: 프로젝트의 `strategy/` 디렉토리

```
/ax-define "러프 아이디어"
```

### 레이어 3: 메타 (새 단계 개발)

**목적**: "루프로 품질 검증이 필요한 새 단계" 개발 자체
**도구**: 레이어 1 전체가 이 레이어의 도구
**사용처**: 새 script.py + rubric.yml을 labs에 추가할 때

---

## 디렉토리 구조

```
moomoo-ax/
├── src/                              # 레이어 1 — 루프 엔진
│   ├── loop.py                       #   오케스트레이터 (labs/ 대상)
│   ├── judge.py                      #   루브릭 → LLM Judge → 점수
│   ├── claude.py                     #   Claude CLI 래퍼
│   └── db.py                         #   Supabase 로그
│
├── labs/                             # 레이어 1 실험장
│   ├── seed-gen/
│   │   ├── program.md                #   오너 규칙 (루프에서 개선 참고용)
│   │   ├── script.py                 #   AI가 개선하는 스크립트
│   │   ├── rubric.yml                #   평가 기준
│   │   ├── input/                    #   실험 입력
│   │   ├── best/                     #   최고 점수 스냅샷
│   │   └── logs/                     #   iteration 로그
│   ├── jtbd-gen/
│   └── ...
│
├── labs/.archive/                    # 버전별 실험 스냅샷 (히스토리)
│   ├── v0.2/
│   │   ├── seed-gen/                 #   승격 당시 program/script/rubric
│   │   └── ...
│   └── v0.3/
│
├── plugin/                           # 레이어 2 — 배포 스킬 (순정)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   └── skills/
│       └── ax-define/
│           ├── SKILL.md              #   파이프라인 진입점
│           ├── runner.py             #   script 실행 헬퍼
│           └── stages/
│               ├── seed-gen/
│               │   └── script.py     #   순정 (program.md, rubric.yml 없음)
│               ├── jtbd-gen/
│               │   └── script.py
│               ├── problem-frame/
│               │   └── script.py
│               ├── scope-gen/
│               │   └── script.py
│               └── prd-gen/
│                   └── script.py
│
├── strategy/                         # moomoo-ax 자체의 define 산출물
│   ├── seed.md
│   ├── jtbd.md
│   ├── problem-frame.md
│   ├── scope.md
│   └── prd.md
│
├── docs/                             # 기술 reference
│   └── rubric-guide.md
│
├── versions/                         # 버전별 실행 기록
│   ├── v0.1.md
│   └── v0.2/
│       ├── plan.md
│       ├── retro.md
│       └── changelog.md
│
├── dashboard/                        # 관측 (Next.js, Vercel 배포)
├── notes/                            # 설계 논의
└── CLAUDE.md, PROJECT_BRIEF.md, README.md
```

## 승격 흐름 (labs → plugin)

```
① labs/{stage}/에서 loop.py 루프 실행
② best 도달 + 오너 확인
③ 현재 labs/{stage}/ 전체를 labs/.archive/v{version}/{stage}/에 스냅샷
④ labs/{stage}/best/script.py → plugin/skills/ax-define/stages/{stage}/script.py 복사
⑤ plugin은 순정 유지 (program.md, rubric.yml 포함 안 함)
⑥ 필요 시 labs/.archive/에서 히스토리 복원 → 재개선
```

## 누가 쓰는가

- **yoyo** — rubato, dashboard, moomoo-ax 등
- **jojo** — rofan-world 등
- 두 사람의 프로젝트 진행 상황, 토큰 소비량을 대시보드에서 추적

## 버전 계획

| 버전 | 목표 | 핵심 산출물 |
|------|------|-----------|
| v0.1 | (폐기) | MVP 시도, 범위 과대로 실패 |
| **v0.2** | 루프 엔진 + define 파이프라인 + 3 레이어 분리 + 관측 인프라 | src/loop.py, labs/ 5 stage, plugin/ax-define, strategy/, dashboard 껍데기 |
| v0.3 | design 루프 | 디자인 스크립트 + 시각 eval |
| v0.4 | implement 루프 | 구현 스크립트 + 정적 게이트 |
| v0.5~0.9 | 실전 적용 + 강화 | 프로젝트 적용 → 피드백 → 스크립트/eval 진화 |
| v1.0 | 출시 + jojo 공유 | 안정적 루프 + 대시보드 + 문서 |

## 기술 스택

- **루프 엔진**: Python (src/loop.py, judge.py, claude.py)
- **워커**: Claude CLI (`claude -p` subprocess)
- **eval**: LLM Judge (1회 호출, priority 가중치)
- **로그**: Supabase (ap-northeast-2, project id: aqwhjtlpzpcizatvchfb)
- **대시보드**: Vercel + Next.js 16 + shadcn/ui + recharts
- **배포**: Claude Code plugin (plugin/skills/ax-define)
- **코드**: GitHub (lazyyoyo/moomoo-ax)

## 성공 기준 (v1.0)

- [ ] 3가지 단계에서 루프가 수렴 (define, design, implement)
- [ ] 각 단계의 최적화된 스크립트가 plugin에 편입
- [ ] 오너 개입 없이 80% 이상 산출물이 기대치 도달
- [ ] yoyo + jojo 프로젝트에서 실사용
- [ ] 대시보드에서 프로젝트 진행 상황 + 토큰 소비량 추적
- [ ] jojo가 독립적으로 사용 가능
