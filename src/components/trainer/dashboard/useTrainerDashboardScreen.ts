import { useFocusEffect, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { BackHandler } from "react-native";

import { TrainingAgendaItem, fetchTrainerAgenda } from "@/api/training";
import { DatePreset, DateRange, rangeForPreset } from "@/components/trainer/DateDrop";
import { useAuth } from "@/hooks/useAuth";
import { subscribe } from "@/services/liveEvents";
import { DashboardStats } from "./dashboardUtils";
import { toApiDate } from "./TrainerMoreMenu";

// Live "training_created" pushes drive refreshes now - this interval is
// just a safety net for a missed push or a reconnect gap, not the primary
// mechanism, hence far slower than the old 10s poll.
const FALLBACK_POLL_MS = 60000;

const EMPTY_STATS: DashboardStats = {
  totalTrainees: 0,
  totalSessions: 0,
  completed: 0,
  pending: 0,
  executedPercentage: 0,
  pendingPercentage: 0,
};

export type TrainerDashboardTab = "home" | "plan" | "profile" | "more";

export function useTrainerDashboardScreen() {
  const router = useRouter();
  const { admin, adminToken, adminLogout } = useAuth();

  const [activeTab, setActiveTab] = useState<TrainerDashboardTab>("home");
  const [menuOpen, setMenuOpen] = useState(false);
  const [dateDropOpen, setDateDropOpen] = useState(false);
  const [datePreset, setDatePreset] = useState<DatePreset>("today");
  const [dateRange, setDateRange] = useState<DateRange>(() =>
    rangeForPreset("today", { start: new Date(), end: new Date() }),
  );
  // Until the trainer explicitly applies a date filter, `loadAgenda` sends
  // no start/end at all - the backend then uses its own default view
  // (today for sessions, all-time for trainees) rather than whatever
  // `dateRange` happens to hold for display in the calendar boxes.
  const [filterApplied, setFilterApplied] = useState(false);
  // Every number here comes straight off the backend response - it's the
  // one joining against `conference`/`attendance`/`assessment_results`, so
  // nothing gets re-derived from the raw agenda list on the client.
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS);
  // Always the trainer's most recently completed sessions all-time, straight
  // off the backend - independent of `dateRange`/`filterApplied` above, so
  // the Recent Sessions card doesn't go empty just because today (or the
  // applied filter range) has nothing completed in it.
  const [recentCompleted, setRecentCompleted] = useState<TrainingAgendaItem[]>([]);
  const [loadingAgenda, setLoadingAgenda] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  // Shared by the header's power button AND the hardware/gesture back
  // button below - either one opens the same confirmation.
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);

  const loadAgenda = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      if (mode === "refresh") setRefreshing(true);
      else if (mode === "load") setLoadingAgenda(true);
      try {
        const data = await fetchTrainerAgenda(
          adminToken,
          filterApplied
            ? { start: toApiDate(dateRange.start), end: toApiDate(dateRange.end) }
            : undefined,
        );
        setStats({
          totalTrainees: data.totalTrainees,
          totalSessions: data.totalSessions,
          completed: data.completed,
          pending: data.pending,
          executedPercentage: data.executedPercentage,
          pendingPercentage: data.pendingPercentage,
        });
        setRecentCompleted(data.recentCompleted);
      } catch {
        if (mode !== "silent") {
          setStats(EMPTY_STATS);
          setRecentCompleted([]);
        }
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoadingAgenda(false);
      }
    },
    [adminToken, dateRange, filterApplied],
  );

  useFocusEffect(
    useCallback(() => {
      loadAgenda();
      const unsubscribe = subscribe("training_created", () => loadAgenda("silent"));
      const interval = setInterval(() => loadAgenda("silent"), FALLBACK_POLL_MS);
      return () => {
        unsubscribe();
        clearInterval(interval);
      };
    }, [loadAgenda]),
  );

  // Hardware/gesture back on this screen asks for confirmation instead of
  // leaving straight away - same popup and destination as the header's
  // power button. Only registered while this screen is actually focused,
  // so it doesn't swallow back-presses on other screens.
  useFocusEffect(
    useCallback(() => {
      const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
        setConfirmLogoutOpen(true);
        return true;
      });
      return () => subscription.remove();
    }, []),
  );

  const applyDateRange = (range: DateRange, preset: DatePreset) => {
    // Just update the filter and stay on the dashboard - the agenda/stats
    // re-fetch on their own because `loadAgenda`/`loadMonthAgenda` depend on
    // `dateRange`, which reruns the focus effect below while this screen is
    // still focused. This used to also navigate to `/sessions`, which took
    // the trainer off the dashboard before they could see the refreshed
    // stats there.
    setDateRange(range);
    setDatePreset(preset);
    setFilterApplied(true);
    setDateDropOpen(false);
  };

  const requestLogout = () => setConfirmLogoutOpen(true);

  const cancelLogout = () => setConfirmLogoutOpen(false);

  const confirmLogout = () => {
    setConfirmLogoutOpen(false);
    adminLogout();
    router.replace("/");
  };

  const handleLaunch = (conferenceUid: string) => {
    router.push({ pathname: "/session_dashboard", params: { conferenceUid } });
  };

  const closePanels = () => {
    setMenuOpen(false);
  };

  const handleBottomNavSelect = (tab: TrainerDashboardTab) => {
    setActiveTab(tab);
    if (tab === "home") {
      // Return to home view
    } else if (tab === "plan") {
      // Only carry the calendar range over if the trainer actually applied
      // one - otherwise `dateRange` is still just its "today" default, and
      // forwarding it would make the Sessions screen's "All" tab silently
      // show only today's sessions instead of everything.
      router.push(
        filterApplied
          ? {
              pathname: "/sessions",
              params: { start: toApiDate(dateRange.start), end: toApiDate(dateRange.end) },
            }
          : "/sessions",
      );
    } else if (tab === "profile") {
      router.push("/trainer_profile");
    } else if (tab === "more") {
      setMenuOpen(true);
    }
  };

  return {
    router,
    admin,
    activeTab,
    menuOpen,
    dateDropOpen,
    setDateDropOpen,
    datePreset,
    dateRange,
    loadingAgenda,
    refreshing,
    stats,
    recentCompleted,
    loadAgenda,
    applyDateRange,
    confirmLogoutOpen,
    requestLogout,
    cancelLogout,
    confirmLogout,
    handleLaunch,
    closePanels,
    handleBottomNavSelect,
  };
}
