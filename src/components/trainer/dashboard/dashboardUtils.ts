import { DatePreset } from "@/components/trainer/DateDrop";

export type { DatePreset };

export const PRESET_LABELS: Record<DatePreset, string> = {
  today: "Today",
  this_month: "This Month",
  last_7: "Last 7 Days",
  last_30: "Last 30 Days",
  custom: "Custom",
};

export function formatDisplayDate(d: Date): string {
  const day = String(d.getDate()).padStart(2, "0");
  const month = d.toLocaleDateString("en-GB", { month: "short" });
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

export function formatSessionTime(dateStr: string | null, timeStr: string | null): string {
  let dateFormatted = "--";
  if (dateStr) {
    const parsed = new Date(`${dateStr}T00:00:00`);
    if (!isNaN(parsed.getTime())) {
      dateFormatted = `${String(parsed.getDate()).padStart(2, "0")} ${parsed.toLocaleDateString("en-GB", { month: "short" })} ${parsed.getFullYear()}`;
    }
  }
  const timeFormatted = timeStr || "10:00 AM";
  return `${dateFormatted} • ${timeFormatted}`;
}

export type DashboardStats = {
  totalTrainees: number;
  totalSessions: number;
  completed: number;
  pending: number;
  executedPercentage: number;
  pendingPercentage: number;
};

// All of `DashboardStats` is computed server-side now (see
// `TrainerAgendaResponse` in api/training.ts) and just read off the
// fetch response - no client-side derivation left to do here.

export type SessionStatusType = "completed" | "in_progress" | "upcoming";

export function getSessionStatusInfo(status: string): { label: string; type: SessionStatusType; bg: string; color: string } {
  if (status === "Completed") {
    return { label: "Completed", type: "completed", bg: "#DCFCE7", color: "#16A34A" };
  }
  if (status === "Ongoing") {
    return { label: "In Progress", type: "in_progress", bg: "#E0F2FE", color: "#0284C7" };
  }
  return { label: "Upcoming", type: "upcoming", bg: "#FEF3C7", color: "#D97706" };
}
