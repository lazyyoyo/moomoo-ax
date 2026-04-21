# Semantic Versioning — 제품 버전명 판정 규칙

기준: [Semantic Versioning 2.0](https://semver.org/). team-ax는 모든 제품 버전을 `MAJOR.MINOR.PATCH` 3자리로 표기한다.

> **본 문서는 "제품 버전"에 적용된다.** team-ax 플러그인 자체 버전(`v0.1` 등)과 혼동하지 말 것 — 플러그인 버전은 sprint 산출물 기준으로 별도 관리.

## 한 줄 요약

| 자리 | 올리는 시점 | 키워드 |
|---|---|---|
| **MAJOR** | 호환성을 깨는 변경 | breaking change, API removal, schema migration without backward path |
| **MINOR** | 새 기능 추가 (호환 유지) | new feature, additive API, additive schema |
| **PATCH** | 버그 수정 / 내부 개선 (호환 유지) | bug fix, perf, refactor, copy 변경 |

> 0.x 시리즈는 "공개 안정 보장 전" 상태로 간주 — 0.MINOR.PATCH 자리에서 breaking change가 일어나도 MAJOR(`1.0.0`)로 올리지 않을 수 있다. 단, 본 프로젝트는 외부 사용자가 있는 제품(rubato, rofan-world)이므로 0.x여도 가급적 정식 규칙을 따른다.

## 판정 플로우

```
이 제품 버전의 변경사항을 한 줄씩 검토 →
  ├─ 호환성을 깬 항목이 1개라도 있는가?
  │     └─ Yes → MAJOR 올림
  │     └─ No  → 아래로
  ├─ 새 기능 추가가 1개라도 있는가?
  │     └─ Yes → MINOR 올림 (PATCH는 0으로 리셋)
  │     └─ No  → 아래로
  └─ 버그 수정·내부 개선만 있는가?
        └─ Yes → PATCH 올림
```

> "And 없는 한 문장" JTBD 안에서 자릿수가 갈리는 게 정상. 새 기능 + 버그 수정이 한 버전에 묶이면 MINOR가 우선한다 (변경 폭이 큰 쪽).

## 케이스 표

| 변경 내용 | 판정 |
|---|---|
| `/api/books` 응답 필드 제거 | MAJOR (응답 스키마 깨짐) |
| `/api/books`에 `cover_url` 필드 추가 | MINOR (additive) |
| `books.title` NULL 허용 → NOT NULL (마이그레이션 필요) | MAJOR (DB 호환 깨짐) |
| `books` 테이블에 `read_count` 컬럼 신규 | MINOR |
| 로그인 화면 카피 수정 | PATCH |
| 정렬 알고리즘 내부 변경 (사용자 영향 없음) | PATCH |
| 로그인 모달에 소셜 로그인 버튼 추가 | MINOR |
| 마이페이지 신규 도입 (rubato v1.7.0) | MINOR |
| package.json 의존성 보안 패치만 | PATCH |
| 환경 변수 이름 변경 (배포 문서 갱신 필요) | MAJOR (배포자 입장 호환 깨짐) |

## team-ax에서의 결정 시점

1. Phase A 6단계 — `product-owner`가 SLC 통과한 슬라이스에 대해 **위 플로우로 판정**.
2. 오너에게 한 줄로 보고 (`v1.7.0 (MINOR — 마이페이지 신규)`).
3. 오너 승인 후 scope.md `§ 버전 메타`에 기록.
4. Phase B에서 `versions/vX.Y.Z/` 폴더 승격 + `version/vX.Y.Z` 브랜치 + Story별 worktree 자동 생성.

**minor vs patch 흐름 분기:**

| 구분 | 흐름 |
|---|---|
| **minor** | Phase A → B(worktree) → C → Story별 병렬 개발 → version branch 머지 → QA → 배포 |
| **patch** | main에서 hotfix 브랜치 → 수정 → 즉시 배포 (Phase A~C 경량 실행 또는 생략) |

## 가드레일

- **버전명 선결정 금지** — Phase A 6단계가 끝나기 전에 "이번 v1.8.0 작업할 거야"라고 확정하지 않는다. 범위가 자릿수를 결정한다.
- **major/minor 분기 동작 금지** — team-ax는 단일 흐름. 자릿수가 무엇이든 JTBD/Story Map/SLC는 항상 수행한다.
- **0.x ↔ 1.x 전환** — 첫 안정판 출시 시 별도 합의. 자동 판정 대상이 아님.

## 참고

- 외부 표준: https://semver.org/
- 이전 단계: `slc.md`
- 다음 단계: `spec-lifecycle.md`
