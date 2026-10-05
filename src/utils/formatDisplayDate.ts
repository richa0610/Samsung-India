// Accepts "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS" and displays it as "Fri, 25 Jul 2026".
export function formatDisplayDate(value: string | null): string {
  if (!value) return "--";
  const date = new Date(`${value.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  const weekday = date.toLocaleDateString("en-US", { weekday: "short" });
  const day = String(date.getDate()).padStart(2, "0");
  const month = date.toLocaleDateString("en-US", { month: "short" });
  return `${weekday}, ${day} ${month} ${date.getFullYear()}`;
}

export function getTodayFormattedDate(): string {
  const date = new Date();
  const day = String(date.getDate()).padStart(2, "0");
  const month = date.toLocaleDateString("en-US", { month: "short" });
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
}

/** Today's date in India (IST, UTC+5:30) as "YYYY-MM-DD", whatever the device's own time zone -
 *  the same "today" the server uses for the trainer's Home and Sessions. */
export function istToday(): string {
  return new Date(Date.now() + 330 * 60 * 1000).toISOString().slice(0, 10);
}

/** This month so far in India - its 1st through today ("YYYY-MM-DD") - the default date range of
 *  the trainer's lists and Sessions screen. */
export function monthToTodayRange(): { start: string; end: string } {
  const today = istToday();
  return { start: `${today.slice(0, 7)}-01`, end: today };
}
