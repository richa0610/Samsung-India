import { ReactNode, createContext, useCallback, useContext, useMemo, useState } from "react";

import { AdminFilters, defaultAdminFilters } from "@/api/adminFilters";

/** "home" is the admin dashboard's own filter; "lists" is shared by the Training and
 *  Attendance list pages; "trainee" is the trainee dashboard's date range. Setting
 *  one never changes the others. */
export type AdminFilterScope = "home" | "lists" | "trainee";

type ScopedFilters = Record<AdminFilterScope, AdminFilters>;

type AdminFiltersContextValue = {
  filters: ScopedFilters;
  apply: (scope: AdminFilterScope, filters: AdminFilters) => void;
  clear: (scope: AdminFilterScope) => void;
};

const AdminFiltersContext = createContext<AdminFiltersContextValue | null>(null);

export function AdminFiltersProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<ScopedFilters>(() => ({
    home: defaultAdminFilters(),
    lists: defaultAdminFilters(),
    trainee: defaultAdminFilters(),
  }));

  const apply = useCallback(
    (scope: AdminFilterScope, next: AdminFilters) => setFilters((prev) => ({ ...prev, [scope]: next })),
    [],
  );
  const clear = useCallback(
    (scope: AdminFilterScope) => setFilters((prev) => ({ ...prev, [scope]: defaultAdminFilters() })),
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
    }),
    [applied, apply, clear, scope],
  );
}
