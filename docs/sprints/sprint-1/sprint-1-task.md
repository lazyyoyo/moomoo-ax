# sprint-1 tasks

sprint-1-plan.md의 범위(팀-ax 플러그인 v0.1 — `ax-define` 스킬)를 구체 태스크로 분해.

> **실행 방식 주의** — team-ax 플러그인을 **만드는 중**이라 team-ax 자체 스킬·에이전트로 자기를 부트스트랩할 수 없다. 모든 태스크는 **직접 파일 작성/수정** 방식. 도그푸딩(실제 호출 검증)은 스프린트 비범위.

## 의존성 그래프

```
T0 (스캐폴드)
 ├─ T1.* (references 6개)              ──┐
 ├─ T2.* (ax-define templates)         ──┤
 ├─ T3.* (agents 2개)                  ──┤
 └─ TR.* (ax-review 스킬 + 설치스크립트) ──┼─→ T4 (ax-define SKILL.md) → T5 (self-review) → T6 (릴리즈)
                                         │
```

T1 / T2 / T3 / TR은 서로 독립. 순서 무관하게 병렬로 작성 가능.
TR.5(install-local-skills.sh)은 TR.1~TR.4 파일이 실제로 있어야 의미 있으므로 TR 내부 순서: TR.1~TR.4 → TR.5 → TR.6(AGENTS.md).
T4(SKILL.md)는 T1 / T2 / T3 / TR의 파일 경로를 참조해야 하므로 이들 완료 후.
T5(self-review)는 T4까지 끝난 상태에서 일관성 검증.
T6(릴리즈)는 T5 APPROVE 후.

---

## T0 — 스캐폴딩

**산출물**: 플러그인 디렉토리 구조.

- [x] T0.1 — `plugin/skills/ax-define/` 생성
- [x] T0.2 — `plugin/skills/ax-define/references/` 생성
- [x] T0.3 — `plugin/skills/ax-define/templates/` 생성
- [x] T0.4 — `plugin/skills/ax-review/` 생성
- [x] T0.5 — `plugin/skills/ax-review/references/` 생성
- [x] T0.6 — `plugin/agents/` 확인 (존재)
- [x] T0.7 — 빈 `SKILL.md` placeholder (ax-define + review 두 곳, T4·TR에서 채움)

**완료기준**: 위 폴더가 존재하고 구조가 맞음.

---

## T1 — references/ 문서 6개 작성

각 문서는 **스킬/에이전트가 참조하는 프레임워크 기준서**. 짧고 명확하게 (50~100줄 내외 권장).

- [x] **T1.1 — `references/jtbd.md`** (Jobs To Be Done 프레임워크)
  - 내용: JTBD 정의, 레벨 구분(JTBD / Story / Backlog), "한 버전 = 하나의 JTBD" 원칙, "And 없는 한 문장" 테스트
  - 참조 소스: team-product `product-define/references/jtbd-storymap-slc.md`, sprint-1-plan의 §JTBD 블록
  - 완료기준: "And 없는" 테스트 예시 O/X 포함

- [x] **T1.2 — `references/story-map.md`** (Story Map 그리드 작성법)
  - 내용: Activities × Stories 그리드, 수평 슬라이스 = 버전 스코프, 태스크 배치 규칙
  - 참조: team-product `jtbd-storymap-slc.md`
  - 완료기준: rubato 제품 v1.7.0 재구성 예시 포함

- [x] **T1.3 — `references/slc.md`** (Simple / Lovable / Complete)
  - 내용: 각 축의 정의, 체크 예시(통과/실패), 패치 모음 버전에서의 적용
  - 완료기준: SLC 실패 시 분리/축소 판단 기준 명시

- [x] **T1.4 — `references/semver.md`** (Semantic Versioning 판정 규칙)
  - 내용: semver 2.0 요약, major/minor/patch 판정 기준, 0.x 시리즈 규칙
  - 링크: https://semver.org/
  - 완료기준: "breaking change → major", "새 기능 → minor", "버그 수정 → patch" 판정 플로우 포함

- [x] **T1.5 — `references/spec-lifecycle.md`** (spec in-place 갱신 + 마커 + 파일명)
  - 내용: `⏳ planned` 마커 형식(기존 변경 / 신규 추가 둘 다 예시), in-place 원칙, 파일명 규칙 4종, deprecated는 `git rm`
  - 강제 장치 4종:
    1. 기존 파일 매핑 탐색 의무화
    2. 파일명 규칙 (시점·변경 단위 접미사 금지: `-fix` / `-patch` / `-enhance` / `-redesign` / `-v2`)
    3. 시간 축 본문 금지
    4. spec vs changelog 판정 가드
  - 참조 소스: team-dev `backlog/SKILL.md` (refine), team-product `spec-writing-guide.md`
  - 완료기준: rubato specs/ 증식 사례(원인 4가지) 요약 포함

- [x] **T1.6 — `references/docs-structure.md`** (BACKLOG / scope / CHANGELOG 3-문서)
  - 내용: 세 문서 책임 분리, 항목 생애 흐름 다이어그램, ROADMAP 제거 근거
  - 완료기준: CHANGELOG 포맷(Keep a Changelog)은 개념만 언급, 실제 작성은 deploy 단계임을 명시

> T1.7(codex-review reference)은 범용 `ax-review` 스킬로 이관되어 **TR 섹션**에서 다룬다.

---

## T2 — templates/ 작성

- [x] **T2.1 — `templates/scope.md`** (scope.md 템플릿)
  - 섹션: § 버전 메타 / § JTBD / § Story Map / § SLC 체크 / § 비범위 / § 수정 계획 / § 수정 로그 / § 리뷰
  - 각 섹션에 placeholder + 주석
  - 완료기준: sprint-1-plan의 rubato 제품 v1.7.0 예시가 이 템플릿을 따름

- [x] **T2.2 — (선택) Phase A 산출물 템플릿**
  - `templates/intake.md`, `interview.md`, `jtbd.md`, `story-map.md`, `slc.md`
  - 없어도 무방 — 에이전트가 free-form으로 작성 가능
  - 필요 판단은 T3 작성 후 결정

---

## T3 — agents/ 2개 작성

team-product `agents/po.md`, `analyst.md` 구조를 참조하되 team-ax 맥락으로 재작성. **reviewer 에이전트는 없음** — 리뷰는 별도 `ax-review` 스킬(TR)로 codex에 위임.

- [x] **T3.1 — `plugin/agents/product-owner.md`**
  - frontmatter: name, description, model(opus), tools(Read/Grep/Glob/AskUserQuestion/Write/Edit)
  - Role: Phase A 전체 (intake, interview, JTBD, Story Map, SLC, 제품 버전명 결정)
  - Constraints: 비자명한 질문만, "And 없는 한 문장" 테스트, SLC 통과 필수, 단계 스킵 금지
  - Investigation Protocol: 1~6단계 (sprint-1-plan Phase A)
  - Failure Modes: 가정 기반 진행, 범위 묶기, 오너 과부하, SLC 무시, major/minor 분기 습관
  - 참조: `references/jtbd.md`, `story-map.md`, `slc.md`, `semver.md`

- [x] **T3.2 — `plugin/agents/analyst.md`**
  - frontmatter: tools(Read/Grep/Glob/Write/Edit) — AskUserQuestion 제외
  - Role: Phase C plan + write (specs 매핑, scope.md §수정 계획 작성, specs in-place 갱신, BACKLOG inbox 정리, §수정 로그 기록)
  - Constraints: 기존 specs/ 전체 읽기 필수(매핑 탐색), 파일명 규칙 엄수, `⏳ planned` 마커 사용, 시간 축 본문 금지
  - Failure Modes: 새 파일 남발, 접미사 사용(`-fix`·`-v2` 등), 시간 축 기술, spec vs changelog 혼동
  - 참조: `references/spec-lifecycle.md`, `docs-structure.md`

> T3.3 (reviewer 에이전트)은 제거됨. 리뷰는 **TR 섹션의 범용 `ax-review` 스킬**이 담당 (codex 위임).

**공통 사항**
- 각 에이전트 파일 말미에 "Common Protocol" 섹션 (team-product 에이전트 포맷 참조) — Verification Before Completion + Tool Usage
- frontmatter `description`은 Claude Code가 에이전트 자동 매칭에 쓰므로 구체적으로 (team-product `po.md` 수준)

---

## TR — 범용 `ax-review` 스킬 (codex 위임)

team-ax의 모든 리뷰(문서·구현·PR)를 codex에 위임하는 범용 스킬. v0.1은 `doc` 타입만 구현하고 나머지는 인자 파싱 + "미구현" stub.

- [x] **TR.1 — `plugin/skills/ax-review/SKILL.md`** (스킬 본체 — Claude/Codex 공용 정본)
  - frontmatter:
    - `name: ax-review`
    - `description`: "범용 리뷰 스킬 (codex 위임) — doc/code/pr 타입. Use when: ax-review, 문서 리뷰, 구현 리뷰, PR 리뷰"
    - `argument-hint`: `<doc|code|pr> <target>`
  - 동작:
    - `$ARGUMENTS` 첫 단어로 타입 파싱 (`doc` / `code` / `pr`)
    - 타입별 체크리스트 경로 매핑:
      - `doc` → `references/doc-checklist.md` (v0.1 구현)
      - `code` → `references/code-checklist.md` (v0.1 stub)
      - `pr` → `references/pr-checklist.md` (v0.1 stub)
    - 리뷰 지침 구성: 대상 파일/번호 + 체크리스트 본문 로드 + 출력 포맷 요구
    - 실행: 스킬 본체는 **read-only로 분석만**. 쓰기 행위 금지 (codex 쪽 default sandbox = read-only와 일치).
  - 출력 포맷: 첫 줄 `APPROVE` 또는 `REQUEST_CHANGES: {이유}`, 이후 줄에 항목별 근거 본문
  - 호출자 쪽에서 stdout을 받아 `§리뷰` 섹션에 기록
  - 완료기준: Codex에서 `$ax-review doc versions/undefined/scope.md` 실행 시 판정 결과 한 줄 + 근거가 돌아옴.

- [x] **TR.2 — `plugin/skills/ax-review/references/doc-checklist.md`** (v0.1 구현 타입)
  - 대상: 문서 수정이 의도대로 됐는지 검증 (scope.md + 관련 문서들)
  - 체크리스트 5종:
    1. §수정 계획의 각 항목이 실제 파일에 반영됐는가?
    2. 새 파일 생성 시 "기존 파일 매핑 탐색" 근거가 있는가?
    3. 파일명이 `-fix` / `-patch` / `-enhance` / `-redesign` / `-v2` 접미사를 포함하지 않는가?
    4. spec 본문에 시간 축 기술(예: "v1.5에서 추가")이 없는가?
    5. 버그 수정·핫픽스가 신규 파일이 아닌 기존 spec 갱신으로 처리됐는가?
  - 대조 근거: scope.md §수정 계획 vs `git diff HEAD`
  - 출력 포맷 명시

- [x] **TR.3 — `plugin/skills/ax-review/references/code-checklist.md`** (v0.1 stub)
  - 한 줄 문서: "구현 리뷰 체크리스트. 후속 스프린트(ax-build 도입 시)에서 작성."
  - SKILL.md가 이 타입 호출 시 "미구현" 안내 후 중단.

- [x] **TR.4 — `plugin/skills/ax-review/references/pr-checklist.md`** (v0.1 stub)
  - 한 줄 문서: "PR 리뷰 체크리스트. 후속 스프린트(ax-deploy 도입 시)에서 작성."
  - SKILL.md가 이 타입 호출 시 "미구현" 안내 후 중단.

- [x] **TR.5 — `plugin/scripts/install-local-skills.sh`** (codex·claude 스킬 동기화)
  - 참조 원본: `/Users/sunha/hq/projects/KESE-KIT/scripts/install-local-skills.sh`
  - 동작:
    1. `plugin/skills/ax-review/` → rsync → `~/.codex/skills/ax-review/` (Codex가 `$ax-review`로 발견)
    2. `plugin/skills/ax-review/` → rsync → `~/.claude/plugins/cache/lazyyoyo/team-ax/_latest_/skills/ax-review/` (Claude 플러그인 캐시 갱신, 캐시 존재 시에만)
  - rsync 플래그: `-a --delete --exclude '.DS_Store'`
  - 실행 안내 문서: `AGENTS.md` 또는 README에 "스킬 갱신 후 `bash plugin/scripts/install-local-skills.sh` 실행" 문구
  - 완료기준: 스크립트 실행 후 `ls ~/.codex/skills/ax-review/` 에 SKILL.md + references/ 확인

- [x] **TR.6 — `AGENTS.md` 신설 (루트)**
  - KESE-KIT의 `AGENTS.md` 패턴 차용. 내용:
    - 활성 스킬 이름 (`ax-define`, `ax-review`)
    - 설치 스크립트 경로 + 실행법
    - Codex 호출 규약 (`$ax-review doc ...`)
    - Claude 호출 규약 (`/team-ax:ax-review ...` — 설치된 플러그인 기준)
    - Claude → Codex 위임 예시 (`codex exec '$ax-review ...'`)
  - 완료기준: AGENTS.md만 읽어도 스킬 호출 3가지 방식이 명확

---

## T4 — `plugin/skills/ax-define/SKILL.md` 작성

**이 스프린트의 핵심 산출물.** 위 references/agents/templates를 엮는 conductor.

- [x] **T4.1 — frontmatter**
  - `name: ax-define`
  - `description`: "team-ax define — 제품 버전 스코프 결정 + 스펙 in-place 갱신 + plan/write/review 검증. Use when: /ax-define, 제품 define, 버전 스코프"
  - `argument-hint`: (v0.1은 인자 없음. 추후 확장 여지만)

- [x] **T4.2 — Phase 순서 제어**
  - Phase A (1~6) → Phase C (9~11). Phase B 건너뜀(v0.2 예정)을 명시.
  - 각 단계에서 호출할 주체:
    - Phase A 전체 = `product-owner` (Claude 서브에이전트)
    - Phase C plan/write = `analyst` (Claude 서브에이전트)
    - Phase C review = **`$ax-review doc versions/undefined/scope.md` 호출** (범용 review 스킬, codex 위임)
  - 산출물 저장 위치: 모두 `versions/undefined/`

- [x] **T4.3 — 입력/출력 명세**
  - 입력: `BACKLOG.md` inbox / 기존 `docs/specs/` / 오너 인터뷰
  - 출력: `versions/undefined/` 하위 Phase A 산출물 + scope.md / `docs/specs/` in-place 갱신 / `BACKLOG.md` inbox 정리

- [x] **T4.4 — Phase C 루프 재진입 규칙**
  - `$ax-review doc` 판정이 `REQUEST_CHANGES`면 §수정 계획으로 되돌아가 `analyst` 재실행.
  - `APPROVE`일 때만 완료 처리.
  - 리뷰 결과(stdout) 전체를 scope.md `§리뷰` 섹션에 기록.

- [x] **T4.5 — 가드레일**
  - 제품 버전명 선결정 금지 (Phase A 끝에서만 결정)
  - major/minor 분기 금지 (단일 흐름)
  - JTBD/Story Map/SLC 단계 생략 금지
  - 새 spec 파일 생성 전 "기존 파일 매핑 탐색" 선행 필수

- [x] **T4.6 — 참조 섹션**
  - `references/*.md` 6개 파일 경로 + 한 줄 설명

**완료기준**: SKILL.md가 자체로 완결된 실행 지침. Phase A → Phase C 순서대로 읽어나가면 "어느 에이전트가 어느 파일에 무엇을 쓰는지"가 명확.

---

## T5 — Self-review (일관성 검증)

팀-ax 플러그인 외부에 의존하지 않는 내부 검증. 사람(오너 + Claude 메인세션)이 체크.

- [x] **T5.1 — 용어 일관성**: "제품 버전" vs "플러그인 버전" 구분이 모든 문서에서 흐트러지지 않는지
- [x] **T5.2 — 경로 교차검증**: ax-define SKILL.md와 review SKILL.md가 참조하는 `references/*.md` / `templates/*.md` / `agents/*.md` 경로가 실제 파일과 일치
- [x] **T5.3 — Phase B 부재 일관성**: 모든 산출물 저장 위치가 `versions/undefined/`임. `versions/vX.Y.Z/` / `cycle/X.Y.Z` / worktree 언급은 "v0.2 예정" 주석 있을 때만
- [x] **T5.4 — 책임 경계**: plan/write는 analyst 전담, review는 `$ax-review doc` 스킬 전담(codex 위임). analyst에 쓰기 권한, review 스킬은 codex 호출만.
- [x] **T5.5 — 강제 장치 4종 체크**: `review/references/doc-checklist.md`에 4종이 모두 들어가 있음
- [x] **T5.6 — ax-review 스킬 타입 stub**: `code` / `pr` 타입이 호출 시 "미구현" 안내 후 중단 동작 (인자 파싱은 정상)
- [x] **T5.7 — 설치 스크립트 검증**: `install-local-skills.sh` 실행 시 `~/.codex/skills/ax-review/` + Claude 캐시 경로 갱신 확인. `ls` 결과 SKILL.md + references/ 존재.
- [x] **T5.8 — sprint-1-plan과의 부합**: plan 문서의 "범위 / 비범위 / 성공 기준"이 실제 구현에 반영됨

**완료기준**: 8개 항목 모두 PASS. 미비 시 T4/TR/T3/T1으로 되돌아가 수정.

---

## T6 — 플러그인 릴리즈 (v0.1.0)

- [x] **T6.1 — 버전 동기화 확인**
  - `plugin/.claude-plugin/plugin.json` version = `0.1.0`
  - `.claude-plugin/marketplace.json` version = `0.1.0`
  - (둘 다 현재 0.1.0 확인됨)
- [x] **T6.2 — 커밋**
  - 메시지: `sprint-1: team-ax v0.1.0 — ax-define(Phase A+C) + ax-review(codex 위임) 구현`
  - 포함 파일:
    - `plugin/skills/ax-define/**`
    - `plugin/skills/ax-review/**`
    - `plugin/agents/product-owner.md` + `analyst.md`
    - `plugin/scripts/install-local-skills.sh`
    - `AGENTS.md`

- [x] **T6.2.5 — 스킬 설치 실행** (배포 전 검증)
  - `bash plugin/scripts/install-local-skills.sh`
  - `ls ~/.codex/skills/ax-review/SKILL.md` 확인
  - Codex에서 `$ax-review doc <sample>` 한 번 호출해 동작 확인
- [x] **T6.3 — PR 생성 + 머지**
  - main 브랜치에 머지 (--no-ff)
  - 이전에 별도 브랜치 분기해서 작업했다면 해당 브랜치 머지, 아니면 main 직접 작업 후 push
- [x] **T6.4 — 태그 생성**
  - `git tag v0.1.0 -m "team-ax 플러그인 v0.1.0"`
  - `git push origin v0.1.0`
- [x] **T6.5 — GitHub Release 생성** (선택)
  - `gh release create v0.1.0 --title "team-ax v0.1.0" --notes "ax-define 스킬(Phase A+C) + 범용 review 스킬(doc 타입) 구현. Phase B 부트스트랩은 v0.2 예정, code/pr 리뷰 타입은 후속 스프린트."`

**완료기준**: `git tag -l | grep v0.1.0` 출력 + GitHub에 태그 push 완료.

---

## 이번 스프린트에서 하지 않는 것 (리마인더)

- 도그푸딩 (rubato/rofan-world 등에 실제 `/ax-define` 호출) — 비범위
- Phase B 부트스트랩 (폴더 승격 / `cycle/X.Y.Z` / worktree) — 플러그인 v0.2
- 분리 감지 / 복수 제품 버전 / 의존성 분석 — 플러그인 v0.2
- 병렬 실행 / Story worktree — 플러그인 v0.3+
- Hook 기반 자동 강제 (T1.5의 4종 장치는 **에이전트 규칙**으로만 구현. 하드 훅은 이번 범위 밖)
- design / implement / qa / deploy 스킬 구현

---

## 상태

- [x] T0 완료 (스캐폴딩 — ax-define + review 양쪽)
- [x] T1 완료 (references 6개)
- [x] T2 완료 (ax-define templates)
- [x] T3 완료 (에이전트 2개: product-owner, analyst)
- [x] TR 완료 (ax-review 스킬 본체 + doc-checklist + code/pr stub + install-local-skills.sh + AGENTS.md)
- [x] T4 완료 (ax-define SKILL.md)
- [x] T5 PASS (7개 self-review 항목)
- [x] T6 릴리즈 (v0.1.0 태그)
