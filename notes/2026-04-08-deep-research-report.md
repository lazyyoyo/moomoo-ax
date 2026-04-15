# Claude Code 기반 플러그인 마켓플레이스를 위한 하네스 엔지니어링·멀티모델 오케스트레이션·auto-research 통합 구현 리서치

## 문제 정의와 제약 조건

현재 상황의 핵심 제약은 “사람(오너) 리뷰가 사실상 유일한 피드백 루프”로 동작해 디자인 디테일 완성도가 쉽게 상향되지 못한다는 점과, 에이전트 파이프라인이 장시간·대규모 컨텍스트(파일 읽기/명령 출력/대화 누적)를 동반하면서 토큰·사용량 상한을 빠르게 소진한다는 점입니다. citeturn31view0turn32view0

구독형 사용량은 “세션 길이 제한(컨텍스트 윈도우)”과 “기간별 사용량 제한(usage limit)”이 별도로 존재하며, Claude/Claude Code/데스크톱 등 서로 다른 표면에서의 사용이 동일한 usage limit 풀에 합산된다는 점이 운영상 중요한 전제입니다. citeturn36view3turn35view1 또한 고급 추론(extended thinking)이나 도구/커넥터 사용은 토큰 소모를 크게 만들 수 있어(문서에서 “tool/connector는 token-intensive”로 명시) 설계·운영 단계에서 의도적으로 억제/격리할 필요가 있습니다. citeturn36view3turn16view2

이 리서치는 “개념 소개”가 아니라, (1) 멱등적 결과를 강제하는 하네스(게이트/룰/린트/검증)로 품질 루프를 자동화하고, (2) 모델별 강점을 살린 CLI 오케스트레이션으로 토큰을 티어링하며, (3) auto-research식 ‘평가 함수 기반 반복 최적화’를 제품 개발 파이프라인 define→design→implement→qa→deploy에 삽입하는 통합 플러그인 설계로 수렴합니다. citeturn8view0turn23view0turn32view0turn34view1turn13view0

## 하네스 엔지니어링의 실무 적용 구조

### “하네스”를 구현 요소로 분해하기

하네스는 “모델이 무엇이든, 결과가 일정한 궤도를 벗어나지 않게 만드는 외부 구조”로 이해하는 것이 실무적입니다. 이 관점에서 하네스는 (a) **결정적(deterministic) 규칙**(린터, 포맷터, 파일 보호, import 정렬, 금지 패턴 등)과 (b) **판단이 필요한 규칙**(LLM judge/체크리스트/휴리스틱)로 구성됩니다. citeturn23view0turn17view0turn18view2

Claude Code 관점에서 결정적 하네스의 1차 구현 수단은 “Hooks”입니다. Hooks는 특정 이벤트에 사용자 정의 셸 커맨드를 실행해, “LLM이 선택적으로 실행할지 말지”가 아니라 “항상 실행되도록” 동작을 강제한다고 문서에 명시되어 있습니다. citeturn23view0 즉, “일관성(멱등성)을 위한 강제력”을 프롬프트가 아니라 런타임 규칙으로 옮기는 것이 하네스 엔지니어링의 실무 핵심입니다. citeturn23view0turn18view2

또한 “역할 분리 + 검수 게이트 + 실패 시 반송(재작업)” 구조가 결과의 일관성을 높인다는 사례 서술이 존재합니다(Writer/Researcher/Reviewer 분리, 체크리스트 불합격 시 반송). citeturn18view1turn31view0 이 구조는 Claude Code 문서의 “Writer/Reviewer 패턴(신선한 컨텍스트에서 리뷰)”과도 결이 같습니다. citeturn32view1

### CPS(Context–Problem–Solution)로 기획 문서를 “평가 가능한 스펙”으로 만드는 방법

CPS는 패턴 기술에서 “문제가 발생하는 상황(Context), 해결해야 할 문제(Problem), 해결책(Solution)”의 관계를 핵심으로 보고, 패턴 설명이 이 세 요소를 반드시 포함해야 한다고 정리합니다. citeturn22view1 실무에서는 CPS를 “에이전트가 (1) 무엇을 이해해야 하고, (2) 무엇이 실패인지 알 수 있으며, (3) 어떤 산출물을 어떤 형태로 내야 하는지”로 바꾸는 것이 중요합니다. citeturn31view0turn23view0

다음은 “CPS를 ‘검증 가능한 산출물 계약’으로 강화”한 템플릿입니다(핵심은 Solution을 **아키텍처/UX/검증/완료조건**까지 포함한 계약으로 만드는 것입니다). citeturn22view1turn31view0turn16view2

```md
# CPS Spec: <feature-name>

## Context
- 제품/플러그인 위치: (repo path, plugin id)
- 사용자 시나리오: (user story)
- 디자인 시스템: (토큰/컴포넌트/규칙의 출처 파일 경로)
- 기술 제약: (프레임워크, 상태관리, i18n, 접근성 기준, 성능 예산)
- 변경 금지 영역: (protected files / folders)

## Problem
- 현재 문제가 드러나는 증상: (스크린샷/영상/재현 steps)
- 실패 정의(DoD의 반대): (예: spacing mismatch, a11y regression, lint fail)
- 우선순위/범위: (in-scope / out-of-scope)

## Solution
### Output Contract
- 생성/수정 파일 목록(예상): (paths)
- UI 결과물: (어떤 화면/컴포넌트가 어떻게 바뀌는지)
- 코드 품질: (lint rules, typecheck, test)
- UX 일관성: (interaction, emptystate, skeleton, loading, motion)

### Verification (Gates)
- Gate 1: 정적 규칙 (lint/format/import/name)
- Gate 2: 테스트 (unit/integration/e2e)
- Gate 3: 시각 회귀 (Playwright screenshot)
- Gate 4: LLM Judge 체크리스트 (design/ux/code)

### Acceptance Criteria (Pass/Fail)
- 숫자 기준: (예: screenshot diff <= 0.1%, a11y violations=0)
- 체크리스트 기준: (Yes >= N, critical=0)
- 재작업 조건: (fail이면 어떤 단계로 되돌리는지)
```

이 구조는 “검증 기준을 제공하면 에이전트 성능이 크게 좋아지고, 스크린샷 비교·테스트 실행·출력 검증이 가능할 때 피드백 루프가 자동화된다”는 Claude Code 권고와 직접 맞물립니다. citeturn31view0turn23view0

### 린터/커스텀 룰로 “AI 코드 생성 가능 공간”을 축소하는 실제 패턴

정적 하네스의 목적은 “좋은 코드를 생성하라”가 아니라 “나쁜 코드가 생성될 수 없게 만들기”입니다. 이를 위해서는 (1) 룰셋을 명문화하고, (2) 에이전트가 코드를 쓰는 즉시 자동 적용되도록 만들며, (3) 실패 시 자동 수정 또는 재작업 루프로 연결해야 합니다. citeturn23view0turn16view2turn9search3

#### 파일명/폴더명 강제

파일명 컨벤션은 “결과물 탐색 비용”과 “리팩터링 안정성”에 직결되므로, 프롬프트 규칙보다 린터 규칙이 강합니다. 파일명 강제용 ESLint 플러그인(예: `eslint-plugin-check-file`, `eslint-plugin-filenames`, `eslint-plugin-validate-filename`)은 폴더/파일 패턴을 규칙으로 고정합니다. citeturn5search21turn5search9turn5search29

#### import 순서/그룹/정렬 강제

내장 `sort-imports`는 “선언 내 멤버 정렬 + 일부 자동 수정”에 강점이 있지만, 멀티라인 재정렬 등은 제한이 있다는 점이 문서에 명시되어 있습니다. citeturn5search18 프로젝트 단위로 import 그룹(외부/내부/상대/스타일 등)과 빈 줄 규칙을 강제하려면 `eslint-plugin-import` 계열 규칙(`import/order`)이나 import helper 계열을 함께 사용하는 사례가 일반적입니다. citeturn5search30turn5search14

#### 커스텀 룰 제작과 “에이전트 통제 포인트”로의 임베딩

커스텀 룰은 “AI가 자주 만드는 구조적 실수”를 규칙으로 박아넣는 방식이 유효합니다(예: 금지된 추상화 레벨, 특정 폴더에서의 특정 import 금지, 디자인 토큰 직접 값 사용 금지 등). ESLint는 플러그인이 커스텀 룰을 노출하는 구조(`rules` export)를 공식 문서로 안내합니다. citeturn5search28 또한 타입스크립트 프로젝트에서 강력한 제약을 걸려면 typed linting을 고려해야 하며, 타입 정보를 쓰는 규칙은 느리지만 더 강력하다는 점이 문서에 명시되어 있습니다. citeturn5search35

이 룰들을 “AI 생성 루프”에 직접 연결하려면, (a) CLI 실행(예: `eslint --fix`)을 hooks의 PostToolUse에 붙여 자동 실행하거나, (b) Node.js API로 ESLint를 호출해 결과를 JSON으로 받아 “재작업 지시”로 환류시키는 방식이 있습니다. ESLint는 Node.js API 사용 목적을 “플러그인/툴 작성자가 CLI 없이 ESLint 기능을 직접 사용”하기 위함으로 설명합니다. citeturn5search16turn23view0turn32view0

### 정성적 평가(Eval) 루프를 “설명 가능한 체크리스트 + 자동 재작업”으로 구현

정성적 평가에서 가장 큰 문제는 “점수의 재현성”입니다. LLM-as-a-Judge 접근이 편리하지만, 연구에서는 Likert(1~5) 같은 총평 점수 방식이 모델 간 불일치/분산이 크다는 지적이 나와 있고, 이를 체크리스트(이진 질문)로 분해해 신뢰도를 높이려는 프레임워크가 제안됩니다(예: CheckEval). citeturn30view0turn30view1 즉, 디자인/UX/코드 품질을 “준수 여부 질문(Yes/No)”로 쪼개어, 재작업 지시를 “어떤 항목이 왜 실패했는지”로 되돌려주는 구조가 실무적으로 유리합니다. citeturn30view1turn31view0

정성 평가를 실제 게이트로 만들기 위해서는 “주관적 Judge”만 두지 않고, **객관 신호를 먼저 깔고 그 위에 Judge를 얹는** 구성이 안정적입니다.

- UI 시각 회귀: entity["organization","Playwright","browser testing tool"]는 스냅샷 기반 비교(`toMatchSnapshot`)와 스크린샷 비교(`toHaveScreenshot` 계열) 같은 기능을 문서로 제공합니다. citeturn9search3turn9search11
- 접근성 구조 회귀: Playwright는 aria snapshot(YAML 형태 접근성 트리 스냅샷)도 문서로 제공하여 구조적 UX 일관성 검증에 쓸 수 있습니다. citeturn9search31
- 에이전트 품질 자동화 도구: entity["organization","Promptfoo","llm eval cli"]는 “여러 모델/프롬프트 조합을 CLI로 평가·레드팀”하는 오픈소스 도구로 소개됩니다. citeturn9search2turn9search6
- LLM 시스템 평가 프레임워크: entity["company","OpenAI","ai research company"]의 Evals는 LLM/LLM 시스템 평가 프레임워크로, 커스텀 eval 작성 및 데이터 기반 테스트를 지원한다고 설명됩니다. citeturn9search1turn9search13

Claude Code 문서도 “테스트/스크린샷/예상 출력 등 검증 기준이 있을 때 성능이 크게 좋아지고, 없으면 사용자가 유일한 피드백 루프가 된다”고 명시합니다. citeturn31view0 따라서 “디자인 완성도 낮음 → 오너 수동 리뷰 과부하” 문제는, 하네스 관점에서는 “검증 가능한 디자인/UX 게이트의 부재”로 재정의되고, 해결은 “게이트 자동화 + 재작업 루프”가 됩니다. citeturn31view0turn23view0turn30view0

### 기존 팀 체계에 점진 도입하는 로드맵

이미 디자인 시스템/스펙 문서/에이전트 파이프라인이 있는 팀은, 하네스를 “스펙 재작성”이 아니라 “게이트 추가”로 도입하는 편이 리스크가 낮습니다. citeturn23view0turn24view0turn31view0

첫 단계는 결정적 게이트부터 시작합니다. Hooks는 코드 자동 포맷, 보호 파일 수정 차단, 컨텍스트 재주입(컴팩션 이후), 설정 변경 감사 로그 등 다양한 패턴을 예제로 제공합니다. citeturn23view0 이때 CLAUDE.md에 누적되던 “규칙 텍스트”를 hooks/skills로 옮겨 기본 컨텍스트를 줄이라는 비용 관리 가이드도 함께 적용하는 것이, 토큰과 품질을 동시에 건드립니다. citeturn16view2turn15view0

둘째 단계는 CPS 문서 체계를 “새 템플릿”으로 강제하는 것입니다. CPS 자체는 최소 3요소를 제시하지만(필수), 실무에서는 Solution에 “검증 게이트/완료조건”을 포함시켜 스펙을 바로 실행 가능한 형태로 바꿉니다. citeturn22view1turn31view0turn23view0

셋째 단계는 정성 평가를 체크리스트화하고, 실패 시 자동 재작업 루프를 붙입니다. CheckEval이 제안하는 것처럼 평가 기준을 이진 질문으로 분해하면, “왜 실패했는지”가 자동으로 드러나 재작업 프롬프트의 품질이 올라갑니다. citeturn30view0turn30view1

넷째 단계는 역할 분리(Writer/Reviewer/QA)의 멀티 에이전트 게이트 구조를 고정합니다. Claude Code의 플러그인 예시 중 “code-review” 플러그인이 다중 전문 에이전트를 병렬 실행하고, “confidence-based scoring”으로 false positive를 줄이는 방향을 제시합니다. citeturn24view0 이는 “스코어 기반 게이트”를 플러그인 차원에서 구현할 수 있음을 보여주는 실물 레퍼런스입니다. citeturn24view0turn23view0

## 멀티모델 오케스트레이션 구현 패턴

### Claude Code CLI에서 Codex CLI·Gemini CLI를 함께 쓰는 구조

핵심은 “오케스트레이터(컨트롤 플레인)”와 “워커(실행 플레인)”를 분리하는 것입니다. 오케스트레이터는 CPS/게이트/재작업 정책을 들고 전체 파이프라인을 진행하고, 워커는 특정 작업을 수행한 뒤 구조화된 산출물로 핸드오프합니다. Claude Code는 hooks/플러그인/서브에이전트로 오케스트레이션을 구성할 수 있고, 비대화(non-interactive) 실행 시 JSON/stream-json 출력으로 외부 파이프라인과 쉽게 결합됩니다. citeturn32view0turn23view0turn24view0

워커로서 CLI 기반 에이전트를 붙일 때는, 각 도구의 “헤드리스 + 구조화 출력” 지원이 실무 난이도를 크게 낮춥니다.

- entity["organization","GitHub","code hosting platform"]에 공개된 Codex CLI는 로컬에서 실행되는 코딩 에이전트로 소개되며, 설치/실행이 명확합니다. citeturn26view2turn26view0
- Codex CLI는 비대화 실행에서 newline-delimited JSON 이벤트를 출력할 수 있고(`--json`/`--experimental-json`), 최종 메시지를 파일로 저장(`--output-last-message`)하거나, 최종 응답 형상을 JSON Schema로 강제(`--output-schema`)할 수 있습니다. citeturn13view1turn13view2turn13view0
- entity["company","Google","technology company"]의 Gemini CLI는 Google Cloud 문서에서 오픈소스 터미널 에이전트로 소개되며, built-in tools + 로컬/원격 MCP + ReAct 루프 기반으로 복잡한 작업을 수행한다고 명시합니다. citeturn14view0turn33search13
- Gemini CLI는 headless 모드에서 `-p/--prompt`로 실행되고, `--output-format`으로 JSON 및 JSONL(streaming) 출력과 exit code를 제공합니다. citeturn34view0turn34view1turn34view2

따라서 Claude Code 내부에서 Bash tool로 다음과 같은 “워커 호출 패턴”을 고정할 수 있습니다(의도는 예시이며, 실제 스크립트는 플러그인에 내장합니다). citeturn32view0turn13view0turn34view1

```bash
# 1) Codex worker: 구조화 산출물 강제 + 최종 결과 파일 저장
codex exec "Generate a patch for issue X. Output JSON with fields {diff, files, notes}." \
  --output-schema ./.harness/schemas/codex_patch.schema.json \
  --output-last-message ./.harness/out/codex_patch.json \
  --json

# 2) Gemini worker: headless + JSON output (stats 포함)
gemini -p "Given cps.md, propose UI improvements and output JSON {components, tokens, rationale}." \
  --output-format json > ./.harness/out/gemini_ui.json

# 3) Claude worker(비대화): 구조화 output으로 평가/리뷰
claude -p "Evaluate .harness/out/* against the rubric; output JSON." \
  --output-format json > ./.harness/out/claude_judge.json
```

### 모델별 태스크 라우팅 전략

태스크 라우팅은 “모델 강점”보다 “컨텍스트 비용 구조”가 더 결정적입니다. Claude Code 문서에서 컨텍스트는 대화·파일 읽기·커맨드 출력 모두를 포함하며 빠르게 소진되고, 컨텍스트가 차면 성능이 저하된다고 명시합니다. citeturn15view0turn31view3 따라서 라우팅의 목표는 “고비용 추론을 줄이기”가 아니라 “고비용 추론이 필요한 순간에만 쓰기”로 정의하는 편이 안전합니다. citeturn16view2turn31view0

Claude Code 비용 가이드는 “Sonnet은 대부분 코딩에 충분하고 Opus는 복잡한 아키텍처 결정/다단계 추론에만 남겨두라”는 형태로 모델 티어링을 권고합니다. citeturn16view2 이를 멀티모델로 확장하면 다음처럼 역할을 고정할 수 있습니다(‘강점’이라기보다 ‘비용/컨텍스트 구조’ 기준입니다).

- Claude(고비용): CPS 스펙 확정, 게이트(루브릭) 정의, 최종 리뷰/판정, 실패 원인 요약 및 다음 재작업 프롬프트 생성. citeturn31view0turn16view2turn30view1  
- Codex(코드 생성 워커): 구현·리팩터링·로컬 리뷰 같은 “파일 수정/패치 생성” 중심 작업. 특히 `--output-schema`로 “산출물 형상(예: diff+메타)”을 강제하면 오케스트레이터가 안정적으로 후처리할 수 있습니다. citeturn13view0turn26view0turn13view2  
- Gemini(멀티모달/도구 집약 워커): 디자인 이미지/스케치 기반 UI 제안, 긴 컨텍스트(문서/디자인 시스템) 기반 분석, Google Search grounding 등을 활용한 리서치/검증. CLI 자체가 ReAct+tools+MCP 구조임이 문서로 명시되어 있습니다. citeturn14view0turn14view1turn34view0

### 모델 간 컨텍스트 전달을 “파일 계약”으로 표준화

컨텍스트 전달은 대화 전달이 아니라 “중간 산출물 전달”로 설계하는 편이 멱등성이 높습니다. Codex는 최종 메시지 파일 저장과 JSON Schema 검증을 지원하고, Gemini는 headless JSON 출력에 stats(토큰/툴/파일 변경) 같은 메타데이터를 포함할 수 있으며, Claude는 비대화 JSON/stream-json 출력이 가능합니다. citeturn13view0turn34view0turn32view0

따라서 `.harness/` 아래에 “항상 같은 파일 구조”를 만들고, 워커는 반드시 그 파일만 읽고/쓰도록 제한하는 것이 실무적으로 유리합니다(범위가 고정되면 평가와 캐시도 쉬워집니다). citeturn23view0turn16view2turn12view0

```text
.harness/
  cps/
    <ticket>.md
  rubrics/
    design_checklist.yml
    code_checklist.yml
  schemas/
    worker_patch.schema.json
    judge_result.schema.json
  out/
    codex_patch.json
    gemini_ui.json
    claude_judge.json
  logs/
    iteration_<n>.jsonl
```

### 토큰 비용 최적화의 중심: “컨텍스트 격리 + 전처리 + 요약”

Claude Code 비용 문서는 다음을 명시적으로 권고합니다: 컨텍스트를 작게 유지( `/clear`, `/compact`, `/context`, status line), 모델 선택(Sonnet/Opus), MCP 오버헤드 관리, hooks로 로그/테스트 출력 전처리, 서브에이전트로 verbose 작업을 격리, agent team은 토큰이 크게 늘 수 있으니 작게 유지. citeturn16view2turn16view1turn32view0 이 원칙은 멀티모델에서도 동일하게 적용됩니다. 즉, (1) 설계/판정은 고가 모델에 남기고, (2) 반복 작업은 워커에 보내며, (3) 워커 산출물은 JSON으로 요약해 돌아오게 해서 오케스트레이터 컨텍스트를 오염시키지 않는 방식입니다. citeturn34view1turn13view1turn31view2

“도구를 줄이거나, CLI 도구를 선호하라”는 비용 가이드의 조언도 멀티모델 운영에 중요합니다. 문서는 MCP 서버 정의가 컨텍스트에 영향을 주고, 가능하면 `gh/aws/gcloud` 같은 CLI 도구를 선호하라고 명시합니다. citeturn16view2turn16view1

### 멀티모델 파이프라인의 오픈소스 레퍼런스

멀티모델 오케스트레이션을 “즉시 재사용 가능한 형태”로 제공하는 레퍼런스는 다음 축으로 정리됩니다.

- Claude Code 플러그인 시스템: 공식 리포지터리의 plugins 디렉터리가 “commands/agents/skills/hooks/MCP”로 확장하는 구조를 예시로 제시합니다. citeturn24view0turn23view0  
- Codex CLI 오픈소스: 로컬 실행 코딩 에이전트로서 설치/퀵스타트와 함께 제공됩니다. citeturn26view0turn25view3  
- Gemini CLI 오픈소스: 터미널 에이전트 + MCP 지원 + headless JSON/JSONL + exit code까지 포함하는 자동화 지향 인터페이스를 제공합니다. citeturn27view0turn34view1turn34view0  
- 평가 프레임워크: Promptfoo(멀티모델 eval CLI), OpenAI Evals(LLM 시스템 eval 프레임워크) 같은 도구가 “반복 가능한 평가”를 도구화합니다. citeturn9search2turn9search1turn9search13

## auto-research의 아키텍처와 제품 개발 파이프라인 적용

### auto-research의 동작 원리

entity["people","Andrej Karpathy","ai researcher"]의 auto-research는 “에이전트가 코드를 수정 → 짧은 학습(5분) → 평가 지표가 개선되면 유지, 아니면 폐기 → 반복”이라는 루프를 표방합니다. citeturn37view1turn37view0 핵심 설계 선택은 세 가지로 요약됩니다.

첫째, 수정 범위를 단일 파일로 고정합니다(`train.py`만 수정; `prepare.py`는 평가/데이터 유틸로 고정). citeturn37view0turn37view1 둘째, 실험 예산을 고정합니다(항상 5분). citeturn37view0turn37view1 셋째, 평가 함수를 단일 scalar metric으로 고정합니다(val_bpb; 낮을수록 좋음). citeturn37view0turn37view1 이런 구조 덕분에 “루프가 멈추지 않고 계속 돌아가며, 개선을 확인했을 때만 브랜치를 전진시키는” 방식이 안전하게 성립합니다. citeturn37view2turn37view3

또한 `program.md`는 실험 설정, 로그 기록(`results.tsv`), keep/discard/crash 기준, “개선 아니면 git reset으로 되돌림” 같은 운영 규칙을 상세히 스크립팅합니다. citeturn8view0turn37view2 이 점이 중요한 이유는, auto-research가 단순한 “자동 코딩”이 아니라 “평가 함수를 중심으로 한 운영 규칙(조직 코드)”이기 때문입니다. citeturn37view1turn8view0

### “평가 함수를 바꾸면 최적화 방향이 바뀐다”를 제품 개발에 적용하는 방식

auto-research는 특정 모델/툴이 아니라, “고정된 평가 함수에 대해 로컬 탐색을 계속하면 결과가 그 평가 함수에 맞게 최적화된다”는 구조를 실증하려는 형태입니다(실제로 val_bpb를 기준으로 keep/discard를 반복). citeturn37view1turn37view2 실무 적용의 요지는 “무엇을 점수화할지”를 먼저 결정하고, 그 점수를 개선하는 변경만 남기게 만드는 것입니다. citeturn30view1turn31view0

여기서 디자인 디테일 완성도를 끌어올리려면, 평가 함수를 “감상”이 아니라 “검증 가능한 체크리스트 + 시각 회귀 + 접근성 구조”로 구성해야 합니다. CheckEval이 제안하는 체크리스트(이진 질문) 접근은 “점수의 설명 가능성”과 “평가 모델 간 일관성”을 목표로 합니다. citeturn30view0turn30view1 Playwright의 스크린샷/스냅샷 비교는 UI 회귀를 수치적으로 다루는 기반이 됩니다. citeturn9search11turn9search3

### define→design→implement→qa→deploy에 auto-research 루프 삽입

auto-research의 “단일 수정 범위” 아이디어를 제품 개발에 그대로 옮기면, 각 단계별로 **수정 가능 영역**과 **평가 함수**를 고정해 반복 루프를 만들 수 있습니다. citeturn37view0turn23view0turn31view0

- define: CPS 문서만 수정 가능(스펙 자체의 품질을 개선). CPS는 Context/Problem/Solution 3요소를 필수로 하며, 이를 검증 게이트까지 포함하는 계약으로 확장할 수 있습니다. citeturn22view1turn31view0  
- design: 디자인 토큰/컴포넌트 문서/스토리북 스냅샷(또는 UI 샘플 페이지)만 수정 가능. 평가는 (a) 시각 회귀, (b) 체크리스트(타이포/간격/색/컴포넌트 사용), (c) 접근성 스냅샷으로 구성합니다. citeturn9search11turn9search31turn30view1  
- implement: 구현 코드만 수정 가능. 평가는 lint/type/test + 코드 품질 체크리스트입니다. citeturn31view0turn5search16turn16view2  
- qa: 테스트/시나리오/스크린샷 골든만 수정 가능. 평가는 테스트 통과 + 회귀 diff입니다. citeturn9search11turn31view0  
- deploy: 배포 스크립트/릴리즈 노트/모니터링 규칙만 수정 가능(이 단계는 “자동 변경”보다 “검증/리포팅 자동화”에 비중이 큽니다). citeturn32view0turn34view1  

이렇게 단계별로 “수정 가능 파일 집합”을 좁히면, auto-research가 `train.py`만 수정하게 한 이유(스코프 관리, diff 검토 용이)와 구조적으로 동일해집니다. citeturn37view0turn37view1

### 디자인 완성도 평가에 auto-research 패턴을 적용하는 구체 구현 방향

디자인 완성도는 단일 숫자로 환원하기 어렵기 때문에, 실무에서는 “다중 신호 → 단일 합성 점수”가 필요합니다. CheckEval류 접근을 따르면, 루브릭을 이진 질문으로 분해한 뒤 가중치를 부여해 합산 점수를 만들 수 있고, 실패 항목이 곧 재작업 프롬프트의 근거가 됩니다. citeturn30view1turn30view0

합성 점수 예시는 다음처럼 구성될 수 있습니다(구현 시에는 YAML/JSON으로 정의하고, 루프마다 동일하게 평가합니다). citeturn34view1turn9search11turn31view0

- 시각 회귀 점수: Playwright 스크린샷 diff가 임계값 이하이면 통과. citeturn9search11turn9search3  
- 접근성 구조 점수: aria snapshot 변화가 허용 범위 내인지(또는 위반 0). citeturn9search31  
- 디자인 체크리스트 점수: 타이포 스케일 준수, spacing 토큰 사용, 버튼/폼 상태(hover/disabled/loading) 존재, empty/error state 존재 등 Yes/No. citeturn30view1turn31view0  
- 코드/구성 체크리스트 점수: 컴포넌트 재사용, import 규칙, 파일명 규칙 위반 0. citeturn5search18turn5search21turn5search16  

이 방식은 “검증이 가능하면 에이전트가 스스로 비교·수정·반복할 수 있다”는 Claude Code 지침과 합치합니다. citeturn31view0turn23view0

## 세 주제를 하나의 새 플러그인으로 통합하는 설계안

### 플러그인 패키징 단위와 구성 요소

Claude Code 플러그인 예시 디렉터리는 플러그인이 “custom slash commands, specialized agents, hooks, MCP servers”로 확장된다고 설명하고, 표준 구조(`commands/agents/skills/hooks/.mcp.json`)를 제시합니다. citeturn24view0turn23view0 이를 기반으로 “Harness Orchestrator” 플러그인은 다음 4가지를 한꺼번에 묶는 것이 자연스럽습니다.

- Commands: `/harness:spec`, `/harness:run`, `/harness:eval`, `/harness:loop` 같은 진입점. citeturn24view0turn32view0  
- Agents: (Planner/Implementer/Design-Reviewer/QA-Runner) 역할 분리 에이전트. citeturn32view1turn31view0turn18view2  
- Hooks: 결정적 강제(포맷/린트/보호 파일/컨텍스트 재주입/감사 로그). citeturn23view0turn16view1  
- Worker Integrations: Codex/Gemini 호출 래퍼(헤드리스 JSON/JSONL 수집, 스키마 검증, 아티팩트 저장). citeturn13view0turn34view1turn32view0  

### 통합 플러그인의 “하네스 루프” 실행 엔진

Claude Code 문서는 비대화 모드(`claude -p`)와 `--output-format`(json/stream-json)을 명시적으로 제공하고, 이를 CI/스크립트/자동화에 사용하라고 안내합니다. citeturn32view0 Gemini도 headless JSON/JSONL과 exit code를 제공하고, Codex도 JSON 이벤트 및 최종 메시지 파일 저장/스키마 검증을 제공합니다. citeturn34view1turn13view0turn13view1

따라서 실행 엔진은 “동일한 루프를 N회 반복하며, 각 반복의 결과를 아티팩트로 남기고, 게이트 통과 시에만 변경을 전진시키는” 형태가 됩니다. 이 구조는 auto-research의 `keep/discard`와 동일하며, git reset을 이용한 되돌림 규칙도 그대로 차용할 수 있습니다. citeturn37view2turn37view3

아래는 통합 플러그인이 내부적으로 따를 수 있는 “단일 루프”의 의사 절차입니다(구현 언어는 임의입니다).

```text
Inputs:
  - cps/<ticket>.md
  - rubrics/*.yml
  - budgets: {max_iterations, max_tokens_per_stage, max_wall_time}

Loop i=1..N:
  1) PLAN: Claude가 CPS를 기반으로 실행 계획(파일 범위/게이트)을 확정
  2) DESIGN worker: Gemini가 UI 개선 제안/컴포넌트 계획을 JSON으로 산출
  3) IMPLEMENT worker: Codex가 패치를 생성 (schema-validated JSON: diff/files/notes)
  4) APPLY: 패치 적용(또는 Codex가 직접 수정)
  5) STATIC gates: format/lint/typecheck
  6) UI gates: playwright screenshots + aria snapshots
  7) JUDGE gate: Claude judge 체크리스트(Yes/No) + 합성 점수 계산
  8) DECISION:
      - pass: commit & advance
      - fail: 자동 재작업 프롬프트 생성 → 다음 반복으로
      - crash/timeouts: discard & revert
Outputs:
  - out/iteration_i/*.json + logs/*.jsonl
  - 최종 PR 또는 변경 commit
```

이 설계는 (a) Claude Code가 강조하는 “검증 기준 제공”, (b) hooks 기반의 결정적 강제, (c) 멀티세션/서브에이전트를 통한 컨텍스트 격리, (d) auto-research의 keep/discard 반복을 하나로 합친 형태입니다. citeturn31view0turn23view0turn32view1turn37view2

### 디자인 디테일 완성도를 올리는 “게이트 우선순위” 제안

오너 수동 리뷰 시간을 줄이려면, 사람이 보는 항목을 게이트로 옮기는 순서가 중요합니다. Claude Code 문서에서 UI 변화는 “스크린샷 비교”로 검증하라고 제시되어 있고, 이것이 피드백 루프 자동화의 핵심으로 설명됩니다. citeturn31view0 이에 맞춰 게이트를 “정적 규칙 → 시각 회귀 → 체크리스트 Judge” 순으로 쌓으면, 가장 값싼 신호로 먼저 걸러내고(린트/포맷), 그다음 UI 회귀를 수치로 막고(스크린샷), 마지막에만 주관 판단을 쓰게 됩니다. citeturn9search11turn30view1turn16view2

특히 CheckEval이 강조하는 “평가 기준을 이진 질문으로 분해하면 일관성이 올라간다”는 요지는, 디자인 완성도 평가에서 “좋아요/나빠요” 대신 “토큰 사용 준수?”, “상태(hover/disabled/loading) 존재?”, “간격 스케일 위반?”처럼 판정 가능한 질문으로 바꿔야 한다는 의미로 직접 연결됩니다. citeturn30view0turn30view1

## 운영 관점에서의 토큰·사용량·안정성 관리

첫째, Claude 사용량은 “모델/대화 길이/기능(도구/커넥터)”에 따라 달라지고, 여러 표면에서의 사용이 합산되므로, 자동화 루프가 동작할수록 예측 가능성을 높이기 위해 **컨텍스트 크기·도구 사용·추론 예산**을 고정해야 합니다. citeturn36view3turn16view2turn23view0

둘째, Claude Code 비용 가이드는 hooks로 로그/테스트 출력 전처리를 해서 “수만 토큰을 수백 토큰으로 줄일 수 있다”는 형태의 예시를 제공합니다. citeturn16view1turn23view0 이 패턴은 멀티모델 오케스트레이션에서도 그대로 유효하며, 특히 디자인 평가에서 스크린샷 diff/테스트 로그 같은 verbose 데이터를 “요약 후 반환”으로 바꾸는 것이 오케스트레이터 컨텍스트를 보호합니다. citeturn31view0turn16view2turn34view1

셋째, 구독 한도에 닿았을 때의 운영 옵션은 “리셋 대기” 외에도 extra usage(pay-as-you-go 전환)와 usage bundles(선구매 할인)이 존재합니다. extra usage는 “포함 사용량을 소진한 뒤 표준 API 요율로 소비 기반 과금으로 전환”하는 기능으로 설명되며, usage bundles는 “표준 extra usage 대비 최대 30% 절감” 및 “Claude/Claude Code 등 across products 단일 풀”로 설명됩니다. citeturn36view2turn36view0turn35view1

넷째, 자동화 루프는 실패 시 재시도 정책이 곧 비용 폭탄이 될 수 있습니다. 실제로 Claude Code 사용자가 “예상보다 훨씬 빨리 usage limit에 도달한다”는 문제를 겪고 있고, 관련 이슈를 entity["organization","The Register","technology news site"]는 “early quota exhaustion” 및 자동화 워크플로우 파손으로 보도하면서, 공급자가 문제를 인지했다고 전합니다. citeturn19view0turn19view1 따라서 통합 플러그인에서는 “재시도 횟수 상한, 시간 상한, 실패 시 즉시 discard/revert”가 auto-research의 운영 규칙처럼 1급 정책으로 들어가야 합니다. citeturn37view2turn18view2

마지막으로, 결정적 강제는 보안에도 직결됩니다. Claude Code hooks 예시는 `.env` 등 보호 파일 수정 차단을 PreToolUse로 구현하고, exit code/결정으로 편집을 block할 수 있음을 보여줍니다. citeturn23view0 이 패턴을 멀티모델 워커 호출에도 확장해, “허용된 디렉터리/허용된 명령/허용된 파일 집합”을 정책으로 고정하면, 모델이 바뀌어도 멱등적인 안전 경계가 유지됩니다. citeturn23view0turn13view3turn34view1