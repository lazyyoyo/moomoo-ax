# Paperwork Report — 2026-04-21 (v0.8.2 릴리즈 직후 2차)

## 요약

- v0.8.2에서 워커 모델을 pane→백그라운드로 뒤집으면서 다른 스킬에 pane 모델 잔재 남음
- skill-creator 정적 audit 병행: 사고 기록/외부 제품 이름/구현 상태 시간축 등 PROJECT_BRIEF §6 원칙 위반 발견
- 두 카테고리 묶어 v0.8.3 hotfix로 처리

**수정: 20건. 전부 문서/템플릿, 코드 변경 0.**

## A. 카테고리별 수정

### A-1. pane→백그라운드 잔재 (9건)
- `ax-help/SKILL.md` L55/67/72/92 — 상태 감지 로직을 `.ax/workers/*/pid` 프로세스 기반으로
- `ax-deploy/SKILL.md` L90 — "워커 pane" → "워커 프로세스"
- `ax-paperwork/SKILL.md` L123, `ax-clean/SKILL.md` L116 — 동일 패턴
- `paperwork-checklist.md` L63, `clean-checklist.md` L88 — 동일 패턴
- `ax-build/templates/build-plan.md` L46 — "tmux pane 폭 제약" → "병렬 효율 저하"
- `ax-execute/SKILL.md` L111 — "NEVER run tmux orchestration" → "NEVER 오케스트레이션 환경 조작"
- `README.md` L29 — "tmux 안에서 claude 기동 + pane split" 전제 제거

### A-2. 사고 기록 제거 (6건 / 규칙은 유지)
- `ax-execute/SKILL.md` L117 — 영역 침범 가드 도입부의 "rubato admin-v0.2.0 도그푸딩" 사고 서술 제거
- `product-owner.md` L26-28 — "v0.1.0 dogfooding 사고 기록 — yoyowiki…" 단락 제거
- `executor.md` L30 — "(rubato admin 도그푸딩 피드백)" 괄호 삭제
- `ax-define/SKILL.md` L8, L14 — "rubato, rofan-world" / "예: rubato v1.7.0" 제품명 제거
- `spec-lifecycle.md` L92 — 섹션 제목 "rubato specs/ 증식 사례" → "spec 파일 증식의 원인 4가지"

### A-3. references 학습 예시 외부 제품 이름 제거 (N건)
- `jtbd.md` / `slc.md` (2건) / `story-map.md` / `semver.md` (2건) / `docs-structure.md` / `templates/scope.md` / `product-owner.md` / `ax-define/SKILL.md` (참조 설명)

### A-4. 시간축 주석 제거 (4건)
- `ax-define/SKILL.md` L54/L179/L180/L184 — "v0.1.1 변경/신설" 제거
- `product-owner.md` L20/L65 — "(v0.1.1부터/변경)" 제거
- `ax-review/SKILL.md` L59/L72/L111/L112 — "v0.4 구현 / v0.1 stub" → "stub"만
- `ax-review/references/pr-checklist.md` L1 — 제목에서 "v0.1 stub" → "stub"

### A-5. scripts resolve 패턴 통일 부분 적용 (1건)
- `ax-deploy/SKILL.md` — cleanup 단계에 `$ORCH` resolve 참조 명시

## B. 상태 문서 갱신 (릴리즈 외)

- `HANDOFF.md` — v0.8.3 진행 상태로 재작성
- `BACKLOG.md` — v0.8.1/v0.8.2/v0.8.3 hotfix done 이관 + v0.8.4+ 후보 inbox 이관 (B-SCRIPTS-RESOLVE / B-DESIGN-GATE-CODIFY / B-AXHELP-DEPRECATED) + 사소한 일관성 항목 3건
- `paperwork-report.md` 갱신 (이 파일)

## C. v0.8.4+ 이관 (BACKLOG inbox)

- **B-SCRIPTS-RESOLVE** — plugin/scripts 경로 systematic resolve (ax-build만 `$ORCH` 패턴, 나머지 스킬 8개 미적용). wrapper 인프라 or 각 SKILL.md 개별 resolve 추가
- **B-DESIGN-GATE-CODIFY** — ax-design 게이트 자동 재작업 로직이 SKILL.md에 자연어로. `design-gate.sh` 결정론 강화 (progressive codification)
- **B-AXHELP-DEPRECATED** — ax-help 보조 스킬 목록에서 deprecated executor 에이전트 제외

## D. 참조 무결성 / 중복 / 깨진 링크

없음 (이번 audit에서는).

## 절차

- 브랜치 `hotfix/v0.8.3` (커밋 대기)
- 버전 bump: 0.8.2 → 0.8.3
- CHANGELOG v0.8.3 섹션 작성 완료
- PR 생성 후 오너 승인까지 머지 대기
