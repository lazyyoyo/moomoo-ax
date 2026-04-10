# v0.2 — 루프 엔진 + Define 파이프라인 + 3 레이어 분리

## 목표

1. **레이어 1** 완성: `src/loop.py` 기반 루프 엔진 (labs/ 안에서 script.py 개선)
2. **labs/**: define 파이프라인 5 stage의 script.py 루프로 검증
3. **레이어 2** 설계: `plugin/skills/ax-define/`으로 검증된 script 승격
4. **strategy/**: moomoo-ax 자체 define 산출물
5. **관측 인프라**: Supabase + Vercel 대시보드 껍데기

## 3 레이어 아키텍처 (v0.2에서 정립)

| 레이어 | 목적 | 도구 | 위치 |
|--------|------|------|------|
| **1. 루프 엔진** | script.py 개선 | src/loop.py | labs/ 안에서만 |
| **2. 실행** | 검증된 script 1회 실행 | plugin 스킬 (슬래시 커맨드) | 프로젝트 |
| **3. 메타** | 새 단계 개발 | 레이어 1을 사용 | labs/ 확장 |

## Define 파이프라인

```
러프 아이디어
  → Stage 1: Seed Capture    → seed.md
  → Stage 2: JTBD Discovery  → jtbd.md
  → Stage 3: Problem Framing → problem-frame.md
  ── PO 게이트 (솔루션 선택 확정) ──
  → Stage 4: Scope Definition → scope.md
  → Stage 5: PRD Generation   → prd.md
```

Stage 1→3 자동. PO 확인 후 4→5 자동.

## 디렉토리 구조

```
moomoo-ax/
├── src/                              # 레이어 1 — 루프 엔진
│   ├── loop.py
│   ├── judge.py                      #   priority 가중치, 1회 호출
│   ├── claude.py                     #   Claude CLI 래퍼
│   └── db.py
│
├── labs/                             # 레이어 1 실험장
│   ├── seed-gen/
│   │   ├── program.md
│   │   ├── script.py
│   │   ├── rubric.yml
│   │   ├── input/
│   │   ├── best/
│   │   └── logs/
│   ├── jtbd-gen/
│   ├── problem-frame/
│   ├── scope-gen/
│   └── prd-gen/
│
├── labs/.archive/                    # 버전별 스냅샷
│   └── v0.2/
│
├── plugin/                           # 레이어 2 (순정)
│   └── skills/
│       └── ax-define/
│           ├── SKILL.md
│           ├── runner.py
│           └── stages/
│               ├── seed-gen/script.py
│               ├── jtbd-gen/script.py
│               ├── problem-frame/script.py
│               ├── scope-gen/script.py
│               └── prd-gen/script.py
│
├── strategy/                         # moomoo-ax 자체 define 산출물
│   ├── seed.md
│   ├── jtbd.md
│   ├── problem-frame.md
│   ├── scope.md
│   └── prd.md
│
├── docs/
│   └── rubric-guide.md
│
├── versions/
│   ├── v0.1.md                       # 기존 (파일)
│   └── v0.2/                         # 신규 (폴더)
│       └── plan.md
│
├── dashboard/                        # Next.js, Vercel 배포 완료
└── notes/
```

## Supabase

프로젝트: moomoo-ax (ap-northeast-2), id: aqwhjtlpzpcizatvchfb

### 스키마: iterations (단일 테이블)

| 컬럼 | 타입 |
|------|------|
| id | uuid PK |
| created_at | timestamptz |
| ax_version | text |
| user | text (yoyo / jojo) |
| project | text |
| detail | jsonb |

## 구현 순서 + 진행 상태

### 레이어 1 (루프 엔진)
1. [x] Supabase 프로젝트 + 스키마 (2026-04-09)
2. [x] src/db.py (2026-04-09)
3. [x] src/claude.py 래퍼 (토큰 추적)
4. [x] src/judge.py (1회 호출 + priority 가중치)
5. [x] src/loop.py (script.py 실행 방식)

### labs/ 5 stage
6. [x] seed-gen (program.md + script.py + rubric.yml)
7. [x] jtbd-gen
8. [x] problem-frame
9. [x] scope-gen
10. [x] prd-gen

### 파이프라인 검증
11. [x] 대시보드 PRD 파이프라인 (1차 실행)
12. [x] moomoo-ax 자체 PRD 파이프라인 (Stage 1~3까지)
13. [ ] moomoo-ax Stage 4~5 이어서 (strategy/에 저장)

### 레이어 2 (플러그인)
14. [ ] plugin/skills/ax-define/ 구조 생성
15. [ ] labs/{stage}/best/script.py → plugin으로 승격
16. [ ] plugin/skills/ax-define/SKILL.md
17. [ ] plugin/skills/ax-define/runner.py (5 stage 실행기)
18. [ ] labs/.archive/v0.2/ 스냅샷

### 관측
19. [x] dashboard/ Next.js 껍데기
20. [x] Supabase 연결
21. [x] Vercel 배포 (https://moomoo-ax.vercel.app)
22. [ ] 대시보드에서 뭘 볼지 정의 → 개선

## 성공 기준

- [x] 루프가 수렴하는 것을 1회 이상 확인
- [x] 토큰/비용 추적
- [x] Supabase 로그 적재
- [x] script.py가 iteration에서 개선됨
- [ ] plugin 승격 + 다른 프로젝트에서 호출 가능
- [ ] moomoo-ax strategy/ 완성 (자체 정체성 문서)

## 주요 결정

- **script.md → script.py** (실행 가능한 결정적 코드)
- **judge 1회 호출** (항목별 → 전체 한 번에, 89% 비용 절감)
- **priority 가중치** (critical/high/medium/low, critical No→0.0)
- **3 레이어 분리** (루프 엔진 / 실행 / 메타)
- **plugin 순정** (program.md, rubric.yml 없이 script.py만)
- **실험 히스토리는 labs/.archive/**에 버전별 스냅샷
- **폰트 Pretendard**, **shadcn/ui + recharts** (Tremor는 React 19 비호환)

## 이슈 / 메모

- v0.1 실패 원인: 범위 과대, tmux 인프라 선행, eval gradient 부재 → 리셋
- judge 초기 항목별 호출 $6.75 → 1회 호출 $0.79 (89% 절감)
- rubric이 너무 쉬워서 대부분 1회 통과 → 실전 적용 후 rubric 강화 필요 (v0.3+)
