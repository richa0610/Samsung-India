export type DateRange = { start: Date; end: Date };
export type DatePreset = "today" | "this_month" | "last_7" | "last_30" | "custom";

export const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export const MONTH_FULL_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export const PRESETS: { key: DatePreset; label: string }[] = [
  { key: "today", label: "Today" },
  { key: "this_month", label: "This Month" },
  { key: "last_7", label: "Last 7 Days" },
  { key: "last_30", label: "Last 30 Days" },
];

export const startOfDay = (d: Date): Date =>
  new Date(d.getFullYear(), d.getMonth(), d.getDate());

export function isSameDay(d1: Date | null, d2: Date | null): boolean {
  if (!d1 || !d2) return false;
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

export function isBetweenDates(
  target: Date,
  start: Date | null,
  end: Date | null
): boolean {
  if (!start || !end) return false;
  const t = startOfDay(target).getTime();
  const s = startOfDay(start).getTime();
  const e = startOfDay(end).getTime();
  const min = Math.min(s, e);
  const max = Math.max(s, e);
  return t > min && t < max;
}

export function isToday(d: Date): boolean {
  return isSameDay(d, new Date());
}

export function rangeForPreset(preset: DatePreset, fallback?: DateRange): DateRange {
  const today = startOfDay(new Date());
  switch (preset) {
    case "today":
      return { start: today, end: today };
    case "this_month":
      return {
        start: new Date(today.getFullYear(), today.getMonth(), 1),
        end: new Date(today.getFullYear(), today.getMonth() + 1, 0),
      };
    case "last_7":
      return {
        start: new Date(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - 6
        ),
        end: today,
      };
    case "last_30":
      return {
        start: new Date(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - 29
        ),
        end: today,
      };
    default:
      return fallback || { start: today, end: today };
  }
}

export function formatDMY(d: Date): string {
  return `${String(d.getDate()).padStart(2, "0")}-${String(d.getMonth() + 1).padStart(2, "0")}-${d.getFullYear()}`;
}

export function formatMonthDay(d: Date): string {
  const day = String(d.getDate()).padStart(2, "0");
  const month = MONTH_FULL_NAMES[d.getMonth()];
  return `${day} ${month}`;
}

export function formatDisplayDate(d: Date): string {
  const day = String(d.getDate()).padStart(2, "0");
  const month = MONTH_NAMES[d.getMonth()];
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

export type CalendarGridDay = {
  date: Date;
  dayNumber: number;
  isCurrentMonth: boolean;
};

export function generateMonthGrid(
  year: number,
  month: number
): CalendarGridDay[] {
  const firstDayIndex = new Date(year, month, 1).getDay();
  const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
  const totalDaysInPrevMonth = new Date(year, month, 0).getDate();

  const days: CalendarGridDay[] = [];

  // Trailing days from previous month
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    const dayNumber = totalDaysInPrevMonth - i;
    days.push({
      date: new Date(year, month - 1, dayNumber),
      dayNumber,
      isCurrentMonth: false,
    });
  }

  // Days in current month
  for (let i = 1; i <= totalDaysInMonth; i++) {
    days.push({
      date: new Date(year, month, i),
      dayNumber: i,
      isCurrentMonth: true,
    });
  }

  // Leading days from next month to fill out the remaining grid slots (to a multiple of 7, up to 35 or 42)
  const remaining = (7 - (days.length % 7)) % 7;
  for (let i = 1; i <= remaining; i++) {
    days.push({
      date: new Date(year, month + 1, i),
      dayNumber: i,
      isCurrentMonth: false,
    });
  }

  return days;
}
