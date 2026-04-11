# SPEC: @ 자연어 날짜 입력 파서

## 목적

입력 텍스트에서 `@내일`, `@금요일`, `@4/5` 같은 날짜 태그를 파싱해
날짜 객체로 변환하고 원문에서 태그를 제거한 cleanText 를 돌려준다.

## 구현 대상 파일

`dev/src/lib/parse-date-tag.ts` (신규 생성, TypeScript)

## 공개 API

```typescript
export interface DateTagResult {
  cleanText: string;      // @태그 제거 후 양쪽/중복 공백 정리된 본문
  date: Date | null;      // 파싱된 날짜. 매칭/유효성 실패 시 null
  label: string | null;   // 표시용 라벨 "M/D (요일)" — 예: "4/3 (금)"
  matchedRaw: string | null; // 매칭된 원본 토큰 — 예: "@내일"
}

export function parseDateTag(text: string, baseDate: Date): DateTagResult;
```

- `baseDate` 기준으로 상대 날짜/요일을 계산한다 (테스트 용이성).
- 매칭 없음 / 유효성 실패 시 `{cleanText: text, date: null, label: null, matchedRaw: null}`.

## 지원하는 날짜 패턴

### 1. 상대 날짜
- `@내일` → baseDate + 1일
- `@모레` → baseDate + 2일
- `@글피` → baseDate + 3일

### 2. 요일 (이번 주, 오늘 이후 가장 가까운)
- `@월요일` ~ `@일요일`
- 규칙: 오늘 이후 가장 가까운 해당 요일.
  - 오늘이 목요일인데 `@금요일` → 내일
  - 오늘이 목요일인데 `@월요일` → 다음 주 월요일
  - 오늘이 목요일인데 `@목요일` → **다음 주 목요일** (오늘이면 +7)

### 3. 다음 주 요일
- `@다음주월요일` ~ `@다음주일요일`
- baseDate 가 속한 주의 다음 주 월요일을 기준으로 오프셋 계산.

### 4. 숫자 날짜
- `@4/5` 또는 `@4월5일` → 해당 월/일
- 유효하지 않은 날짜 (예: `@2/30`) → `date: null`
- 이미 지난 날짜 → **내년**으로 해석
  - 예: baseDate 가 4월인데 `@1/1` → 내년 1월 1일

## 완료 기준

1. `@내일` 입력 시 baseDate + 1일로 파싱된다.
2. `@금요일` 등 요일 패턴이 '오늘 이후 가장 가까운' 규칙으로 파싱된다 (오늘이면 +7).
3. `@다음주월요일` 등 다음주 요일 패턴이 올바른 날짜로 파싱된다.
4. `@4/5`, `@4월5일` 숫자 패턴이 해당 월/일로 파싱되며 이미 지났으면 내년.
5. 유효하지 않은 날짜 (@2/30) 는 `date: null` 로 처리된다.
6. 매칭되지 않는 패턴 (@가나다) 은 `date: null`, `cleanText: 원본` 으로 반환한다.
7. `cleanText` 는 @태그 제거 후 양쪽/중복 공백이 정리된 상태여야 한다.

## 예시 입출력 (baseDate: 2026-04-02 목요일)

```typescript
parseDateTag("회의 준비 @내일", BASE)
// { cleanText: "회의 준비", date: 4/3, label: "4/3 (금)", matchedRaw: "@내일" }

parseDateTag("@모레 장보기", BASE)
// { cleanText: "장보기", date: 4/4, ... }

parseDateTag("점심 @목요일", BASE)
// date: 4/9 (오늘이 목요일 → 다음 주)

parseDateTag("미팅 @다음주월요일", BASE)
// date: 4/6

parseDateTag("약속 @4/5", BASE)
// date: 2026/4/5, label: "4/5 (일)"

parseDateTag("생일 @1/1", BASE)
// date: 2027/1/1  (이미 지나서 내년)

parseDateTag("테스트 @2/30", BASE)
// date: null  (유효하지 않음)

parseDateTag("테스트 @가나다", BASE)
// date: null, cleanText: "테스트 @가나다"  (매칭 없음, 원본 유지)

parseDateTag("  보고서 제출  @내일  ", BASE)
// cleanText: "보고서 제출"  (양쪽/중복 공백 정리)
```

## 참고 (base/ 디렉토리)

- `parse-hashtag.ts` — 같은 프로젝트의 `#프로젝트명` 파서. 동일한 스타일 / 구조를 따를 것
  - 단순 정규식 매칭 → cleanText + 파싱 결과 반환
- `date-utils.ts` — 요일 이름 배열 (`["일","월","화","수","목","금","토"]`) 과 `formatDate` 등 기존 유틸

## 비범위

- 입력 컴포넌트 (`QuickInput`) 수정 X — 파서만 만든다
- 테스트 파일 생성 X — 이 fixture 는 구현 단일 파일만 평가한다
- `@ 2/5` (공백 포함) 지원 X
