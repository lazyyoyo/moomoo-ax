# Implementation: haru:7475bef

## Summary
- verdict: ready
- `@` 자연어 날짜 태그 파서 구현 (상대/요일/다음주요일/숫자 4개 패턴 + cleanText 정리)
- 생성 파일: `dev/src/lib/parse-date-tag.ts`

## Files

### dev/src/lib/parse-date-tag.ts
```typescript
const DAYS = ["일", "월", "화", "수", "목", "금", "토"];

export interface DateTagResult {
  cleanText: string;
  date: Date | null;
  label: string | null;
  matchedRaw: string | null;
}

function formatLabel(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()} (${DAYS[d.getDay()]})`;
}

function stripAndClean(text: string, matched: string): string {
  return text.replace(matched, "").replace(/\s+/g, " ").trim();
}

function weekdayIndex(ch: string): number {
  return DAYS.indexOf(ch);
}

export function parseDateTag(text: string, baseDate: Date): DateTagResult {
  const none: DateTagResult = { cleanText: text, date: null, label: null, matchedRaw: null };

  // 1. 다음주 요일 (요일 패턴보다 먼저 검사)
  const nextWeek = text.match(/@다음주([월화수목금토일])요일/);
  if (nextWeek) {
    const targetIdx = weekdayIndex(nextWeek[1]);
    const d = new Date(baseDate);
    const daysUntilNextMon = ((8 - d.getDay()) % 7) || 7;
    d.setDate(d.getDate() + daysUntilNextMon);
    const offset = (targetIdx - 1 + 7) % 7;
    d.setDate(d.getDate() + offset);
    const matched = nextWeek[0];
    return { cleanText: stripAndClean(text, matched), date: d, label: formatLabel(d), matchedRaw: matched };
  }

  // 2. 상대 날짜
  const rel = text.match(/@(내일|모레|글피)/);
  if (rel) {
    const offsets: Record<string, number> = { 내일: 1, 모레: 2, 글피: 3 };
    const d = new Date(baseDate);
    d.setDate(d.getDate() + offsets[rel[1]]);
    const matched = rel[0];
    return { cleanText: stripAndClean(text, matched), date: d, label: formatLabel(d), matchedRaw: matched };
  }

  // 3. 요일 (오늘 이후 가장 가까운, 오늘이면 +7)
  const weekday = text.match(/@([월화수목금토일])요일/);
  if (weekday) {
    const targetIdx = weekdayIndex(weekday[1]);
    const d = new Date(baseDate);
    let offset = (targetIdx - d.getDay() + 7) % 7;
    if (offset === 0) offset = 7;
    d.setDate(d.getDate() + offset);
    const matched = weekday[0];
    return { cleanText: stripAndClean(text, matched), date: d, label: formatLabel(d), matchedRaw: matched };
  }

  // 4. 숫자 날짜 (@M/D 또는 @M월D일)
  const num = text.match(/@(\d{1,2})(?:\/|월)(\d{1,2})(?:일)?/);
  if (num) {
    const month = parseInt(num[1], 10);
    const day = parseInt(num[2], 10);
    const baseYear = baseDate.getFullYear();
    const candidate = new Date(baseYear, month - 1, day);
    if (candidate.getMonth() !== month - 1 || candidate.getDate() !== day) {
      return none;
    }
    const baseMidnight = new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate());
    let year = baseYear;
    if (candidate.getTime() < baseMidnight.getTime()) {
      year = baseYear + 1;
    }
    const finalDate = new Date(year, month - 1, day);
    const matched = num[0];
    return { cleanText: stripAndClean(text, matched), date: finalDate, label: formatLabel(finalDate), matchedRaw: matched };
  }

  return none;
}
```

## Self-check
- spec 완료 기준 매핑:
  1. 충족 (`@내일` → offsets.내일=1, baseDate+1일)
  2. 충족 (요일 패턴에서 `offset===0 → 7` 로 오늘이면 다음 주 처리)
  3. 충족 (`@다음주X요일` 핸들러에서 다음 주 월요일 계산 후 오프셋)
  4. 충족 (`@M/D` / `@M월D일` 정규식, `candidate < baseMidnight` 시 year+1)
  5. 충족 (new Date 역검증으로 `@2/30` → none 반환)
  6. 충족 (모든 패턴 미매칭 시 `none` = {cleanText: text, ...null})
  7. 충족 (`stripAndClean` 에서 `\s+` → 단일 공백 + trim)
- 타입 안전성: OK (DateTagResult 인터페이스 export, 모든 분기 동일 shape)
- 에지 케이스 처리: `@2/30` 유효성 실패, `@가나다` 미매칭, 양쪽/중복 공백, 오늘 요일 = 다음 주, 과거 숫자 날짜 → 내년, `@4월5일` / `@4/5` 모두 동일 처리
- 토큰 효율: 설명 없음 (주석 최소, 섹션 번호 주석만 유지)