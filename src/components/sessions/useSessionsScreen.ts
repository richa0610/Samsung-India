import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { EMPTY_ADMIN_FILTERS } from "@/api/adminFilters";
import { TrainingAgendaItem, fetchTrainingFacets, fetchTrainingsPage } from "@/api/training";
import { DashboardTab } from "@/components/trainer/dashboard/DashboardBottomNav";
import { useAuth } from "@/hooks/useAuth";
import { istToday, monthToTodayRange } from "@/utils";
import { DEFAULT_SESSION_FILTERS, SessionFilters, SessionTab } from "./sessionsUtils";

// Sessions arrive a page at a time: the server applies this trainer's authorization, the tab,
// search and filters, sorts them (live first, then upcoming soonest, then completed newest) and
// returns only the requested page. Scrolling near the end asks for the next one.
const PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 300;

type SelectOption = { label: string; value: string };

/** The later / earlier of two optional YYYY-MM-DD dates (strings compare correctly in this format). */
const laterOf = (a?: string, b?: string) => (a && b ? (a > b ? a : b) : a || b || "");
const earlierOf = (a?: string, b?: string) => (a && b ? (a < b ? a : b) : a || b || "");

const toOptions = (values: string[]): SelectOption[] =>
  values.filter((v) => v && v !== "Not Assigned").map((v) => ({ label: v, value: v }));

export function useSessionsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ start?: string; end?: string; tab?: string; status?: string }>();
  const { adminToken } = useAuth();

  // When arriving without explicit stats card date parameters (e.g. via Plan tab), the default
  // date filter is the 1st of this month to today in IST - like every trainer list.
  const defaultMonthRange = useMemo(() => monthToTodayRange(), []);
  const baseStart = params.start ?? defaultMonthRange.start;
  const baseEnd = params.end ?? defaultMonthRange.end;

  const initialTab: SessionTab = params.tab === "today" || params.tab === "completed" ? params.tab : "all";
  const [activeTab, setActiveTab] = useState<SessionTab>(initialTab);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(params.status);
  const [syncedStatusParam, setSyncedStatusParam] = useState(params.status);
  if (params.status !== syncedStatusParam) {
    setSyncedStatusParam(params.status);
    setStatusFilter(params.status);
  }

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [query, setQuery] = useState<string>("");
  const [filters, setFilters] = useState<SessionFilters>(DEFAULT_SESSION_FILTERS);
  const [sessions, setSessions] = useState<TrainingAgendaItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [locationOptions, setLocationOptions] = useState<SelectOption[]>([]);
  const [sessionTypeOptions, setSessionTypeOptions] = useState<SelectOption[]>([]);
  const [bottomTab, setBottomTab] = useState<DashboardTab>("plan");
  const [moreOpen, setMoreOpen] = useState(false);

  // Follow the `tab` route param when it changes (e.g. arriving from "View Reports"): adjusted
  // during render against the last value seen, rather than in an effect that renders twice.
  const [syncedTabParam, setSyncedTabParam] = useState(params.tab);
  if (params.tab !== syncedTabParam) {
    setSyncedTabParam(params.tab);
    if (params.tab === "today" || params.tab === "completed" || params.tab === "all") {
      setActiveTab(params.tab);
    }
  }

  // One request per pause in typing, not one per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setQuery(searchQuery.trim()), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const dateRangeSubtitle = useMemo(() => {
    const sDate = filters.fromDate || baseStart;
    const eDate = filters.toDate || baseEnd;
    let datePart = `${sDate} - ${eDate}`;
    if (sDate && eDate) {
      try {
        const s = new Date(sDate);
        const e = new Date(eDate);
        const sStr = `${String(s.getDate()).padStart(2, "0")} ${s.toLocaleDateString("en-GB", { month: "short" })}`;
        const eStr = `${String(e.getDate()).padStart(2, "0")} ${e.toLocaleDateString("en-GB", { month: "short" })}`;
        datePart = `${sStr} - ${eStr}`;
      } catch {
        // Fallback
      }
    }
    const effectiveStatus = activeTab === "completed" ? undefined : statusFilter;
    if (effectiveStatus && effectiveStatus !== "all" && effectiveStatus !== "total") {
      const capStatus = effectiveStatus.charAt(0).toUpperCase() + effectiveStatus.slice(1);
      return `${datePart} · ${capStatus}`;
    }
    return datePart;
  }, [baseStart, baseEnd, filters.fromDate, filters.toDate, activeTab, statusFilter]);

  // Everything that decides WHICH sessions are listed; a change starts again from page 1.
  // The date range is the screen's own range (from the dashboard or default month range) narrowed by the From/To filter.
  const listRequest = useMemo(() => {
    const today = istToday();
    const effectiveStatus = activeTab === "completed" ? ("completed" as const) : statusFilter;
    return {
      sort: "session" as const,
      limit: PAGE_SIZE,
      q: query,
      onDate: activeTab === "today" ? today : undefined,
      status: effectiveStatus,
      location: filters.location || undefined,
      filters: {
        ...EMPTY_ADMIN_FILTERS,
        start: filters.fromDate || baseStart,
        end: filters.toDate || baseEnd,
        trainingTypes: filters.sessionType ? [filters.sessionType] : [],
      },
    };
  }, [activeTab, statusFilter, query, filters, baseStart, baseEnd]);

  // Only the latest request may update the list - a slow reply for an old tab / search is dropped,
  // and aborted so it stops using the connection.
  const requestId = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  // Set synchronously, so two end-of-list events in one frame can't ask for the same page twice
  // (the `loadingMore` state only updates on the next render).
  const loadingMoreRef = useRef(false);
  useEffect(() => () => inFlight.current?.abort(), []);

  const loadSessions = useCallback(
    async (mode: "load" | "refresh" = "load") => {
      if (!adminToken) {
        setSessions([]);
        setLoading(false);
        return;
      }
      const id = ++requestId.current;
      inFlight.current?.abort();
      const controller = new AbortController();
      inFlight.current = controller;
      if (mode === "refresh") setRefreshing(true);
      else setLoading(true);
      try {
        const result = await fetchTrainingsPage(adminToken, { ...listRequest, page: 1, signal: controller.signal });
        if (id !== requestId.current) return;
        setSessions(result.items);
        setPage(1);
        setTotalPages(result.totalPages ?? 1);
      } catch {
        if (controller.signal.aborted) return; // superseded by a newer request
        if (id === requestId.current) {
          setSessions([]);
          setTotalPages(0);
        }
      } finally {
        if (id === requestId.current) {
          if (mode === "refresh") setRefreshing(false);
          else setLoading(false);
        }
      }
    },
    [adminToken, listRequest],
  );

  const loadMore = useCallback(async () => {
    if (!adminToken || loading || loadingMoreRef.current || page >= totalPages) return;
    const id = requestId.current;
    loadingMoreRef.current = true;
    setLoadingMore(true);
    try {
      const result = await fetchTrainingsPage(adminToken, { ...listRequest, page: page + 1 });
      if (id !== requestId.current) return;
      setSessions((current) => {
        const seen = new Set(current.map((s) => s.conferenceUid));
        return [...current, ...result.items.filter((s) => !seen.has(s.conferenceUid))];
      });
      setPage(page + 1);
      if (result.totalPages != null) setTotalPages(result.totalPages);
    } catch {
      // Keep what is already on screen; scrolling again retries.
    } finally {
      loadingMoreRef.current = false;
      setLoadingMore(false);
    }
  }, [adminToken, listRequest, loading, page, totalPages]);

  const loadFacets = useCallback(async () => {
    if (!adminToken) return;
    try {
      const facets = await fetchTrainingFacets(adminToken, { start: baseStart, end: baseEnd });
      setLocationOptions(toOptions(facets.trainingHubs));
      setSessionTypeOptions(toOptions(facets.trainingTypes));
    } catch {
      // The filters just offer no options until the next visit.
    }
  }, [adminToken, baseStart, baseEnd]);

  useFocusEffect(
    useCallback(() => {
      loadSessions();
    }, [loadSessions]),
  );

  useFocusEffect(
    useCallback(() => {
      loadFacets();
    }, [loadFacets]),
  );

  const handleFiltersChange = (patch: Partial<SessionFilters>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  };

  const handleLaunchSession = (conferenceUid: string) => {
    router.push({ pathname: "/session_dashboard", params: { conferenceUid } });
  };

  const handleReportSession = (conferenceUid: string) => {
    router.push({ pathname: "/session_dashboard", params: { conferenceUid } });
  };

  const handleSelectTab = (tab: SessionTab) => {
    setActiveTab(tab);
    setStatusFilter(undefined);
  };

  const handleBottomNavSelect = (tab: DashboardTab) => {
    setBottomTab(tab);
    if (tab === "home") {
      router.replace("/trainer_dashboard");
    } else if (tab === "plan") {
      if (params.start || params.end || params.status || params.tab) {
        router.replace("/sessions");
      } else {
        handleSelectTab("all");
      }
    } else if (tab === "today") {
      handleSelectTab("today");
    } else if (tab === "profile") {
      router.push("/trainer_profile");
    } else if (tab === "more") {
      setMoreOpen(true);
    }
  };

  const currentBottomTab: DashboardTab =
    bottomTab === "more" ? "more" : activeTab === "today" ? "today" : "plan";

  return {
    activeTab,
    setActiveTab: handleSelectTab,
    setSearchQuery,
    filters,
    handleFiltersChange,
    locationOptions,
    sessionTypeOptions,
    dateRangeSubtitle,
    loading,
    refreshing,
    loadSessions,
    // The server already filtered and sorted them - this is the list as shown.
    filteredSessions: sessions,
    loadMore,
    loadingMore,
    handleLaunchSession,
    handleReportSession,
    bottomTab: currentBottomTab,
    moreOpen,
    setMoreOpen,
    handleBottomNavSelect,
  };
}
