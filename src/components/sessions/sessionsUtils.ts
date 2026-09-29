import { Colors } from "@/theme/colors";

export type SessionTab = "all" | "today" | "completed";

export type SessionFilters = {
  fromDate: string;
  toDate: string;
  location: string;
  sessionType: string;
};

export const DEFAULT_SESSION_FILTERS: SessionFilters = {
  fromDate: "",
  toDate: "",
  location: "",
  sessionType: "",
};

export type SessionDisplayStatus = "live_now" | "scheduled" | "completed";

export type SessionStatusConfig = {
  label: string;
  dotColor?: string;
  badgeBg: string;
  badgeTextColor: string;
  borderColor: string;
  buttonType: "launch" | "report" | "live";
  buttonBg: string;
  buttonText: string;
};

export function getSessionStatusConfig(
  conferenceStatus: string,
  approvalStatus?: string
): SessionStatusConfig {
  const normalized = (conferenceStatus || "").toLowerCase();

  if (normalized === "ongoing" || normalized === "live" || normalized === "live now") {
    return {
      label: "LIVE NOW",
      dotColor: Colors.red,
      badgeBg: Colors.dangerBg,
      badgeTextColor: Colors.red,
      borderColor: "#FCA5A5",
      buttonType: "live",
      buttonBg: Colors.brandBlue,
      buttonText: "LIVE",
    };
  }

  if (normalized === "completed") {
    return {
      label: "COMPLETED",
      dotColor: "#0D9488",
      badgeBg: "#CCFBF1",
      badgeTextColor: "#0D9488",
      borderColor: "#99F6E4",
      buttonType: "report",
      buttonBg: "#1E293B",
      buttonText: "REPORT",
    };
  }

  // Scheduled / Upcoming default
  return {
    label: "SCHEDULED",
    badgeBg: "#FEF3C7",
    badgeTextColor: "#B45309",
    borderColor: "#FDE68A",
    buttonType: "launch",
    buttonBg: Colors.brandBlue,
    buttonText: "LAUNCH",
  };
}

export function parseSessionDate(dateStr?: string | null, timeStr?: string | null) {
  let day = "07";
  let month = "JUL";
  let time = timeStr || "09:00";

  if (dateStr) {
    const parsed = new Date(`${dateStr}T00:00:00`);
    if (!isNaN(parsed.getTime())) {
      day = String(parsed.getDate()).padStart(2, "0");
      month = parsed.toLocaleDateString("en-GB", { month: "short" }).toUpperCase();
    }
  }

  return { day, month, time };
}
