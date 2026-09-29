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

export function formatMonthToToday(): string {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const sDay = String(firstDay.getDate()).padStart(2, "0");
  const sMonth = firstDay.toLocaleDateString("en-GB", { month: "short" });
  const eDay = String(now.getDate()).padStart(2, "0");
  const eMonth = now.toLocaleDateString("en-GB", { month: "short" });
  return `${sDay} ${sMonth} - ${eDay} ${eMonth}`;
}

