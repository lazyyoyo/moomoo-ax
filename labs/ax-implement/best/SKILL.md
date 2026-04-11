---
name: ax-implement
description: "구현. plan → build → review → simplify → test. Use when: /ax-implement, 구현, 빌드, 개발"
---

<!--
[ax-implement seed v0 — team-ax 포팅 노트]

이 문서는 team-product/skills/product-implement 의 seed 포팅본이다.
v0.2 원칙 (plan R12): **복사 후 불필요한 것 주석만**. 본격 재구성은 levelup loop 가 담당.

moomoo-ax 실행 환경 차이:
- src/loop.py 가 Claude CLI 를 single call 로 호출 (subagent 오케스트레이션 없음)
- conductor 메인세션 / planner·executor·reviewer·qa subagent 계층 없음
- .phase 파일, phase-usage-logger.sh, Codex Adversarial 은 v0.2 범위 밖
- references/* 파일 내용은 이 single call 에서 로드되지 않음 (경로만 유지)

→ 해당 구간은 `[ax-note]` 주석으로 표시. 로직은 건드리지 않음.
→ levelup loop 가 이 SKILL.md 를 iteration 간 개선. deterministic 규칙은 script 추출 후보.
-->

# /ax-implement

구현. plan → build → review → simplify → test.

## 최우선 코드 품질 규칙 (HARD RULES)

이 규칙은 build/review/simplify 전 단계에서 **무조건** 적용된다. 위반 시 verdict=partial 로 간주하고 Self-check 에 명시한다.

### R-LEN. 공개 함수 본체 ≤ 60줄

- 모듈에서 export 되는 모든 함수(기본 export 포함)의 **본체(body)** 는 60줄을 넘을 수 없다.
  - "본체 줄 수" = 함수 여는 `{` 다음 줄부터 닫는 `}` 전 줄까지. 빈 줄 포함.
- 60줄을 넘길 것 같으면 **즉시** 내부 블록을 `function` 또는 `const helper = ...` 로 분리한다.
  - 분리 기준 힌트:
    - 정규식 매칭 + 추출 + 반환 객체 조립 → 매칭 단계별로 `tryMatchX(text, base): DateTagResult | null` 같은 헬퍼로 쪼갠다.
    - 공통 후처리(예: `cleanText`/`label` 조립)는 `buildResult(...)` 헬퍼로 뺀다.
    - 날짜 계산, 인덱스 계산, 패딩 같은 순수 계산은 `startOfDay`, `addDays`, `nextWeekdayFrom` 등 작은 함수로 분리.
- 공개 함수는 **분기 디스패처** 형태를 선호한다: 각 패턴 매칭 헬퍼를 순서대로 호출하고, 첫 성공을 반환. dispatcher 자체도 60줄 안에 들어와야 한다.
- 헬퍼 함수도 가능한 한 20~30줄 이내로 유지. 헬퍼가 다시 60줄을 넘기면 재분리한다.

### R-DRY. 리터럴/상수 단일 선언

같은 의미의 값은 **모듈 상단의 단일 상수** 에서만 선언하고, 정규식과 문자열은 그 상수를 **참조** 해야 한다. 같은 리터럴이 코드(정규식 alternation 포함)에서 2회 이상 반복되면 규칙 위반으로 본다.

필수 적용 대상 (예시 — 도메인에 맞춰 적용):

- **요일 한글 이름**: `일/월/화/수/목/토/금` 및 `일요일/월요일/...` 은 `DAYS`, `WEEKDAY_LONG` 같은 상수 배열/객체에 한 번만 정의한다. 라벨 생성, 요일 인덱스 조회, 정규식 alternation 모두 이 상수에서 파생.
- **상대 날짜 키워드**: `내일/모레/글피` 등은 `RELATIVE_OFFSETS` 한 곳에서만 정의. 정규식은 `Object.keys(RELATIVE_OFFSETS).join("|")` 로 생성.
- **수량/시간 단위**: `일/주/개월/년` 등은 `UNIT_TO_DAYS` 한 곳에서만 정의. 정규식과 계산 모두 동일 소스에서 파생.
- **특수 트리거 문자**: `@`, `#` 등은 `const TAG_PREFIX = "@"` 같은 상수 하나로 관리하고 정규식에서는 `new RegExp(\`\${TAG_PREFIX}...\`)` 로 합성.
- **매직 넘버**: 요일 보정(`+7`, `%7`), 월요일 인덱스(`1`) 같은 계산 상수도 가능한 이름 상수로 뽑는다 (`DAYS_IN_WEEK = 7`, `MONDAY_INDEX = 1`).

정규식을 문자열 리터럴로 쓰는 경우에도 동일:
