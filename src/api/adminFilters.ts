export type AdminFilters = {
  /** YYYY-MM-DD, inclusive. */
  start: string;
  end: string;
  trainers: string[];
  zones: string[];
  regions: string[];
  sessionTypes: string[];
  trainingTypes: string[];
};

export const EMPTY_ADMIN_FILTERS: AdminFilters = {
  start: "",
  end: "",
  trainers: [],
  zones: [],
  regions: [],
  sessionTypes: [],
  trainingTypes: [],
};

const pad2 = (n: number) => String(n).padStart(2, "0");
const toIso = (d: Date) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

/** The dashboard's starting filter: today only. */
export function defaultAdminFilters(): AdminFilters {
  const today = toIso(new Date());
  return { ...EMPTY_ADMIN_FILTERS, start: today, end: today };
}

/** What the filter panel pre-fills for the dashboard: 1st of this month through today. */
export function monthToDateAdminFilters(): AdminFilters {
  const now = new Date();
  return { ...EMPTY_ADMIN_FILTERS, start: toIso(new Date(now.getFullYear(), now.getMonth(), 1)), end: toIso(now) };
}

export function adminFiltersActive(filters: AdminFilters): boolean {
  return Boolean(
    filters.start ||
      filters.end ||
      filters.trainers.length ||
      filters.zones.length ||
      filters.regions.length ||
      filters.sessionTypes.length ||
      filters.trainingTypes.length,
  );
}

/** Query-string parts for the backend's shared admin filter (empty ones omitted). */
export function adminFilterParams(filters?: AdminFilters): [string, string][] {
  if (!filters) return [];
  const entries: [string, string][] = [
    ["start", filters.start],
    ["end", filters.end],
    ["trainers", filters.trainers.join(",")],
    ["zones", filters.zones.join(",")],
    ["regions", filters.regions.join(",")],
    ["session_types", filters.sessionTypes.join(",")],
    ["training_types", filters.trainingTypes.join(",")],
  ];
  return entries.filter(([, value]) => value !== "");
}
