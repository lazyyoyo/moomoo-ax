# code 리뷰 체크리스트 (v0.4)

대상: 구현 코드가 spec/DS/보안 기준에 맞는지 검증.

## 체크리스트 7종

### 1. spec 정합성

변경된 코드가 `docs/specs/` 시나리오와 일치하는가?
- 각 spec 시나리오가 코드에 구현되었는가?
- spec에 없는 기능이 추가되지 않았는가?

> 1건이라도 불일치 → **FAIL**.

### 2. DS 토큰 준수

하드코딩된 색상/간격/폰트가 없는가?
- `#hex`, `rgb()`, `hsl()` 직접 사용 금지
- arbitrary value (`[16px]`, `[#ff0000]`) 금지
- DS 토큰(CSS 변수/Tailwind 클래스)만 사용

> 1건이라도 발견 → **FAIL**.

### 3. silent failure 검출

에러를 삼키는 코드가 없는가?
- 빈 catch 블록
- 에러 무시 (`catch (e) {}`)
- 로깅 없는 에러 처리
- Promise 미처리 (`.catch` 없는 async)

> 1건이라도 발견 → **FAIL**.

### 4. 보안

하드코딩된 키/토큰/시크릿이 없는가?
- API 키, 시크릿, 쿠키값이 코드에 직접 존재
- 민감정보 로그 출력 (`console.log(password)` 등)
- `.env` 파일 직접 읽기 (`fs.readFile('.env')`)

> 1건이라도 발견 → **FAIL**.

### 5. 텍스트 하드코딩

UI 텍스트가 i18n/copy 시스템을 경유하는가?
- JSX/TSX 내 한글/영문 문자열 직접 사용
- 에러 메시지, 버튼 라벨, 안내 문구 등

> 프로젝트에 i18n 시스템이 있으면 검사. 없으면 PASS.

### 6. 상태 처리

모든 데이터 페칭 화면에 상태 변형이 구현됐는가?
- loading 상태 (skeleton/spinner)
- error 상태 (재시도 UI)
- empty 상태 (빈 데이터 안내)

> 데이터 페칭 화면에서 1종이라도 누락 → **FAIL**.

### 7. 반복 패턴

동일한 토큰/컴포넌트/로직이 3회 이상 반복되는가?
- 같은 스타일 조합 3회 → 컴포넌트 추출 권장
- 같은 API 호출 패턴 3회 → 훅/유틸 추출 권장

> 3회 이상 → **오너 보고** (FAIL은 아님, 정보 제공).

## 출력 포맷

```
{APPROVE | REQUEST_CHANGES: {한 줄 이유}}

## 항목별 근거
1. spec 정합: PASS/FAIL — {근거}
2. DS 토큰: PASS/FAIL — {근거}
3. silent failure: PASS/FAIL — {근거}
4. 보안: PASS/FAIL — {근거}
5. 텍스트 하드코딩: PASS/FAIL — {근거}
6. 상태 처리: PASS/FAIL — {근거}
7. 반복 패턴: INFO — {발견 내용 또는 없음}

## 재작업 노트 (REQUEST_CHANGES일 때만)
- {수정 지침 1}
- {수정 지침 2}
```

## 판정 규칙

- 1~6 모두 PASS → `APPROVE`
- 1~6 중 1개라도 FAIL → `REQUEST_CHANGES: {가장 심각한 항목}`
- 7은 판정에 영향 없음 (정보 제공)
