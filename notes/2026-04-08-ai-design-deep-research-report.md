# AI 에이전트 기반 UI/UX 디자인 완성도 자동화 시스템 리서치

## 목표를 “오너 리뷰 제거”가 아니라 “게이트 통과 자동화”로 재정의

현재 프로세스(목업 생성 → 오너 피드백 → 수정 반복)가 장기적으로 오너 시간을 소모하는 이유는, “좋은 디자인”을 판정하는 기준이 사람 머릿속(암묵지)에 있고, 그 기준이 **기계가 실행 가능한 형태(테스트/린트/루브릭/스냅샷)**로 충분히 전환되지 않았기 때문입니다. 이런 상황에서는 에이전트가 개선해도 “통과/불통과”가 불명확해 반복이 늘어나기 쉽습니다. 이를 실무적으로 해결하려면 목표를 “더 잘 만들어라”가 아니라 “아래 게이트를 통과하면 merge 가능”으로 바꿔야 합니다. citeturn0search0turn0search1turn0search2turn3search1turn1search1

게이트는 비용(실행 시간/토큰) 순서대로 계층화하는 편이 안정적입니다. 예를 들어 (1) 정적 규칙(포맷/린트/타입), (2) 시각 회귀(스크린샷 diff), (3) 접근성 구조 회귀(ARIA snapshot), (4) LLM Judge(체크리스트 기반)처럼 “값싼 신호로 먼저 걸러내고, 비싼 판단은 마지막에” 배치합니다. Playwright는 스크린샷 기반 시각 비교를 기본 기능으로 제공하며, ARIA 스냅샷은 접근성 트리(YAML)를 저장/비교하는 방식으로 구조 변화 검증에 사용할 수 있습니다. citeturn0search2turn0search19turn3search3turn3search37

이 구조로 전환하면 오너의 역할은 “매번 픽셀 리뷰”에서 “루브릭(체크리스트) 정의와 임계값 튜닝”으로 이동합니다. CheckEval 연구는 LLM-as-Judge가 Likert 점수(예: 1~5) 방식에서 합의율이 낮고 분산이 크며, 이를 이진(Yes/No) 체크리스트로 분해하면 평가 신뢰도가 개선된다고 보고합니다. 즉, “디자인 완성도”도 점수보다 체크리스트가 운영에 유리합니다. citeturn1search1turn1search9turn1search5

## AI 에이전트 기반 디자인 품질 자동화 사례와 현실적인 구현 단위

### 디자이너 없이 ‘프로덕션에 가까운 UI’에 도달한 사례 유형

실무에서 “디자이너 없이도 빠르게 그럴듯한 UI”가 가능한 사례는 대체로 (A) **반복 가능한 컴포넌트/토큰 체계가 이미 있는 스택**(예: shadcn/ui+Tailwind) 위에 (B) **생성형 UI 도구/에이전트**를 얹고 (C) **반복 루프를 도구화(버전·diff·스크린샷)**한 형태로 나타납니다.

- entity["company","Vercel","cloud platform company"]의 v0는 React/Tailwind/shadcn UI 같은 오픈소스 툴 기반 코드 생성과 반복(iteration) 편집 흐름을 공식적으로 설명하며, 특정 팀이 v0로 실제 제품 페이지/기능을 만든 예시(Braintrust의 pricing page, Ingo의 초기 제품 등)를 함께 제시합니다. citeturn2search12turn2search20  
- v0를 이용해 “복사-붙여넣기형(코드 소유권 유지)” 컴포넌트 컬렉션을 만든 커뮤니티 프로젝트도 관찰됩니다(예: Tailwind+React 기반 컴포넌트 묶음). 이는 “디자이너가 없어도 UI 라이브러리의 형태를 빠르게 누적”하는 유형에 가깝습니다. citeturn2search23turn2search20  
- 학술/연구 측면에서는 “UI 스크린샷 → 멀티모달 LLM이 디자인 피드백/바운딩박스/품질 점수”를 생성하는 체인(프롬프트 체인 + 유사도 기반 few-shot 선택)을 제안한 연구가 있으며, 이는 “에이전트가 사람이 하던 UI 리뷰를 자동화하려는” 방향의 구체 청사진으로 볼 수 있습니다. citeturn3search1turn3search8turn3search14  

### 디자인 시스템을 에이전트가 ‘항상 참조’하게 만드는 방법

핵심은 “프롬프트 상의 약속”이 아니라 “실행 환경에서 강제되는 참조 경로”를 만드는 것입니다. Claude Code는 hooks로 이벤트 기반 커맨드 실행 및 컨텍스트 주입을 지원합니다. 특히 `UserPromptSubmit` 이벤트는 `additionalContext` 형태로 텍스트를 컨텍스트에 주입할 수 있어, 매번 DESIGN_SYSTEM.md 전체를 붙여넣지 않고도 “요약/규칙/금지사항”을 자동으로 삽입하는 구조를 만들 수 있습니다. citeturn0search0turn0search13

실무적으로는 다음 3단으로 분리하면 운영이 쉽습니다.

- **규칙의 단일 소스**: `DESIGN_SYSTEM.md`, `brand/`, “디자인 원칙” 문서를 변경 이력과 함께 유지(이미 보유).  
- **자동 주입 레이어**: hooks가 “현재 작업 범위에서 필요한 규칙만” 짧게 주입(예: 타이포 스케일, spacing 규칙, 색상 토큰 사용, shadcn 컴포넌트 우선 사용). citeturn0search0turn0search13  
- **정적 강제 레이어**: 포맷터/린터/커스텀 룰로 “규칙 위반 결과물이 저장/커밋되기 어렵게” 구성. Tailwind는 공식 Prettier 플러그인으로 클래스 정렬을 자동화할 수 있고, ESLint 플러그인으로 Tailwind 사용 일관성(클래스 순서/모순된 클래스/비허용 클래스 등)을 규칙화할 수 있습니다. citeturn2search13turn2search0turn2search1turn2search10turn2search4turn2search7  

### shadcn/ui + Tailwind 환경에서 품질을 끌어올리는 실전 패턴

shadcn/ui는 “디자인 시스템의 기반”을 표방하며, 커스터마이즈/확장 가능한 컴포넌트를 제공하는 형태(코드 복사-붙여넣기 중심)로 운영됩니다. Tailwind v4 마이그레이션 문서에서도 shadcn/ui의 장점으로 “숨겨진 추상화가 없고, 최종적으로 프로젝트에 남는 코드는 본인이 직접 썼을 법한 코드”임을 강조합니다. 이 특성은 AI 에이전트 운영에서 특히 유리합니다(정답 공간이 ‘프로젝트에 존재하는 컴포넌트/토큰’으로 좁아지기 때문). citeturn2search2turn2search11turn2search26

구현 패턴은 (1) 생성 범위 제한, (2) 조합 규칙 고정, (3) 스타일 일관성 자동화로 쪼개는 편이 안정적입니다.

- (1) **생성 범위 제한**: “원시 HTML 요소 직접 스타일링”보다 `components/ui/*`(shadcn)와 프로젝트 공통 컴포넌트만 조합하도록 룰을 둡니다. shadcn/ui가 “프로젝트에 코드가 들어오고 이후 로컬 컴포넌트처럼 다룬다”는 운영 모델과 잘 맞습니다. citeturn2search26turn2search2  
- (2) **조합 규칙 고정**: 예를 들어 “페이지 레이아웃은 `Container`+`Section`+`Stack` 같은 얇은 래퍼로만 구성, 섹션 간 간격은 spacing 토큰만 사용”처럼 조합 단위를 정하면, 에이전트가 불필요한 CSS 발명(임의 값)을 할 확률이 줄어듭니다. (이 부분은 팀 문서로 고정하는 것이 핵심이며, 강제는 린트/테스트로 수행) citeturn0search0turn2search2  
- (3) **스타일 일관성 자동화**: Tailwind 클래스 정렬(Prettier) + Tailwind ESLint(모순/비허용/순서)로 “클래스 혼잡도”와 “충돌”을 줄입니다. 이는 간격/정렬 문제의 상당 부분(특히 변형 클래스 혼재)을 조기에 드러내는 데 유리합니다. citeturn2search13turn2search0turn2search10turn2search7turn2search4  

또한 spacing/타이포의 디테일을 “선호”가 아니라 “규칙”으로 만들려면 스케일을 강제해야 합니다. Material Design은 레이아웃 spacing을 4dp 단위 증분으로 다루는 방식과 타이포 적용 가이드를 제공합니다. Tailwind 기본 스케일(4px 계열)과 정합이 좋아, “간격은 4px 기반 배수로만” 같은 룰을 만들 때 참고 근거로 사용할 수 있습니다. citeturn5search26turn5search2turn5search10  

## 디자인 평가 자동화 설계: 페르소나 + 동적 체크리스트 + 스크린샷/비전

### 페르소나를 “사전 정의”가 아니라 “기능 컨텍스트에서 자동 도출”하는 구현

페르소나 자동 생성은 연구/실무에서 활발히 다뤄지고 있으며, LLM을 이용해 페르소나를 생성하고 그 품질을 평가하는 연구가 존재합니다. 또한 인터뷰 기반 정성 데이터에서 LLM을 활용해 페르소나/시나리오를 도출하고 설계 프로세스에 통합하는 절차를 제안한 연구도 있습니다. 따라서 구현 목표는 “정교한 페르소나 문서 작성”이 아니라, **기능 스펙에서 테스트 가능한 사용자 관점 세트를 생성**하는 데 두는 편이 낫습니다. citeturn3search6turn3search12turn3search2

실무 구현은 다음 JSON 산출물 계약으로 고정하는 방식이 좋습니다(이렇게 해야 이후 Judge 단계가 deterministic하게 작동합니다).  

```json
{
  "feature": "reading-log",
  "personas": [
    {
      "id": "p1",
      "name": "바쁜 직장인",
      "goals": ["매일 10분 독서 기록", "다음에 읽을 책 빠르게 결정"],
      "constraints": ["모바일 사용", "짧은 세션", "알림 선호"],
      "success_signals": ["2탭 이내 기록 완료", "상태가 명확히 보임"]
    }
  ],
  "critical_journeys": [
    {
      "id": "j1",
      "persona_id": "p1",
      "steps": ["홈 → 오늘 기록 → 페이지/시간 입력 → 저장 → 피드백 확인"],
      "edge_cases": ["오프라인/지연", "저장 실패", "중복 저장"]
    }
  ]
}
```

이 산출은 이후 단계에서 “UX 플로우 평가”와 “상태 처리(loading/empty/error)” 평가의 기준점으로 쓰입니다. 페르소나 도출 자체는 LLM이 수행하되, 안정성은 다음 체크리스트/게이트가 보장하는 구조입니다. citeturn1search1turn1search9turn0search2  

### 체크리스트 기준을 “기능에 따라 동적 생성”하는 방식

CheckEval은 (1) 평가 차원 정의, (2) 체크리스트 생성, (3) 체크리스트 기반 평가의 3단계를 제안하며, 고수준 기준을 Boolean QA로 번역해 신뢰도를 높이는 접근을 취합니다. 이 구조를 UI/UX로 옮기면 “고정 루브릭(항상 동일)”과 “기능별 루브릭(동적)”을 결합할 수 있습니다. citeturn1search9turn1search1turn1search13

- **고정 루브릭(항상 적용)**: spacing 스케일 준수, 타이포 계층 유지, 색 대비/가독성, 컴포넌트 일관성(shadcn 사용), 접근성 역할/라벨, 상태 처리(loading/empty/error) 존재. citeturn3search3turn2search2turn5search26turn5search2  
- **동적 루브릭(기능별 생성)**: 예를 들어 “독서 기록” 기능이면 입력 흐름(실수 방지), 저장 실패 복구, 중복 방지, 최근 기록 재편집, 타임라인/통계 노출 방식 등이 평가 항목이 됩니다. (생성 로직은 “페르소나 + critical journeys + 화면 목록”을 입력으로 하는 LLM chain으로 고정)

동적 루브릭 생성 프롬프트는 “항목을 Yes/No로 답할 수 있어야 한다”는 제약을 계약으로 넣어야 합니다(그래야 CheckEval류 장점을 살립니다). citeturn1search1turn1search9  

### Playwright 스크린샷 + LLM 비전으로 “이 UI가 좋은지” 판단하는 패턴

Playwright는 시각 비교를 위한 `toHaveScreenshot()`를 제공하며, 이는 최초 실행 시 기준 이미지를 생성하고 이후 실행에서 비교합니다. 또한 스크린샷 어서션은 “두 번 연속 동일한 결과가 나올 때까지 기다린 뒤 비교”하는 동작을 하므로, 애니메이션/로딩으로 인한 불안정성을 줄이는 데 도움이 됩니다. citeturn0search2turn0search19

접근성/구조 측면에서는 ARIA 스냅샷이 페이지 접근성 트리의 YAML 표현을 제공하고, 이를 저장·비교해 구조 일관성 검증에 활용할 수 있습니다. 이 방식은 “텍스트/역할/계층” 중심이라 시각적 변경에 비해 덜 깨지는 게이트로 쓸 수 있습니다. citeturn3search3turn3search37

여기에 멀티모달 LLM을 결합하는 구체 패턴은 UI Critique 연구가 상당히 실무 친화적인 구조를 제공합니다. 해당 연구는 “UI 스크린샷을 입력으로 멀티모달 LLM에 질의하여 디자인 피드백, 바운딩 박스, 디자인 품질 레이팅을 받는” 프롬프트 체인을 제안하며, few-shot 예시를 “태스크/시각 유사도”로 선택하는 전략을 결합합니다. 이는 곧 “레퍼런스 자동 선택 + 비전 기반 리뷰”의 결합 청사진입니다. citeturn3search1turn3search14

비전 Judge 실행은 headless CLI가 있으면 운영이 쉬워집니다. Gemini CLI는 headless 모드에서 `--prompt/-p`로 실행하고, `--output-format json` 또는 JSONL 스트리밍을 제공하며, 스크립팅/자동화와 일관된 exit code를 지원합니다. 즉 “스크린샷 파일 + 루브릭 + 스펙”을 넣고 “JSON 판정”을 받는 워커로 두기 적합합니다. citeturn0search9turn0search6turn0search3turn0search24  

## 디자인 자동 개선 루프: auto-research 패턴을 UI/UX에 이식하기

### “목업 생성 → 자동 평가 → 실패 기반 재작업 → 재평가” 아키텍처

auto-research의 핵심은 “고정된 예산(시간) 안에서 실험을 반복하고, 단일 메트릭이 개선될 때만 변경을 유지(keep)하며, 아니면 폐기(discard)한다”는 운영 규칙입니다. 원본은 5분 학습 예산과 val_bpb 최적화를 명시하며, 크래시 없이 시간 예산 내 완료되는 모든 변경을 탐색 대상으로 둡니다. citeturn1search2turn1search2

UI/UX로 이식할 때는 “예산”을 (A) 반복 횟수, (B) Playwright 실행 시간, (C) LLM Judge 호출 횟수로 치환하고, “메트릭”을 (1) 스크린샷 diff, (2) ARIA snapshot diff, (3) 체크리스트 합성 점수로 구성합니다. 기반 메커니즘은 동일하게 **keep/discard + 로그**로 구현합니다. citeturn0search2turn3search3turn1search9turn1search2

### 반복 횟수와 품질의 관계를 다루는 근거와 운영 전략

일반 텍스트 생성 영역에서는 Self-Refine가 “동일 LLM이 초안 생성 → 자기 피드백 → 자기 수정”을 반복하는 구조를 제안하며, 다양한 태스크에서 1회 생성 대비 성능/선호 개선을 보고합니다. 또한 코드/리드미 수준에서 “stopping criteria를 두고 반복”하는 흐름도를 명시합니다. 즉, 반복은 무한 루프가 아니라 **조건 충족 시 조기 종료**가 전제입니다. citeturn6view1turn6view0turn3search0

에이전트형 반복 개선에서는 Reflexion이 “피드백을 언어로 반성(reflection)하고, 이를 에피소드 메모리로 유지해 다음 시도에서 의사결정을 개선”하는 구조를 제안합니다. 이는 UI 개선에서도 “이전 실패 패턴(예: 상태 처리 누락, 간격 스케일 위반, CTA 일관성 붕괴)”을 메모리로 축적해 재발을 막는 설계 근거로 사용할 수 있습니다. citeturn1search3turn1search15turn1search27

반복 수렴을 실무적으로 관리하려면, “반복이 늘수록 토큰/시간이 증가한다”는 사실을 전제로, 아래 두 가지를 함께 둡니다.

- **조기 종료 조건**: (a) 모든 정적 게이트 통과 + (b) 시각 diff 임계값 이하 + (c) 체크리스트 critical 0개. (체크리스트 기반 설계의 장점은 “critical”을 명시적으로 둘 수 있다는 점입니다.) citeturn1search9turn0search2turn3search3  
- **반복 상한 + keep/discard**: 상한에 닿으면 best scoring 결과만 남기고 종료(자동 PR 생성 또는 “추가 판단 필요” 상태로 종료). keep/discard 규칙은 auto-research처럼 “점수 개선 시에만 유지”가 기본입니다. citeturn1search2turn1search2  

### 로컬 최적해(국소해) 회피: 다양성 유지와 탐색/활용 분리

로컬 최적해 회피는 “더 많이 반복”이 아니라 “다른 후보를 만든 뒤 평가로 선택”이 핵심입니다. Self-Refine 코드 예시는 temperature 샘플링으로 실행마다 다른 결과가 나올 수 있음을 명시하고 있어(=다양성의 구현 장치), UI 개선에서도 “복수 후보 생성 → 평가로 선발”이 구조적으로 자연스럽습니다. citeturn6view0

또한 비전 기반 디자인 평가 연구에서는 입력 UI와 “태스크/시각 유사도”가 높은 few-shot 예시를 선택해 평가/피드백 품질을 높이는 체인을 제안합니다. 이는 곧 “탐색 단계에서는 다양한 레퍼런스/후보를 넓게 가져오고, 활용 단계에서는 가장 유사한 근거를 좁혀 적용”하는 전략으로 볼 수 있습니다. citeturn3search1turn3search14

실제 구현에서는 다음 두 레일을 분리하는 방식이 유지보수에 유리합니다.

- **탐색 레일**: 3~5개의 후보 UI를 생성(레이아웃/정보 구조가 다르게), 각각 동일 평가를 돌려 상위 1개만 선택. (이때는 스타일 미세 조정보다 “화면 구조/흐름” 다양성에 집중) citeturn6view0turn3search1  
- **활용 레일**: 선택된 1개 후보에 대해서만 spacing/타이포/색/상태 처리 등 디테일 최적화를 반복. (이 단계에서 시각 회귀 + 체크리스트 기반) citeturn0search2turn1search9  

### 실패 항목 → 재작업 프롬프트 자동 생성 기법

재작업 프롬프트를 사람이 쓰면 결국 병목이 됩니다. CheckEval류 구조를 UI에 적용하면, 실패는 “Yes/No 질문의 No 목록”으로 표현되고, 이 No 목록이 곧 “수정 지시서”로 변환될 수 있습니다(예: “로딩 상태가 있는가? No” → “해당 화면에 skeleton 또는 spinner 상태를 추가하고, 네트워크 지연 시에도 레이아웃 점프가 없게 할 것”). citeturn1search1turn1search9

여기에 UI Critique 체인의 장점(바운딩박스/구체 피드백)을 결합하면 “어디를 무엇 때문에 고쳐야 하는지”가 더 직접적으로 생성됩니다. 실무에서는 바운딩박스 좌표를 그대로 DOM에 매핑하기 어렵기 때문에, 스크린샷 피드백을 **ARIA snapshot의 역할/이름 기반 요소 식별**과 결합해 “수정 대상 요소를 접근성 이름으로 지칭”하도록 프롬프트를 설계하는 편이 견고합니다. citeturn3search1turn3search3turn3search37  

## 디자인 레퍼런스 시스템: 구축·자동 선택·독서 관리 도메인 벤치마크

### 레퍼런스 구축: “스크린샷 저장”이 아니라 “검색 가능한 데이터셋”으로 만들기

레퍼런스는 단순히 이미지를 모으는 것이 아니라, **기능 컨텍스트로 검색 가능**해야 에이전트가 자동으로 참조할 수 있습니다. UI 데이터셋 측면에서 Rico는 “모바일 앱 디자인 스크린샷/구조 데이터를 대규모로 모아 design search, UI layout/code generation 등에 쓰일 수 있다”는 목적을 가진 대표 데이터셋으로 소개됩니다. 또한 Rico의 후속 회고 연구는 데이터셋이 다양한 연구/응용에 기반이 되었음을 정리합니다. citeturn5search1turn5search37

대규모 스크린 데이터 측면에서는 MobileViews처럼 대규모 screenshot-view hierarchy pair를 제공하는 데이터셋도 존재합니다. 이는 “도메인 레퍼런스가 부족할 때 일반 UI 패턴을 끌어오는” 백업 소스로 쓸 수 있습니다. citeturn5search21

레퍼런스의 “검색 가능성”을 올리기 위해, 멀티모달 LLM을 이용해 UI 이미지에서 의미(semantics)를 추출하고 이를 기반으로 영감형 UI 검색을 개선하는 연구가 있으며, 실제로 MLLM 기반 의미 추출/해석과 semantic UI search 시스템을 제안합니다. 이는 레퍼런스를 “시각 유사도”뿐 아니라 “의도/대상/무드/기능”으로 자동 분류·검색하는 구현 근거가 됩니다. citeturn5search0turn5search4turn5search8

### 기능별 레퍼런스 자동 선택/참조

UI Critique 연구는 입력 UI에 대해 few-shot 예시를 “태스크/시각 유사도”로 선택하는 전략을 명시합니다. 이를 제품에 적용하면, 기능 스펙(예: “독서 기록”, “서재”, “하이라이트”, “통계”)을 태스크 라벨로 보고 레퍼런스를 자동 선택한 뒤, “선택된 레퍼런스의 패턴을 준수하라”가 아니라 “왜 이 패턴이 좋은지(정보 구조/상태 처리/타이포 계층)를 추출해 적용하라”로 변환하는 체인이 가능합니다. citeturn3search1turn3search14

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["Goodreads shelves UI web app","The StoryGraph reading stats charts UI","Readwise highlights export interface","LibraryThing catalog app interface"],"num_per_query":1}

### 독서/도서 관리 도메인에서 벤치마크할 만한 UI/UX 패턴

도메인 레퍼런스는 “각 서비스의 핵심 흐름과 상태 모델”에서 추출하는 편이 실무적으로 유용합니다.

- entity["company","Goodreads","book catalog platform"]: 기본 shelf(읽고 싶음/읽는 중/읽음) 개념과 더불어, DNF(완독하지 않음) shelf를 공식 기능으로 도입하면서 “진행률 기록, shelf 간 이동 시 리뷰/히스토리 유지, Reading Challenge 반영 규칙” 등 상태 모델을 명시합니다. 이는 “상태 처리(특히 중단/보류) UX”를 설계할 때 직접적인 레퍼런스가 됩니다. citeturn4search4turn4search6  
- entity["company","The StoryGraph","reading tracker platform"]: “간단한 트래킹 + 차트/그래프 기반 통계”를 제품 핵심 가치로 전면에 두며, Goodreads 데이터(import) 및 shelf 매핑을 안내합니다. 독서 관리 앱에서 “통계 대시보드/인사이트 화면”의 정보 구조를 설계할 때 참고하기 좋습니다. citeturn4search0turn4search3  
- entity["company","Readwise","reading highlights app"]: 하이라이트/노트를 외부 도구로 export/sync하는 기능을 문서로 제공하며(Markdown/CSV 및 Notion/Obsidian 등), “읽기 → 하이라이트 → 지식 관리 도구 연계” 흐름을 명확히 합니다. 독서 앱에서 “메모/하이라이트의 목적지” UX를 설계할 때 레퍼런스가 됩니다. citeturn4search8turn4search16  
- entity["company","LibraryThing","book catalog service"]: 태그/컬렉션(의미 있는 분류 단위) 같은 조직화 개념이 커뮤니티/문서에서 논의되어 왔고, 앱 설명에서도 개인 소장 도서의 카탈로깅/검색/조직화가 핵심으로 나타납니다. “서재 조직” UX에서 태그와 컬렉션(또는 shelf)의 역할 분리를 설계할 때 참고할 만합니다. citeturn4search1turn4search13  

## Claude Code 플러그인으로 통합 구현하는 청사진

### 플러그인 구성 원칙: “명령·에이전트·훅”으로 강제 가능한 면을 최대화

Claude Code 플러그인은 “커스텀 슬래시 커맨드, 전문 에이전트, hooks, MCP 서버”를 포함하는 확장 단위로 정의됩니다. 즉, 지금 보유한 team-design 에이전트를 그대로 플러그인 내부 에이전트로 배치하고, 루프 실행은 커맨드로 노출하며, 강제(포맷/린트/테스트/스냅샷)는 hooks로 붙이는 구조가 자연스럽습니다. citeturn0search1turn0search0

hooks 문서는 matcher를 이용해 특정 도구 호출 이후(PostToolUse)에 포매터를 실행하는 예시를 제공하며, 이벤트별로 allow/block 등 의사결정 패턴이 다름을 설명합니다. 이 메커니즘을 이용하면 “AI가 파일을 수정한 직후 반드시 lint/format/test가 돈다”를 프롬프트가 아니라 실행 환경에서 보장할 수 있습니다. citeturn0search0turn0search13turn0search17

### 권장 디렉터리/아티팩트 구조(플러그인 + 하네스)

```text
plugins/design-harness/
  commands/
    design:loop.md
    design:eval.md
    design:refpack.md
  agents/
    ui-designer.json
    ux-reviewer.json
    visual-reviewer.json
    detail-reviewer.json
  hooks/
    hooks.json
  skills/
    (선택) 디자인 체크리스트 생성/요약 스킬

.harness/
  specs/
    <feature>.md
  personas/
    <feature>.json
  rubrics/
    base.yml
    feature_<feature>.yml
  refs/
    index.json
    packs/<feature>.json
    screenshots/*.png
  baselines/
    playwright/*.png
    aria/*.yml
  reports/
    iteration_<n>.json
    history.jsonl
```

이 구조의 목적은 “컨텍스트 전달을 대화가 아니라 파일 계약으로 고정”하는 것입니다. 비전 Judge/체크리스트 Judge는 항상 `.harness/` 산출물만 읽고 JSON만 쓰도록 제한하면, 세션이 리셋되어도(또는 모델이 교체되어도) 루프의 멱등성이 올라갑니다. citeturn0search0turn0search9turn1search9

### 핵심 실행 흐름: design:loop 커맨드

1) **스펙 정규화**: `<feature>.md`를 읽고 현재 변경 범위(파일/라우트/컴포넌트)를 선언  
2) **페르소나/저니 생성**: personas JSON 생성(동적) citeturn3search6turn3search12  
3) **동적 루브릭 생성**: base + feature rubric merge(이진 체크리스트) citeturn1search9turn1search1  
4) **UI 생성/수정**: ui-designer가 구현(Next.js + shadcn/ui 조합) citeturn2search2turn2search26  
5) **정적 게이트**: prettier(특히 Tailwind class sorting) + ESLint(Tailwind 규칙) citeturn2search13turn2search0turn2search1  
6) **시각/구조 게이트**: Playwright `toHaveScreenshot()` + `ariaSnapshot()` citeturn0search2turn3search3  
7) **비전/체크리스트 Judge**: Gemini headless(JSON) + CheckEval 스타일 합성 점수 citeturn0search9turn0search6turn1search9turn3search1  
8) **keep/discard + 재작업 지시 생성**: auto-research 패턴으로 점수 개선 때만 유지 citeturn1search2turn6view0turn3search0  

### hooks.json 예시: “수정 직후 강제”와 “규칙 자동 주입”

아래는 개념 예시이며, 실제로는 프로젝트의 패키지 매니저/스크립트 이름에 맞춰 조정합니다.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .harness/scripts/inject-design-context.mjs"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "pnpm prettier:write" },
          { "type": "command", "command": "pnpm lint" }
        ]
      }
    ]
  }
}
```

hooks 가이드가 제시하는 핵심은 matcher로 후처리 범위를 좁히고(PostToolUse에서 Edit/Write 후에만 실행), UserPromptSubmit에서 additionalContext 주입을 활용할 수 있다는 점입니다. citeturn0search0turn0search13

### 시각 회귀를 “스크린샷 파일 커밋” 대신 “검토 UI”로 운영하는 옵션

Playwright 자체로 스크린샷 비교는 가능하지만, 대규모/장기 운영에서는 “스크린샷을 레포에 커밋하고 관리”하는 방식이 부담이 될 수 있습니다. Argos는 Playwright/Cypress 테스트에서 생성된 스크린샷을 CI에서 처리하고, diff를 UI로 리뷰할 수 있도록 하는 “시각 테스트 운영 레이어”를 제공합니다(레포에 이미지를 커밋하지 않는 워크플로우를 문서로 제시). 이는 오너가 “픽셀 리뷰” 대신 “diff 승인/거절”로 개입할 수 있게 만들어, 운영 부담을 낮추는 방향의 선택지입니다. citeturn5search3turn5search27turn5search7