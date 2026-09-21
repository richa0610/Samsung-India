/**
 * useTrainerAgendaList Hook
 * Manages fetching trainer agenda sessions, with focus effect,
 * pull-to-refresh, and a live "training_created" push while focused.
 * `filterPendingOnly` picks which half of the approval split to show:
 * `true` for the Pending Training List (awaiting admin review), `false`
 * for the Training List (already approved - Scheduled/Ongoing/Completed).
 * Rejected trainings show in neither.
 */

import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { useAuth } from "@/hooks/useAuth";
import { TrainingAgendaItem, fetchTrainerAgenda } from "@/api/training";
import { useAdminFilters } from "@/hooks/useAdminFilters";
import { subscribe } from "@/services/liveEvents";

export function useTrainerAgendaList(filterPendingOnly = false, org = false) {
  const { adminToken } = useAuth();
  const { applied, appliedKey } = useAdminFilters("lists");
  const [items, setItems] = useState<TrainingAgendaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      if (mode === "refresh") setRefreshing(true);
      else if (mode === "load") setLoading(true);
      try {
        // Both callers (Training List, Pending Training List) want this
        // trainer's complete history, not the agenda endpoint's default
        // today-only scope - see all_sessions on GET /admin/trainings.
        const data = await fetchTrainerAgenda(adminToken, { all: true, org, filters: org ? applied : undefined });
        // Org-wide (admin) "other" list = everything already reviewed
        // (approved or rejected); a trainer's own list is approved only.
        setItems(
          data.trainings.filter((item) =>
            filterPendingOnly
              ? item.approvalStatus === "Pending"
              : org
                ? item.approvalStatus !== "Pending"
                : item.approvalStatus === "Approved",
          ),
        );
      } catch {
        if (mode !== "silent") setItems([]);
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `appliedKey` is `applied`, serialised so an equal filter doesn't refetch
    [adminToken, filterPendingOnly, org, appliedKey],
  );

  useFocusEffect(
    useCallback(() => {
      load();
      const unsubscribe = subscribe("training_created", () => load("silent"));
      return unsubscribe;
    }, [load]),
  );

  return {
    items,
    loading,
    refreshing,
    refresh: () => load("refresh"),
  };
}
