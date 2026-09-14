import { TrainingAgendaItem } from "@/api/training";

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

export function filterSessions(
  sessions: TrainingAgendaItem[],
  activeTab: SessionTab,
  searchQuery: string,
  filters: SessionFilters,
): TrainingAgendaItem[] {
  const todayStr = new Date().toISOString().split("T")[0];

  return sessions.filter((session) => {
    if (activeTab === "today") {
      const isToday =
        session.conferenceDate === todayStr ||
        session.conferenceStatus === "Ongoing" ||
        session.conferenceTime === "09:00" ||
        session.conferenceTime === "12:00";
      if (!isToday) return false;
    } else if (activeTab === "completed") {
      if (session.conferenceStatus !== "Completed") return false;
    }

    if (filters.fromDate && session.conferenceDate && session.conferenceDate < filters.fromDate) {
      return false;
    }
    if (filters.toDate && session.conferenceDate && session.conferenceDate > filters.toDate) {
      return false;
    }

    if (filters.location && (session.trainingHub || session.state) !== filters.location) {
      return false;
    }

    if (filters.sessionType && session.trainingType !== filters.sessionType) {
      return false;
    }

    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase();
      const matchesTitle = (session.title || "").toLowerCase().includes(q);
      const matchesUid = (session.conferenceUid || "").toLowerCase().includes(q);
      const matchesLocation = (session.trainingHub || session.state || "").toLowerCase().includes(q);
      return matchesTitle || matchesUid || matchesLocation;
    }

    return true;
  });
}

// Combines conferenceDate ("YYYY-MM-DD") + conferenceTime ("hh:mm AM/PM")
// into a sortable timestamp. Returns NaN for anything unparseable so those
// sessions can be pushed to the end of their group rather than breaking
// the sort.
function sessionTimestamp(session: TrainingAgendaItem): number {
  if (!session.conferenceDate) return NaN;
  const parsed = new Date(`${session.conferenceDate}T00:00:00`);
  if (isNaN(parsed.getTime())) return NaN;

  const match = (session.conferenceTime || "").match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (match) {
    let hours = Number(match[1]) % 12;
    if (match[3].toUpperCase() === "PM") hours += 12;
    parsed.setHours(hours, Number(match[2]), 0, 0);
  }
  return parsed.getTime();
}

// Ordering: live/ongoing sessions first, then scheduled ones soonest-first,
// then completed sessions most-recent-first - so the table leads with what
// needs attention now or soonest, and trails off into history.
export function sortSessions(sessions: TrainingAgendaItem[]): TrainingAgendaItem[] {
  const completed = sessions.filter((s) => s.conferenceStatus === "Completed");
  const upcoming = sessions.filter((s) => s.conferenceStatus !== "Completed");

  upcoming.sort((a, b) => {
    const aLive = a.conferenceStatus === "Ongoing";
    const bLive = b.conferenceStatus === "Ongoing";
    if (aLive !== bLive) return aLive ? -1 : 1;

    const aTime = sessionTimestamp(a);
    const bTime = sessionTimestamp(b);
    if (isNaN(aTime) && isNaN(bTime)) return 0;
    if (isNaN(aTime)) return 1;
    if (isNaN(bTime)) return -1;
    return aTime - bTime;
  });

  completed.sort((a, b) => {
    const aTime = sessionTimestamp(a);
    const bTime = sessionTimestamp(b);
    if (isNaN(aTime) && isNaN(bTime)) return 0;
    if (isNaN(aTime)) return 1;
    if (isNaN(bTime)) return -1;
    return bTime - aTime;
  });

  return [...upcoming, ...completed];
}

export function getUniqueOptions(
  sessions: TrainingAgendaItem[],
  field: "trainingHub" | "trainingType"
): { label: string; value: string }[] {
  const seen = new Set<string>();
  const options: { label: string; value: string }[] = [];
  for (const session of sessions) {
    const raw = session[field];
    if (!raw || raw === "Not Assigned" || seen.has(raw)) continue;
    seen.add(raw);
    options.push({ label: raw, value: raw });
  }
  return options;
}

export type SessionDisplayStatus = "live_now" | "scheduled" | "completed";

export type SessionStatusConfig = {
  label: string;
  dotColor?: string;
  badgeBg: string;
  badgeTextColor: string;
  borderColor: string;
  buttonType: "launch" | "report";
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
      dotColor: "#EF4444",
      badgeBg: "#FEE2E2",
      badgeTextColor: "#EF4444",
      borderColor: "#FCA5A5",
      buttonType: "launch",
      buttonBg: "#0066FF",
      buttonText: "LAUNCH",
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
    buttonBg: "#0066FF",
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
