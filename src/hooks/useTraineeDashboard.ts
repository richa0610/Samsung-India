import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { BackHandler } from "react-native";

import { CurrentSession, TraineeDashboard, getCurrentSession, getTraineeDashboard } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { canNavigate } from "@/utils/navigationGuard";

export function useTraineeDashboard() {
  const router = useRouter();
  const { trainee, token, logout } = useAuth();

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
    confirmLogoutOpen,
    requestLogout,
    cancelLogout,
    confirmLogout,
  };
}
