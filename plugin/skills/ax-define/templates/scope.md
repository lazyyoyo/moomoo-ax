<!--
scope.md 템플릿 — team-ax `define` 스킬의 최종 산출물.
저장 위치 (플러그인 v0.1): versions/undefined/scope.md
저장 위치 (플러그인 v0.2+): versions/vX.Y.Z/scope.md (Phase B 폴더 승격 후)

본 템플릿은 8개 섹션을 모두 채워야 한다. SLC 통과 + §리뷰 APPROVE까지가 define 완료 조건.
-->

# scope — {제품 이름} {제품 버전명 or undefined}

## § 버전 메타

<!-- Phase A 6단계에서 확정. 플러그인 v0.1은 폴더 승격·브랜치 생성을 하지 않는다. -->

- **제품 이름**: {예: rubato}
- **제품 버전명**: {예: v1.7.0 — 또는 'undefined' (Phase A 미완료 시)}
- **시맨틱 구분**: {MAJOR | MINOR | PATCH} — 근거: {한 줄}
- **사이클 브랜치**: (플러그인 v0.2부터) `cycle/X.Y.Z`
- **worktree 경로**: (플러그인 v0.2부터) `../{repo}-X.Y.Z`

## § JTBD

<!-- 한 줄. "And 없는 한 문장" 통과 필수. 한 제품 버전 = 하나의 JTBD. -->

> {예: 내 프로필과 설정을 한 곳에서 관리한다.}

## § Story Map

<!--
Story 2~N개 + 각 Story 아래 태스크 bullet (spec 링크 포함).
패치 모음 버전이면 "(패치 모음 — Story 없음)" 표기 + 태스크 목록만.
-->

### Story 1: {Story 이름}
- {태스크 1} (spec: {기능명}.md)
- {태스크 2} (spec: {기능명}.md)

### Story 2: {Story 이름}
- {태스크 1} (spec: {기능명}.md)

## § SLC 체크

<!-- 각 축 한 줄 근거. SLC 실패 시 §Story Map으로 되돌아가 재조정. -->

- **Simple**: {근거 한 줄 — 스코프가 최소한임을 보이는 수치/사실}
- **Lovable**: {근거 한 줄 — 사용자가 쾌적하게 쓸 디테일}
- **Complete**: {근거 한 줄 — 슬라이스만으로 JTBD 독립 충족}

## § 비범위

<!-- 의도적으로 제외한 항목 + 이유. 묻기 전에 답하는 가드레일. -->

- {제외 항목 1} — {이유 한 줄}
- {제외 항목 2} — {이유 한 줄}

## § 수정 계획

<!--
Phase C plan 산출물. analyst가 작성.
파일별 변경 타입(갱신/신규/삭제/마커) + 변경 요약 + 매핑 근거 + 대응 태스크.
-->

| # | 파일 | 변경 타입 | 변경 요약 | 매핑 근거 | 대응 태스크 |
|---|---|---|---|---|---|
| 1 | `docs/specs/profile.md` | 갱신 (마커 추가) | "프로필 카드" 시나리오 추가 | 기존 user.md(인증)와 도메인 분리. 신규 파일 정당화. | Story 1 |
| 2 | `docs/specs/theme.md` | 신규 | 테마 변경 시나리오 | 기존 specs/에 매칭 후보 0개 (전체 grep 확인) | Story 2 |
| 3 | `BACKLOG.md` | 갱신 | inbox에서 "마이페이지" 항목 제거 | — | (전체) |

## § 수정 로그

<!--
Phase C write 산출물. analyst가 작성.
§수정 계획 각 항목의 실행 여부 체크 + 실제 commit ref.
-->

- [ ] #1 `docs/specs/profile.md` 갱신 — commit: `{ref}`
- [ ] #2 `docs/specs/theme.md` 신규 — commit: `{ref}`
- [ ] #3 `BACKLOG.md` inbox 정리 — commit: `{ref}`

## § 리뷰

<!--
Phase C review 산출물. `$ax-review doc versions/undefined/scope.md` 호출 결과를 그대로 붙여넣음.
첫 줄 = APPROVE 또는 REQUEST_CHANGES: {이유}.
REQUEST_CHANGES면 §수정 계획으로 되돌아가 재작업.
-->

```
{ax-review doc 출력 — codex 위임 결과}
```
