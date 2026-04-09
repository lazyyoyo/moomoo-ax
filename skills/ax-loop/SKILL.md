---
name: ax-loop
description: This skill should be used when the user asks to "run ax-loop", "build with ax", "start autonomous build", "run quality gate", "check build status", "/ax run", "/ax status", or mentions autonomous build loop, harness-driven development, or auto-research pattern execution.
version: 0.1.0
---

# ax-loop

auto-research 패턴 기반 자율 빌드 루프. 워커(Claude) → 정적 게이트 → keep/discard 판정 → 자동 재작업 → 반복.

## 핵심 흐름

```
CPS/PRD 로드 → 워커(Claude) 코드 패치 생성 → 패치 적용 → gate_static.sh
  → 통과 = keep (git commit + 체크포인트 저장 + 종료)
  → 실패 = discard (git checkout -- . + 에러 피드백 → 다음 반복)
```

1. CPS/PRD 파일 존재 확인 (없으면 에러)
2. 워커가 Claude headless CLI로 `{files, summary}` JSON 패치 생성
3. 패치를 프로젝트에 적용
4. 정적 게이트(tsc, eslint, build, prettier) 순차 검사
5. 통과 시 keep — git commit, 체크포인트 저장, 종료
6. 실패 시 discard — git checkout으로 원복, 에러를 다음 iteration 프롬프트에 포함
7. 연속 3회 실패 시 오너 에스컬레이션
8. 최대 반복 도달 시 best 결과 유지하고 종료

## 사용법

```bash
# Phase 2 빌드 루프
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-loop/scripts/orchestrator.py run \
  --project ~/hq/projects/rubato --max-iter 5

# 현재 상태 확인
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-loop/scripts/orchestrator.py status \
  --project ~/hq/projects/rubato
```

## 스크립트

- **`scripts/orchestrator.py`** — CLI 진입점. `run`(빌드 루프)과 `status`(현황 조회) 커맨드. `--project` 필수. 루프 제어, CPS/PRD 탐색, 체크포인트, keep/discard 판정, git commit/checkout.
- **`scripts/gate_static.sh`** — 정적 게이트. `$1`=프로젝트경로, `$2`=결과JSON경로. tsc → eslint → build → prettier. 결과를 `{"passed": bool, "errors": [...]}` JSON으로 출력.
- **`scripts/worker.py`** — tmux 기반 Claude 워커. tmux 세션 `ax-workers`에서 `claude -p` 실행. CPS/PRD + `agents/*.md` → 프롬프트 조립 → `{files, summary}` 패치 생성 → 프로젝트에 적용. 실행 중 `tmux attach -t ax-workers`로 관찰 가능.

## 에이전트

워커 역할 정의는 `${CLAUDE_PLUGIN_ROOT}/agents/`에 위치:

- **`coder.md`** — 구현 전문. 기존 코드 패턴 파악 후 최소 수정, lint/typecheck/build 통과 코드 작성.

## 산출물

- `.harness/checkpoints/build_best.json` — 최고 결과 스냅샷 (git ref, iteration, gate 결과)
- `.harness/logs/iteration_NNN.json` — 반복별 로그 (verdict, gate 결과, tokens, duration_sec, error_summary)

## 전제 조건

- 대상 프로젝트에 `package.json` 존재
- 대상 프로젝트에 CPS/PRD 파일 존재 (`.harness/checkpoints/`, `docs/specs/`, `CPS.md`, `PRD.md` 중 하나)
- `claude` CLI 설치 및 인증 완료
- tmux 설치
- Node.js + npm 환경
- git 초기화된 프로젝트

## MVP (v0.1) 스코프

- `run`: Phase 2(Build) 루프만
- `status`: 체크포인트 + 로그 현황
- 게이트: ① 정적만
- 모델: Claude 단일
