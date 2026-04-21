# Story Map

JTBD를 기능 단위로 펼치는 그리드. **"이번 제품 버전 = 어느 슬라이스인가"를 결정**한다.

## 그리드 구조

```
JTBD: {한 문장}

Activities (가로):   {큰 흐름 1}    {큰 흐름 2}    {큰 흐름 3}
                       │              │              │
Stories (세로):      Story A1       Story B1       Story C1   ← 우선순위 ↑
                     Story A2       Story B2       Story C2
                     Story A3       Story B3       Story C3   ← 우선순위 ↓
```

- **Activity** — JTBD를 충족하는 큰 흐름. 보통 2~4개. 사용자가 시간 순서로 거치는 단계.
- **Story** — Activity 안의 기능 단위. "And 없는 한 문장"으로 표현. 위쪽이 우선순위 높음.
- **수평 슬라이스** — 각 Activity의 N번째 Story를 모아 하나의 제품 버전 스코프로 묶는다.

## 작성 규칙

1. **JTBD 먼저, Story Map 다음** — JTBD 한 줄이 확정되어야 Activity가 구분된다.
2. **Activity는 사용자 시간 순서로** — "탐색 → 추가 → 관리" 같은 순행 흐름. 기술 레이어로 자르지 않는다.
3. **각 Story는 spec과 1:1** — Story 이름이 결국 `docs/specs/{기능명}.md`의 스코프와 매칭되어야 한다.
4. **태스크는 Story 아래** — Story 한 칸 안에 구현 태스크 N개. scope.md `§Story Map`에서는 Story 이름 + 태스크 bullet으로 표기.
5. **수평 슬라이스가 곧 제품 버전** — 슬라이스를 빼지 말고, 슬라이스 자체를 작게 잡는다. (Simple 축)

## 패치 모음 버전 예외

"앱 안정성 회복" 같은 패치 모음 제품 버전은 **Story 없이 태스크 목록만** 둘 수 있다. JTBD 한 줄이 추상 단어 하나로 묶이는 경우다. scope.md `§Story Map`에는 `(패치 모음 — Story 없음)` 표기 + 태스크 bullet 목록.

## 예시 — rubato 제품 v1.7.0 재구성

원본 BACKLOG에는 "마이페이지 만들기"가 한 줄로 있었다. Story Map으로 분해하면:

```
JTBD: 내 프로필과 설정을 한 곳에서 관리한다.

Activities:        프로필 보기      설정 변경
                       │               │
Stories:           프로필 카드      테마 변경
                                   비밀번호 변경
                                   (계정 삭제 — 비범위)
```

scope.md `§Story Map` 표기:

```markdown
## Story Map

### Story 1: 프로필 보기
- 프로필 카드 컴포넌트 (spec: profile.md)
- profiles 테이블 + 트리거 (spec: profile.md)
- GET /api/profile (spec: profile.md)

### Story 2: 테마 변경
- 테마 모달 + DB 저장 (spec: theme.md)
- PATCH /api/profile/theme (spec: theme.md)

### Story 3: 비밀번호 변경
- 비밀번호 모달 + 인라인 검증 + 성공 화면 (spec: auth.md)
```

> Story 단위는 build 단계에서 planner가 **파일 집합 단위로 재분할**하는 입력이 된다 (ax-build v0.8 — worktree가 아니라 파일 whitelist 기반 격리). scope 단계의 책임은 scope.md 안의 Story 그룹핑까지.

## 참고

- 이전 단계: `jtbd.md`
- 다음 단계: `slc.md`
