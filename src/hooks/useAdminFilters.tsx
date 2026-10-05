import { ReactNode, createContext, useCallback, useContext, useMemo, useState } from "react";

import { AdminFilters, EMPTY_ADMIN_FILTERS, defaultAdminFilters, monthToDateAdminFilters } from "@/api/adminFilters";

/** "home" is the admin dashboard's own filter; "lists" is shared by the admin Training and
 *  Attendance list pages; "trainerLists" by every list in the trainer's flow (Training,
 *  Attendance and Trainee lists); "trainee" is the trainee dashboard's date range. Setting
 *  one never changes the others. */
export type AdminFilterScope = "home" | "lists" | "trainerLists" | "trainee";

type ScopedFilters = Record<AdminFilterScope, AdminFilters>;

type AdminFiltersContextValue = {
  filters: ScopedFilters;
  apply: (scope: AdminFilterScope, filters: AdminFilters) => void;
  clear: (scope: AdminFilterScope) => void;
};

const AdminFiltersContext = createContext<AdminFiltersContextValue | null>(null);

// The admin dashboard ("home") starts on today and the trainer's lists on this month so far (1st to
// today); the admin list pages and the trainee dashboard start unfiltered (showing everything)
// until the user applies a range. Clearing a filter returns it to this starting point.
const defaultForScope = (scope: AdminFilterScope): AdminFilters => {
  if (scope === "home") return defaultAdminFilters();
  if (scope === "trainerLists") return monthToDateAdminFilters();
  return EMPTY_ADMIN_FILTERS;
};

export function AdminFiltersProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<ScopedFilters>(() => ({
    home: defaultForScope("home"),
    lists: defaultForScope("lists"),
    trainerLists: defaultForScope("trainerLists"),
    trainee: defaultForScope("trainee"),
  }));

  const apply = useCallback(
    (scope: AdminFilterScope, next: AdminFilters) => setFilters((prev) => ({ ...prev, [scope]: next })),
    [],
  );
  const clear = useCallback(
    (scope: AdminFilterScope) => setFilters((prev) => ({ ...prev, [scope]: defaultForScope(scope) })),
    [],
  );

  const value = useMemo(() => ({ filters, apply, clear }), [filters, apply, clear]);

  return <AdminFiltersContext.Provider value={value}>{children}</AdminFiltersContext.Provider>;
}

export function useAdminFilters(scope: AdminFilterScope) {
  const context = useContext(AdminFiltersContext);
  if (!context) throw new Error("useAdminFilters must be used inside AdminFiltersProvider");
  const applied = context.filters[scope];
  const { apply, clear } = context;
  return useMemo(
    () => ({
      applied,
      /** Stable string form of `applied` - handy as a hook dependency. */
      appliedKey: JSON.stringify(applied),
      apply: (next: AdminFilters) => apply(scope, next),
      clear: () => clear(scope),
      /** What `clear` returns this scope to. */
      defaults: defaultForScope(scope),
    }),
    [applied, apply, clear, scope],
  );
}
