import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { EMPTY_ADMIN_FILTERS } from "@/api/adminFilters";
import { TrainingAgendaItem, fetchTrainingFacets, fetchTrainingsPage } from "@/api/training";
import { DashboardTab } from "@/components/trainer/dashboard/DashboardBottomNav";
import { useAuth } from "@/hooks/useAuth";
import { formatMonthToToday } from "@/utils";
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
  const params = useLocalSearchParams<{ start?: string; end?: string; tab?: string }>();
  const { adminToken } = useAuth();

  const initialTab: SessionTab = params.tab === "today" || params.tab === "completed" ? params.tab : "all";
  const [activeTab, setActiveTab] = useState<SessionTab>(initialTab);
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
    if (params.start && params.end) {
      try {
        const s = new Date(params.start);
        const e = new Date(params.end);
        const sStr = `${String(s.getDate()).padStart(2, "0")} ${s.toLocaleDateString("en-GB", { month: "short" })}`;
        const eStr = `${String(e.getDate()).padStart(2, "0")} ${e.toLocaleDateString("en-GB", { month: "short" })}`;
        return `${sStr} - ${eStr}`;
      } catch {
        // Fallback
      }
    }
    return formatMonthToToday();
  }, [params.start, params.end]);

  // Everything that decides WHICH sessions are listed; a change starts again from page 1.
  // The date range is the screen's own range (from the dashboard) narrowed by the From/To filter.
  const listRequest = useMemo(() => {
    const today = new Date().toISOString().split("T")[0];
    return {
      sort: "session" as const,
      limit: PAGE_SIZE,
      q: query,
      onDate: activeTab === "today" ? today : undefined,
      status: activeTab === "completed" ? ("completed" as const) : undefined,
      location: filters.location || undefined,
      filters: {
        ...EMPTY_ADMIN_FILTERS,
        start: laterOf(params.start, filters.fromDate),
        end: earlierOf(params.end, filters.toDate),
        trainingTypes: filters.sessionType ? [filters.sessionType] : [],
      },
    };
  }, [activeTab, query, filters, params.start, params.end]);

  // Only the latest request may update the list - a slow reply for an old tab / search is dropped.
  const requestId = useRef(0);

  const loadSessions = useCallback(
    async (mode: "load" | "refresh" = "load") => {
      if (!adminToken) {
        setSessions([]);
        setLoading(false);
        return;
      }
      const id = ++requestId.current;
      if (mode === "refresh") setRefreshing(true);
      else setLoading(true);
      try {
        const result = await fetchTrainingsPage(adminToken, { ...listRequest, page: 1 });
        if (id !== requestId.current) return;
        setSessions(result.items);
        setPage(1);
        setTotalPages(result.totalPages ?? 1);
      } catch {
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
    if (!adminToken || loading || loadingMore || page >= totalPages) return;
    const id = requestId.current;
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
      setLoadingMore(false);
    }
  }, [adminToken, listRequest, loading, loadingMore, page, totalPages]);

  const loadFacets = useCallback(async () => {
    if (!adminToken) return;
    try {
      const facets = await fetchTrainingFacets(adminToken, { start: params.start, end: params.end });
      setLocationOptions(toOptions(facets.trainingHubs));
      setSessionTypeOptions(toOptions(facets.trainingTypes));
    } catch {
      // The filters just offer no options until the next visit.
    }
  }, [adminToken, params.start, params.end]);

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

  const handleBottomNavSelect = (tab: DashboardTab) => {
    setBottomTab(tab);
    if (tab === "home") {
      router.replace("/trainer_dashboard");
    } else if (tab === "plan") {
      setActiveTab("all");
    } else if (tab === "today") {
      setActiveTab("today");
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
    setActiveTab,
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
