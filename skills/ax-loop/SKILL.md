# ax-loop

auto-research 패턴 기반 자율 빌드 루프. 워커(Claude) → 정적 게이트 → pass/crash → 반복.

## 사용법

프로젝트 루트에서 실행:

```bash
# Phase 2 빌드 루프
python skills/ax-loop/scripts/orchestrator.py run --task "태스크 설명"

# 반복 횟수 지정
python skills/ax-loop/scripts/orchestrator.py run -t "태스크 설명" -n 5

# 현재 상태 확인
python skills/ax-loop/scripts/orchestrator.py status
```

## MVP (v0.1) 스코프

- `run`: Phase 2(Build) 루프만 — 워커 → gate_static → keep/crash → 반복
- `status`: 체크포인트 + 로그 현황
- 게이트: ① 정적만 (eslint, tsc, build, prettier)
- 모델: Claude 단일

## 전제 조건

- 대상 프로젝트에 `package.json` 존재
- `claude` CLI 설치 및 인증 완료
- Node.js + npm 환경

## 산출물

- `.harness/checkpoints/build_best.json` — 최고 결과 스냅샷
- `.harness/logs/iteration_NNN.json` — 반복별 로그
