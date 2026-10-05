import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DashboardTrainingRow, TraineeMetricCard, getTrainingHistory } from "@/api/session";
import { TRAINEE_METRIC_LABELS } from "@/components/trainee/dashboard/TraineeMetricsGrid";
import { useAuth } from "@/hooks/useAuth";

// The history arrives a page at a time (newest first); scrolling near the end loads the next
// page. The date and status filters are applied by the server, so a filter starts again from
// page 1 and the list never holds more than the pages actually scrolled through.
const PAGE_SIZE = 20;

/** The Dashboard metric card this screen was opened from, if the param names a real one. */
function metricCardParam(value: string | undefined): TraineeMetricCard | null {
  return value && value !== "total" && Object.keys(TRAINEE_METRIC_LABELS).includes(value)
    ? (value as TraineeMetricCard)
    : null;
}

export function useTrainingHistory() {
  const router = useRouter();
  const { token } = useAuth();
  // Opened from a Dashboard metric card: that card's trainings over the Dashboard's date range.
  const params = useLocalSearchParams<{ card?: string; start?: string; end?: string }>();

  const [trainings, setTrainings] = useState<DashboardTrainingRow[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [fromDate, setFromDate] = useState(params.start ?? "");
  const [toDate, setToDate] = useState(params.end ?? "");
  const [status, setStatus] = useState("");
  const [card, setCard] = useState(() => metricCardParam(params.card));
  // The filter panel opens from the header's filter button. It starts closed - unless the screen
  // was opened already filtered (from a Dashboard card), so the trainee sees what's applied.
  const [filterOpen, setFilterOpen] = useState(() => !!(params.start || params.end || metricCardParam(params.card)));

  const filters = useMemo(
    () => ({
      start: fromDate || undefined,
      end: toDate || undefined,
      status: status || undefined,
      card: card ?? undefined,
    }),
    [fromDate, toDate, status, card],
  );

  // Only the latest request may update the list; an older one is aborted.
  const requestId = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  // Set synchronously, so two end-of-scroll events in one frame can't ask for the same page twice.
  const loadingMoreRef = useRef(false);
  useEffect(() => () => inFlight.current?.abort(), []);

  const load = useCallback(
    async (mode: "load" | "refresh" = "load") => {
      if (!token) return;
      const id = ++requestId.current;
      inFlight.current?.abort();
      const controller = new AbortController();
      inFlight.current = controller;
      if (mode === "refresh") setRefreshing(true);
      else setLoading(true);
      try {
        const result = await getTrainingHistory(token, { ...filters, page: 1, limit: PAGE_SIZE, signal: controller.signal });
        if (id !== requestId.current) return;
        setTrainings(result.items);
        setPage(1);
        setTotalPages(result.totalPages ?? 0);
      } catch {
        if (controller.signal.aborted || id !== requestId.current) return;
        setTrainings([]);
        setTotalPages(0);
      } finally {
        if (id === requestId.current) {
          if (mode === "refresh") setRefreshing(false);
          else setLoading(false);
        }
      }
    },
    [token, filters],
  );

  const loadMore = useCallback(async () => {
    if (!token || loading || loadingMoreRef.current || page >= totalPages) return;
    const id = requestId.current;
    loadingMoreRef.current = true;
    setLoadingMore(true);
    try {
      const result = await getTrainingHistory(token, { ...filters, page: page + 1, limit: PAGE_SIZE });
      if (id !== requestId.current) return; // the filters changed meanwhile
      setTrainings((current) => {
        const seen = new Set(current.map((row) => row.conferenceUid));
        return [...current, ...result.items.filter((row) => !seen.has(row.conferenceUid))];
      });
      setPage(page + 1);
      if (result.totalPages != null) setTotalPages(result.totalPages);
    } catch {
      // Keep what is on screen; scrolling again retries.
    } finally {
      loadingMoreRef.current = false;
      setLoadingMore(false);
    }
  }, [token, filters, loading, page, totalPages]);

  // On focus, and again (from page 1) whenever a filter changes (`load` changes with it).
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const clearFilters = () => {
    setFromDate("");
    setToDate("");
    setStatus("");
    setCard(null);
  };

  return {
    onBack: () => router.back(),
    trainings,
    loading,
    refreshing,
    loadingMore,
    hasMore: page < totalPages,
    loadMore,
    onRefresh: () => load("refresh"),
    fromDate,
    toDate,
    setFromDate,
    setToDate,
    status,
    setStatus,
    /** The Dashboard card's name while its filter is on (e.g. "Present"), else null. */
    cardLabel: card ? TRAINEE_METRIC_LABELS[card] : null,
    clearCard: () => setCard(null),
    clearFilters,
    filterOpen,
    toggleFilter: () => setFilterOpen((open) => !open),
    hasFilter: !!(fromDate || toDate || status || card),
  };
}
