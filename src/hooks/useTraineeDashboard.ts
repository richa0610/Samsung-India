import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { BackHandler } from "react-native";

import { CurrentSession, TraineeDashboard, getCurrentSession, getTraineeDashboard } from "@/api/session";
import { TraineeMetricCardKey } from "@/components/trainee/dashboard/TraineeMetricsGrid";
import { useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import { canNavigate } from "@/utils/navigationGuard";

export function useTraineeDashboard() {
  const router = useRouter();
  const { trainee, token, logout } = useAuth();
  const { applied, appliedKey } = useAdminFilters("trainee");

  const [session, setSession] = useState<CurrentSession | null>(null);
  const [dashboard, setDashboard] = useState<TraineeDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  // Same confirm-before-logout flow as the trainee profile / home power
  // buttons - opening the popup is separate from actually logging out,
  // which only happens on confirm.
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    // Session drives the header; dashboard drives metrics/performance/table.
    // Either can be absent (no active session / brand-new trainee) - the
    // screen renders zeros and an empty table in that case.
    // Only the 5 most recent here - the full history lives on its own
    // screen (Training Details' "View All" -> /training_history).
    const [sessionResult, dashboardResult] = await Promise.allSettled([
      getCurrentSession(token),
      getTraineeDashboard(token, 5, { start: applied.start, end: applied.end }),
    ]);
    setSession(sessionResult.status === "fulfilled" ? sessionResult.value : null);
    setDashboard(dashboardResult.status === "fulfilled" ? dashboardResult.value : null);
  // eslint-disable-next-line react-hooks/exhaustive-deps -- `appliedKey` is `applied`, serialised so an equal filter doesn't refetch
  }, [token, appliedKey]);

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

  // A metric card opens Training History holding exactly the trainings that card counted, over
  // the dashboard's own date range - like the trainer's Home stat cards open their Sessions list.
  const handleMetricCardPress = (card: TraineeMetricCardKey) => {
    router.push({
      pathname: "/training_history",
      params: {
        ...(card !== "total" && { card }),
        ...(applied.start && { start: applied.start }),
        ...(applied.end && { end: applied.end }),
      },
    });
  };

  const requestLogout = () => setConfirmLogoutOpen(true);

  // Hardware/gesture back asks for confirmation instead of navigating
  // anywhere - same popup and destination as the header's power button, on
  // every trainee tab (Home/Dashboard/Rank/Profile) uniformly.
  useFocusEffect(
    useCallback(() => {
      const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
        requestLogout();
        return true;
      });
      return () => subscription.remove();
    }, []),
  );

  const cancelLogout = () => setConfirmLogoutOpen(false);
  const confirmLogout = () => {
    setConfirmLogoutOpen(false);
    logout();
    if (canNavigate()) router.replace("/");
  };

  return {
    trainee,
    session,
    dashboard,
    loading,
    refreshing,
    handleRefresh,
    handleMetricCardPress,
    confirmLogoutOpen,
    requestLogout,
    cancelLogout,
    confirmLogout,
  };
}
