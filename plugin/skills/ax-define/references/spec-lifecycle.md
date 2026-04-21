# Spec Lifecycle — in-place 갱신 + ⏳ planned 마커

`docs/specs/`는 **"오늘의 진실"만 담는 폴더**. 시간 축 누적 금지. 새 파일 남발 금지.

## 핵심 원칙

1. **in-place 갱신** — 기존 spec은 같은 파일을 덮어쓴다. "v1.5에서 추가" 같은 누적 본문 금지.
2. **`⏳ planned` 마커** — 변경 예정 부분은 마커로 표시 (현재 상태와 병기). 배포 완료 시 deploy 단계에서 마커만 제거.
3. **deprecated는 `git rm`** — 사용자에게 더는 노출되지 않는 기능은 spec 파일을 삭제한다. git history가 보존.
4. **시점 비교는 `git show`** — "v1.5 시점 spec"이 궁금하면 `git show v1.5:docs/specs/{기능}.md`. specs/ 안에 과거 스냅샷을 두지 않는다.

## `⏳ planned` 마커 형식

team-dev `backlog refine`의 마커 방식 차용. 두 가지 케이스:

### 기존 기능 변경 — 본문 아래에 마커 블록

```markdown
## 정렬

기존: 등록일 내림차순으로 정렬한다.

> ⏳ planned — 정렬 기준을 등록일 → 우선순위로 변경. (versions/undefined/scope.md §수정 계획 참조)
```

### 신규 추가 — 신규 섹션 전체를 마커로 감싸기

```markdown
> ⏳ planned — 필터 기능 추가 (태그/날짜 범위 지원). 본 섹션은 deploy 후 마커 제거 + 본문 본격화 예정.

## 필터

### 정상 흐름
- 사용자가 태그를 선택하면 해당 태그가 붙은 항목만 표시된다.
- 사용자가 날짜 범위를 지정하면 범위 내 항목만 표시된다.
```

> 마커는 한 줄 인용(`>`) 블록. 변경 요약 + scope.md 참조 링크를 한 줄로 압축. 마커 없는 본문 변경은 금지(리뷰에서 잡힌다).

## 강제 장치 4종 — 새 spec 파일 남발 차단

### 장치 1 — 기존 파일 매핑 탐색 의무화

새 요구사항을 받으면 `docs/specs/` **전체를 먼저 읽고** "어느 파일에 속하는가"를 제안한다. 매칭 후보가 0개일 때만 신규 생성 허용. analyst는 scope.md `§수정 계획`에 매핑 근거를 명시:

```markdown
- profile.md (갱신) — "프로필 카드" 추가. 기존 user.md에 흡수 가능했으나 user.md는 인증 도메인 → 분리 유지.
```

### 장치 2 — 파일명 규칙 (시점·변경 단위 접미사 금지)

`{기능명}.md` **만** 허용. 다음 접미사는 모두 금지:

| 금지 접미사 | 이유 | 대신 |
|---|---|---|
| `-fix` | 시점 단위 (어느 fix?) | 기존 파일 in-place 갱신 |
| `-patch` | 시점 단위 | 기존 파일 in-place 갱신 |
| `-enhance` | 변경 단위 (한 번 enhance하면 끝?) | 기존 파일 in-place 갱신 |
| `-redesign` | 시점 단위 | 기존 파일 in-place 갱신 (그래도 같은 기능) |
| `-v2` | 시점 단위 | 기존 파일 in-place 갱신 |
| `.old`, `.legacy` | 과거 스냅샷 | `git rm` + git history |

### 장치 3 — 시간 축 본문 금지

spec 본문에 다음 표현이 있으면 위반:

- "v1.5에서 추가됨"
- "기존엔 X였는데 v1.7부터 Y로 변경"
- "Phase 1: 기본 / Phase 2: 확장"
- 변경 이력 테이블 (`| v1.5 | ... | v1.7 | ... |`)

> 변경 이력은 `git log docs/specs/{기능}.md`로 본다. spec 본문은 "지금 이 순간의 진실"만.

### 장치 4 — spec vs CHANGELOG 판정 가드

| 케이스 | 행선지 |
|---|---|
| 새 기능, 새 기능의 시나리오 | `docs/specs/{기능}.md` |
| 기존 기능 동작 변경 | `docs/specs/{기능}.md` (in-place) |
| **버그 수정 / 핫픽스 / 패치** | `docs/specs/{기존-기능}.md` (시나리오에 영향 있을 때만) |
| 사용자 관점 릴리즈 노트 | `CHANGELOG.md` (deploy 단계에서 작성) |

> 버그 수정·핫픽스를 신규 spec 파일로 만들면 위반. 시나리오 변경이 없으면 spec을 건드리지 않고 CHANGELOG만 갱신(deploy).

## 파일명 규칙 4종 (요약)

1. `{기능명}.md` 형태만 허용.
2. 시점·변경 단위 접미사 금지: `-fix`, `-patch`, `-enhance`, `-redesign`, `-v2`, `.old`, `.legacy`.
3. 한 spec = 한 관심사 ("And 없는 한 문장" 통과).
4. Deprecated → `git rm` (`git rm docs/specs/{기능}.md`).

## spec 파일 증식의 원인 4가지

자주 관찰되는 안티패턴과 처방:

| 원인 | 흔적 | 처방 |
|---|---|---|
| 새 파일 남발 | `auth-fix.md`, `auth-redesign.md`, `auth-v2.md`가 동시에 존재 | 장치 1 (매핑 탐색) + 장치 2 (접미사 금지) |
| 시점 단위 접미사 | `book-add-patch.md`로 핫픽스 단발 파일 생성 | 장치 4 (CHANGELOG 분리) |
| 시간 축 본문 | spec에 `## v1.5 변경사항` 섹션 누적 | 장치 3 (시간 축 본문 금지) |
| spec vs changelog 혼동 | "v1.6.2 핫픽스" spec 파일이 release note처럼 작성됨 | 장치 4 (CHANGELOG는 deploy 단계) |

## 책임 분담

| 단계 | 주체 | 행위 |
|---|---|---|
| Phase C plan | `analyst` | 매핑 탐색 + scope.md `§수정 계획`에 변경 타입 기록 (갱신/신규/삭제/마커) |
| Phase C write | `analyst` | `docs/specs/` in-place 갱신 + `⏳ planned` 마커 부착 |
| Phase C review | `ax-review doc` | 4종 위반 검출 + APPROVE/REQUEST_CHANGES 판정 |
| deploy (후속 스프린트) | (미정) | `⏳ planned` 마커 제거 + CHANGELOG 작성 |

## 참고

- team-dev `skills/backlog/SKILL.md` — `⏳ planned` 마커 원형
- team-product `references/spec-writing-guide.md` — in-place 모델 원형
- 다음 단계: `docs-structure.md`
