/**
 * useAdminDashboard Hook
 * Manages admin dashboard data fetching, approving/rejecting sessions,
 * loading/refreshing states, and action states.
 */

import { useCallback, useEffect, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { AdminDashboardStats, fetchAdminDashboardStats } from "@/api/admin";
import { useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import {
  ApiError,
  PendingSessionItem,
  fetchPendingTrainings,
} from "@/api/training";
import { subscribe } from "@/services/liveEvents";

export function useAdminDashboard() {
  const router = useRouter();
  const { admin, adminToken, adminLogout } = useAuth();
  const { applied, appliedKey } = useAdminFilters("home");

  const [pending, setPending] = useState<PendingSessionItem[]>([]);
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
      try {
        const [pendingList, statsResult] = await Promise.all([
          fetchPendingTrainings(adminToken),
          fetchAdminDashboardStats(adminToken, applied),
        ]);
        setPending(pendingList);
        setStats(statsResult);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Couldn't load the admin dashboard.",
        );
      } finally {
        if (isRefresh) {
          setRefreshing(false);
        } else {
          setLoading(false);
        }
      }
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

  const handleLogout = () => {
    adminLogout();
    router.replace("/trainer_login");
  };

  return {
    admin,
    pending,
    stats,
    loading,
    refreshing,
    error,
    refresh: () => load(true),
    handleLogout,
  };
}
