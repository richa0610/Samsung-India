import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";

import { CurrentSession, TraineeDashboard, getCurrentSession, getTraineeDashboard } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";

export function useTraineeDashboard() {
  const router = useRouter();
  const { trainee, token, logout } = useAuth();

  const [session, setSession] = useState<CurrentSession | null>(null);
  const [dashboard, setDashboard] = useState<TraineeDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    // Session drives the header; dashboard drives metrics/performance/table.
    // Either can be absent (no active session / brand-new trainee) - the
    // screen renders zeros and an empty table in that case.
    // Only the 5 most recent here - the full history lives on its own
    // screen (Training Details' "View All" -> /training_history).
    const [sessionResult, dashboardResult] = await Promise.allSettled([
      getCurrentSession(token),
      getTraineeDashboard(token, 5),
    ]);
    setSession(sessionResult.status === "fulfilled" ? sessionResult.value : null);
    setDashboard(dashboardResult.status === "fulfilled" ? dashboardResult.value : null);
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      load().finally(() => setLoading(false));
    }, [load]),
  );

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    load().finally(() => setRefreshing(false));
  }, [load]);

  const handleLogout = () => {
    logout();
    router.replace("/");
  };

  return {
    trainee,
    session,
    dashboard,
    loading,
    refreshing,
    handleRefresh,
    handleLogout,
  };
}
