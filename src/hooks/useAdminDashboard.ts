/**
 * useAdminDashboard Hook
 * Manages admin dashboard data fetching, approving/rejecting sessions,
 * loading/refreshing states, and action states.
 */

import { useCallback, useEffect, useState } from "react";
import { useFocusEffect } from "expo-router";
import { AdminDashboardStats, fetchAdminDashboardStats } from "@/api/admin";
import { useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, fetchPendingTrainingCount } from "@/api/training";
import { subscribe } from "@/services/liveEvents";

export function useAdminDashboard() {
  const { admin, adminToken } = useAuth();
  const { applied, appliedKey } = useAdminFilters("home");

  // How many trainings await review (the banner and the tab badge only ever show the number).
  const [pendingCount, setPendingCount] = useState(0);
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isRefresh = false) => {
      if (!adminToken) return;
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      const fail = (err: unknown) =>
        setError(err instanceof ApiError ? err.message : "Couldn't load the admin dashboard.");

      // The two requests are independent, so each result is shown the moment it
      // arrives - the stat cards no longer wait for the (separate) pending-review
      // count, or the other way round.
      const pendingTask = fetchPendingTrainingCount(adminToken).then(setPendingCount).catch(fail);
      try {
        // A normal open may use the server's 30-second cache; a pull-to-refresh or a
        // live "training changed" event (both call load(true)) always gets fresh numbers.
        setStats(await fetchAdminDashboardStats(adminToken, applied, { fresh: isRefresh }));
      } catch (err) {
        fail(err);
      } finally {
        if (!isRefresh) setLoading(false);
      }
      await pendingTask;
      if (isRefresh) setRefreshing(false);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `appliedKey` is `applied`, serialised so an equal filter doesn't refetch
    [adminToken, appliedKey],
  );

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  // Live WebSocket subscription: silently refetch dashboard stats and lists
  // whenever a relevant event arrives over /ws/admin
  useEffect(() => {
    const unsubCreated = subscribe("training_created", () => load(true));
    const unsubStatus = subscribe("training_status_changed", () => load(true));
    const unsubUpdated = subscribe("training_updated", () => load(true));
    const unsubAttendance = subscribe("attendance_marked", () => load(true));
    return () => {
      unsubCreated();
      unsubStatus();
      unsubUpdated();
      unsubAttendance();
    };
  }, [load]);

  return {
    admin,
    pendingCount,
    stats,
    loading,
    refreshing,
    error,
    refresh: () => load(true),
  };
}
