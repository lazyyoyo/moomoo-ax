const DAYS = ["일", "월", "화", "수", "목", "금", "토"];

export function todayStr(): string {
  return formatDate(new Date());
}

export function tomorrowStr(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return formatDate(d);
}

export function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function parseDate(dateStr: string): Date {
  const [y, m, d] = dateStr.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function isToday(dateStr: string): boolean {
  return dateStr === todayStr();
}

export function calcCarryoverDays(entryDate: string, today: string): number {
  const d1 = new Date(entryDate);
  const d2 = new Date(today);
  return Math.round((d2.getTime() - d1.getTime()) / 86400000);
}

export function formatDateLabel(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const day = DAYS[date.getDay()];
  return `${m}/${d} (${day})`;
}

export function formatShortDate(dateStr: string | null): string {
  if (!dateStr) return "없음";
  const [, m, d] = dateStr.split("-").map(Number);
  return `${m}/${d}`;
}
