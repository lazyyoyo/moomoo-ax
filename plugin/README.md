# team-ax

moomoo-ax가 제공하는 배포 제품. Claude Code 플러그인.

## 한 줄

오너 의도를 기대치에 맞게 **무개입으로 배포까지 가져가는** 파이프라인.

## 스킬 구조

```
skills/
├── ax-autopilot/  # 상위 오케스트레이터 (자동 구간 버전별 확장)
├── ax-init/       # 프로젝트/리포 초기화
├── ax-define/     # 오너 의도 캡처 → 스펙 확정
├── ax-design/     # UX/UI/아키텍처 결정
├── ax-implement/  # 코드 작성
├── ax-qa/         # 검증, 버그 수정 루프
└── ax-deploy/     # 배포 (localhost → preview → production)
```

각 스킬은 `labs/{ax-*}/best/script.py`에서 승격된 **검증된 스크립트**다.

## 자동 구간 (`/ax-autopilot`)

버전별로 점진 확장:

| 버전 | 자동 구간 |
|---|---|
| v0.4 | implement → localhost 확인 → preview deploy |
| v0.6 | design → preview deploy |
| v0.9 (v1.0 이후) | define → preview deploy |
| v1.x+ | define → production deploy |

## 호출 예

```
/ax-autopilot "쓸만한 독서 기록 웹앱"   # 의도만 전달, 나머지 자동
/ax-define "사이드바에 필터 추가"          # 단일 stage만
/ax-implement                               # 현재 컨텍스트에서 구현만
```

## 원칙

- **자동이되, 보인다** — 오너는 개입하지 않지만 대시보드에서 현재 진행 상황 실시간 관찰 가능
- **판단은 meta, 실행은 levelup** — 이 플러그인은 "실행" 레이어에 해당

상세: 프로젝트 루트 `PROJECT_BRIEF.md` 참조.
