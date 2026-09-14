import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useMemo, useState } from "react";

import { DashboardTrainingRow, getTraineeDashboard } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";

// A trainee's own history is inherently small (bounded by how many sessions
// they've ever been part of), so fetching this many once and filtering
// client-side - same pattern as the trainer's Sessions screen - is enough;
// no dedicated paginated endpoint needed.
const ALL_TRAININGS_LIMIT = 500;

export function useTrainingHistory() {
  const router = useRouter();
  const { token } = useAuth();

  const [trainings, setTrainings] = useState<DashboardTrainingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const load = useCallback(
    async (mode: "load" | "refresh" = "load") => {
      if (!token) return;
      if (mode === "refresh") setRefreshing(true);
      else setLoading(true);
      try {
        const data = await getTraineeDashboard(token, ALL_TRAININGS_LIMIT);
        setTrainings(data.trainings);
      } catch {
        setTrainings([]);
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else setLoading(false);
      }
    },
    [token],
  );

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const filteredTrainings = useMemo(
    () =>
      trainings.filter((row) => {
        if (fromDate && (!row.rawDate || row.rawDate < fromDate)) return false;
        if (toDate && (!row.rawDate || row.rawDate > toDate)) return false;
        return true;
      }),
    [trainings, fromDate, toDate],
  );

  const clearFilters = () => {
    setFromDate("");
    setToDate("");
  };

  return {
    onBack: () => router.back(),
    trainings: filteredTrainings,
    loading,
    refreshing,
    onRefresh: () => load("refresh"),
    fromDate,
    toDate,
    setFromDate,
    setToDate,
    clearFilters,
    hasFilter: !!(fromDate || toDate),
  };
}
