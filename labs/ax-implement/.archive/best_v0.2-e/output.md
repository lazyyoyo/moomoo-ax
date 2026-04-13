# Implementation: haru:7475bef

## Summary
- verdict: ready
- `@` 자연어 날짜 파서 구현: 상대/요일/다음주요일/숫자 4개 패턴 + cleanText 정리
- 생성 파일: `dev/src/lib/parse-date-tag.ts`

## Files

### dev/src/lib/parse-date-tag.ts
```typescript
/**
 * 텍스트에서 @날짜 태그를 파싱하여 분리
 * 예: "회의 준비 @내일" → { cleanText: "회의 준비", date: <tomorrow>, label: "4/3 (금)", matchedRaw: "@내일" }
 */

export interface DateTagResult {
  cleanText: string;
  date: Date | null;
  label: string | null;
  matchedRaw: string | null;
}

const DAYS = ["일", "월", "화", "수", "목", "금", "토"];
const WEEKDAY_LONG = DAYS.map((d) => `${d}요일`);
const RELATIVE_OFFSETS: Record<string, number> = { 내일: 1, 모레: 2, 글피: 3 };
const DAYS_IN_WEEK = 7;
const MONDAY_INDEX = 1;
const TAG_PREFIX = "@";

const RELATIVE_PATTERN = new RegExp(
  `${TAG_PREFIX}(${Object.keys(RELATIVE_OFFSETS).join("|")})`
);
const NEXT_WEEK_PATTERN = new RegExp(
  `${TAG_PREFIX}다음주(${WEEKDAY_LONG.join("|")})`
);
const WEEKDAY_PATTERN = new RegExp(
  `${TAG_PREFIX}(${WEEKDAY_LONG.join("|")})`
);
const SLASH_DATE_PATTERN = new RegExp(`${TAG_PREFIX}(\\d{1,2})/(\\d{1,2})`);
const KOREAN_DATE_PATTERN = new RegExp(`${TAG_PREFIX}(\\d{1,2})월(\\d{1,2})일`);

function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function formatLabel(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()} (${DAYS[d.getDay()]})`;
}

function stripTag(text: string, matched: string): string {
  return text.replace(matched, "").replace(/\s+/g, " ").trim();
}

function buildResult(text: string, matched: string, date: Date): DateTagResult {
  return {
    cleanText: stripTag(text, matched),
    date,
    label: formatLabel(date),
    matchedRaw: matched,
  };
}

function nullResult(text: string): DateTagResult {
  return { cleanText: text, date: null, label: null, matchedRaw: null };
}

function tryRelative(text: string, base: Date): DateTagResult | null {
  const m = text.match(RELATIVE_PATTERN);
  if (!m) return null;
  const offset = RELATIVE_OFFSETS[m[1]];
  const date = addDays(startOfDay(base), offset);
  return buildResult(text, m[0], date);
}

function tryNextWeekday(text: string, base: Date): DateTagResult | null {
  const m = text.match(NEXT_WEEK_PATTERN);
  if (!m) return null;
  const targetIdx = WEEKDAY_LONG.indexOf(m[1]);
  const base0 = startOfDay(base);
  const diffToMonday = (MONDAY_INDEX - base0.getDay() + DAYS_IN_WEEK) % DAYS_IN_WEEK;
  const daysToNextMonday = diffToMonday === 0 ? DAYS_IN_WEEK : diffToMonday;
  const nextMonday = addDays(base0, daysToNextMonday);
  const offset = (targetIdx - MONDAY_INDEX + DAYS_IN_WEEK) % DAYS_IN_WEEK;
  return buildResult(text, m[0], addDays(nextMonday, offset));
}

function tryWeekday(text: string, base: Date): DateTagResult | null {
  const m = text.match(WEEKDAY_PATTERN);
  if (!m) return null;
  const targetIdx = WEEKDAY_LONG.indexOf(m[1]);
  const base0 = startOfDay(base);
  let diff = (targetIdx - base0.getDay() + DAYS_IN_WEEK) % DAYS_IN_WEEK;
  if (diff === 0) diff = DAYS_IN_WEEK;
  return buildResult(text, m[0], addDays(base0, diff));
}

function tryNumericDate(text: string, base: Date): DateTagResult | null {
  const m = text.match(SLASH_DATE_PATTERN) ?? text.match(KOREAN_DATE_PATTERN);
  if (!m) return null;
  const month = Number(m[1]);
  const day = Number(m[2]);
  const base0 = startOfDay(base);
  let date = new Date(base0.getFullYear(), month - 1, day);
  if (date.getMonth() !== month - 1 || date.getDate() !== day) {
    return nullResult(text);
  }
  if (date < base0) {
    date = new Date(base0.getFullYear() + 1, month - 1, day);
  }
  return buildResult(text, m[0], date);
}

export function parseDateTag(text: string, baseDate: Date): DateTagResult {
  const matchers = [tryRelative, tryNextWeekday, tryWeekday, tryNumericDate];
  for (const matcher of matchers) {
    const result = matcher(text, baseDate);
    if (result) return result;
  }
  return nullResult(text);
}
```

## Self-check
- spec 완료 기준 매핑:
  1. 충족 (`tryRelative` + `RELATIVE_OFFSETS`의 `내일:1`로 baseDate+1)
  2. 충족 (`tryWeekday`에서 `diff === 0 → DAYS_IN_WEEK`로 +7 강제)
  3. 충족 (`tryNextWeekday`에서 base 주의 다음 월요일을 구한 뒤 offset 가산, `NEXT_WEEK_PATTERN`을 `WEEKDAY_PATTERN`보다 먼저 시도)
  4. 충족 (`SLASH_DATE_PATTERN`/`KOREAN_DATE_PATTERN` 양쪽 시도, `date < base0`이면 year+1)
  5. 충족 (`new Date(y,m-1,d)` 의 month/day 롤오버 검사로 `@2/30` 감지 → `nullResult`)
  6. 충족 (모든 matcher가 null 반환 시 `parseDateTag` 말미에서 `nullResult(text)` — cleanText 원본 유지)
  7. 충족 (`stripTag`가 `replace(/\s+/g," ").trim()` 로 양쪽/중복 공백 정리)
- 타입 안전성: OK (`DateTagResult` export, 모든 경로에서 동일 shape 반환, 숫자 변환은 `Number`)
- 에지 케이스 처리:
  - 오늘과 같은 요일 → 다음 주 (+7)
  - base가 월요일일 때 `@다음주X` → 정확히 7일 뒤부터 계산 (`diffToMonday === 0 → 7`)
  - base가 일요일일 때 `@다음주월요일` → base+1일 (day 0 → MONDAY_INDEX 1)
  - `@2/30` 같은 invalid → month/day 롤오버 감지 후 null 복귀
  - `@1/1` 이 이미 지남 → 내년
  - `@가나다` 매칭 실패 → 원본 cleanText
  - 양쪽 공백/중복 공백 정리
  - `@4월5일` / `@4/5` 둘 다 지원
- 토큰 효율: 설명 최소화 (상단 JSDoc 1개만), HARD RULES 준수 (공개 함수 `parseDateTag` 6줄, 모든 헬퍼 ≤ 15줄, DRY 상수는 `DAYS`/`WEEKDAY_LONG`/`RELATIVE_OFFSETS`/`DAYS_IN_WEEK`/`MONDAY_INDEX`/`TAG_PREFIX` 단일 선언)