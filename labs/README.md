# labs/

**levelup loop의 실험장.** team-ax 플러그인의 각 스킬을 만들고 개선하는 곳.

## 구조

```
labs/
├── ax-init/      # team-ax/ax-init 스킬 개선
├── ax-define/    # team-ax/ax-define 스킬 개선
├── ax-design/    # team-ax/ax-design 스킬 개선
├── ax-implement/ # team-ax/ax-implement 스킬 개선
├── ax-qa/        # team-ax/ax-qa 스킬 개선
├── ax-deploy/    # team-ax/ax-deploy 스킬 개선
└── .archive/     # 구 5-stage 실험 (seed/jtbd/problem/scope/prd-gen)
```

각 stage 폴더는 다음 구조:

```
labs/{stage}/
├── program.md    # 오너 규칙 (불변)
├── script.py     # AI가 개선하는 생성 스크립트
├── rubric.yml    # 평가 기준 — "오너 기대치" 평가 항목 포함
├── input/        # 실험 입력
├── best/         # 최고 점수 스냅샷 (→ plugin/으로 승격)
└── logs/         # iteration 로그
```

## levelup loop 흐름

1. **개선 대상 식별** — meta loop 지시 또는 rubric 점수 낮은 plugin
2. **타겟 지정** — script.py / prompt / rubric 중 무엇을 건드릴지
3. **iteration** — `python src/loop.py ax-{stage}` 로 돌리기
4. **평가** — rubric 기반 LLM Judge → 점수
5. **갱신** — 점수 올랐으면 best 갱신, 아니면 discard
6. **빌드** — `plugin.json` 버전 bump → `plugin/skills/ax-{stage}/`에 복사
7. **배포** — 커밋 → marketplace 재설치

## 원칙

- **rubric은 루프 안에서 불변**. 변경은 meta loop 판단으로 버전 단위에서만.
- **levelup loop 엔진(`src/loop.py`)은 범용**. 대상별 차이는 `program.md + rubric.yml`로 표현.
- **6 stage는 product loop 전용 단위**이지만, levelup loop는 이 단위를 **대상으로** 삼아 각각 개선한다.
