---
name: ax-loop
description: This skill should be used when the user asks to "run ax-loop", "build with ax", "start autonomous build", "run quality gate", "check build status", "/ax run", "/ax status", or mentions autonomous build loop, harness-driven development, or auto-research pattern execution.
version: 0.1.0
---

# ax-loop

auto-research 패턴 기반 자율 빌드 루프. 워커(Claude) → 정적 게이트 → keep/crash 판정 → 자동 재작업 → 반복.

## 핵심 흐름

```
워커(Claude) 코드 작성 → gate_static.sh 검사 → 통과=keep(종료) / 실패=crash(재작업→반복)
```

1. 워커가 Claude headless CLI로 코드 작성/수정
2. 정적 게이트(eslint, tsc, build, prettier) 순차 검사
3. 통과 시 keep — 체크포인트 저장 후 종료
4. 실패 시 crash — 에러에서 재작업 프롬프트 자동 생성, 다음 반복
5. 연속 3회 crash 시 오너 에스컬레이션
6. 최대 반복 도달 시 best 결과 유지하고 종료

## 사용법

프로젝트 루트에서 실행:

```bash
# Phase 2 빌드 루프
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-loop/scripts/orchestrator.py run --task "태스크 설명"

# 반복 횟수 지정
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-loop/scripts/orchestrator.py run -t "태스크 설명" -n 5

# 현재 상태 확인
python ${CLAUDE_PLUGIN_ROOT}/skills/ax-loop/scripts/orchestrator.py status
```

## 스크립트

- **`scripts/orchestrator.py`** — CLI 진입점. `run`(빌드 루프)과 `status`(현황 조회) 커맨드 제공. 루프 제어, 체크포인트 읽기/쓰기, keep/crash 판정 담당.
- **`scripts/gate_static.sh`** — 정적 게이트. eslint → tsc → build → prettier 순차 실행. exit 0 통과, exit 1 실패 + 에러 stdout 출력.
- **`scripts/worker.py`** — Claude headless CLI 래퍼. `agents/*.md`에서 역할 정의 로드, 프롬프트 조립, `claude -p` 호출.

## 에이전트

워커 역할 정의는 `${CLAUDE_PLUGIN_ROOT}/agents/`에 위치:

- **`coder.md`** — 구현 전문. 기존 코드 패턴 파악 후 최소 수정, lint/typecheck/build 통과 코드 작성.

## 산출물

- `.harness/checkpoints/build_best.json` — 최고 결과 스냅샷 (git ref, iteration, gate 결과)
- `.harness/logs/iteration_NNN.json` — 반복별 로그 (verdict, gate 결과, duration, rework_prompt)

## 전제 조건

- 대상 프로젝트에 `package.json` 존재
- `claude` CLI 설치 및 인증 완료
- Node.js + npm 환경

## MVP (v0.1) 스코프

- `run`: Phase 2(Build) 루프만
- `status`: 체크포인트 + 로그 현황
- 게이트: ① 정적만
- 모델: Claude 단일
