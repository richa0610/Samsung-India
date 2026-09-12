/**
 * useTraineeList Hook
 * Shared by Trainee List and Pending Trainee List - fetches the trainee
 * roster with support for filtering to pending-only, plus focus effect,
 * pull-to-refresh, and a live "trainee_created" push while focused.
 */

import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { useAuth } from "@/hooks/useAuth";
import { TraineeListItem, fetchTraineeList } from "@/api/trainee";
import { subscribe } from "@/services/liveEvents";

export function useTraineeList(filterPendingOnly = false) {
  const { adminToken } = useAuth();
  const [items, setItems] = useState<TraineeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      if (mode === "refresh") setRefreshing(true);
      else if (mode === "load") setLoading(true);
      try {
        const data = await fetchTraineeList(adminToken);
        setItems(filterPendingOnly ? data.filter((item) => item.approvalStatus === "Pending") : data);
      } catch {
        if (mode !== "silent") setItems([]);
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoading(false);
      }
    },
    [adminToken, filterPendingOnly],
  );

  useFocusEffect(
    useCallback(() => {
      load();
      const unsubscribe = subscribe("trainee_created", () => load("silent"));
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
