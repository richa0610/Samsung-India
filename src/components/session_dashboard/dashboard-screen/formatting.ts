/** "2h 05m 07s" - always h/m/s, zero when the session hasn't started. */
export function formatDurationHMS(seconds: number | null | undefined): string {
  const s = Math.max(0, Math.floor(seconds ?? 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${String(m).padStart(2, "0")}m ${String(s % 60).padStart(2, "0")}s`;
}

export function formatRuntimeLabel(seconds: number | null | undefined): string {
  return `Runtime : ${formatDurationHMS(seconds)}`;
}

/** "0h 42m" - hours + minutes only, for planned/consumed time budgets. */
export function formatDurationHM(seconds: number | null | undefined): string {
  const s = Math.max(0, Math.floor(seconds ?? 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${String(m).padStart(2, "0")}m`;
}

export function formatGeneratedTimestamp(d: Date): string {
  const day = String(d.getDate()).padStart(2, "0");
  const month = d.toLocaleDateString("en-GB", { month: "long" });
  const year = d.getFullYear();
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
  return `Generated: ${day} ${month} ${year}, ${time}`;
}
