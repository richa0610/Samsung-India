/**
 * usePagedTrainingList
 * The admin Training / Pending Training list, shown a page at a time exactly like
 * the Attendance List: "Show N rows", numbered pages, "Showing 1 to 10 of 132
 * entries". The server does the searching, sorting and paging
 * (GET /admin/trainings/page), so the phone only ever holds the current page.
 * Any change to the filter, search text, sort or rows-per-page returns to page 1.
 */

import { useCallback, useMemo, useRef, useState } from "react";
import { useFocusEffect } from "expo-router";

import { TrainingAgendaItem, TrainingSortKey, fetchTrainingsPage } from "@/api/training";
import { useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import { subscribe } from "@/services/liveEvents";

export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 200];
const DEFAULT_PAGE_SIZE = 10;
const EXPORT_PAGE_SIZE = 200;

/** Table column key -> the server sort it maps to. Columns not listed can't be sorted. */
export const SERVER_SORT_KEYS: Record<string, TrainingSortKey> = {
  trainingsId: "conferenceUid",
  status: "conferenceStatus",
  zone: "zone",
  trainerName: "trainerName",
  date: "conferenceDate",
  time: "conferenceTime",
  sessionType: "sessionType",
  trainingType: "trainingType",
  trainingHub: "trainingHub",
  state: "state",
  district: "district",
  timestamp: "timestamp",
};

type SortState = { key: string; direction: "asc" | "desc" } | null;

export type PagedTrainingList = {
  /** Just the current page's rows. */
  items: TrainingAgendaItem[];
  /** All rows matching the filter / search (null until page 1 arrives). */
  total: number | null;
  /** True only until the very first page arrives - after that the table stays on screen. */
  loading: boolean;
  /** A new page / search / sort / filter is being fetched (the previous rows stay visible meanwhile). */
  searching: boolean;
  refreshing: boolean;
  /** Current page (1-based) and rows per page - both sent to the server. */
  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (size: number) => void;
  refresh: () => void;
  search: string;
  setSearch: (value: string) => void;
  sort: SortState;
  /** asc -> desc -> back to the default order (newest first). */
  toggleSort: (columnKey: string) => void;
  sortableKeys: ReadonlySet<string>;
  /** Every matching row (all pages), for export / copy / print. */
  exportAll: () => Promise<TrainingAgendaItem[]>;
};

/** `otherwise` is the non-pending split: "reviewed" (admin - approved or rejected) or
 *  "approved" (a trainer's own Training List). The server scopes rows to the caller either way. */
export function usePagedTrainingList(
  pendingOnly: boolean,
  otherwise: "reviewed" | "approved" = "reviewed",
): PagedTrainingList {
  const { adminToken } = useAuth();
  const { applied, appliedKey } = useAdminFilters("lists");
  const approval: "pending" | "reviewed" | "approved" = pendingOnly ? "pending" : otherwise;

  const [items, setItems] = useState<TrainingAgendaItem[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searching, setSearching] = useState(false);
  const loadedOnce = useRef(false);

  const [search, setSearchState] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortState>(null);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const setSearch = useCallback((value: string) => {
    setSearchState(value);
    setQuery(value);
  }, []);

  const sortKey = sort ? SERVER_SORT_KEYS[sort.key] : undefined;
  const sortDir = sort?.direction;

  // Everything except the page number: when any of it changes we are looking at
  // a different list, so the page number starts again at 1.
  const requestOptions = useMemo(
    () => ({ approval, filters: applied, q: query, sort: sortKey, dir: sortDir, limit: pageSize }),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `appliedKey` is `applied`, serialised so an equal filter doesn't refetch
    [approval, appliedKey, query, sortKey, sortDir, pageSize],
  );
  const listKey = useMemo(
    () => JSON.stringify([approval, appliedKey, query, sortKey, sortDir, pageSize]),
    [approval, appliedKey, query, sortKey, sortDir, pageSize],
  );

  // The chosen page belongs to one list; for any other list it is page 1. Derived
  // rather than reset in an effect, so a change fetches once (page 1), not twice.
  const [chosenPage, setChosenPage] = useState({ listKey, page: 1 });
  const page = chosenPage.listKey === listKey ? chosenPage.page : 1;
  const setPage = useCallback((next: number) => setChosenPage({ listKey, page: Math.max(next, 1) }), [listKey]);

  // In-memory cache of downloaded pages for the current listKey (filter/search/sort/pageSize).
  // Going back to an already-visited page (e.g. page 2 -> page 1) renders instantly from
  // memory with zero loading overlay or network delay.
  // The cache remembers which list it belongs to and is swapped for an empty one by the loader
  // (never during render) the first time a different list is requested.
  const pageCache = useRef<{ listKey: string; pages: Map<number, TrainingAgendaItem[]> }>({ listKey, pages: new Map() });

  // A response only counts if it belongs to the latest request - a slow reply for
  // an old page or search must never overwrite the newer one.
  const requestId = useRef(0);

  const loadPage = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      const id = ++requestId.current;
      if (pageCache.current.listKey !== listKey) pageCache.current = { listKey, pages: new Map() };
      const pages = pageCache.current.pages;
      if (mode === "refresh") {
        pages.clear();
        setRefreshing(true);
      } else if (mode === "silent") {
        pages.clear();
      } else if (mode === "load") {
        const cached = pages.get(page);
        if (cached) {
          setItems(cached);
          setLoading(false);
          setSearching(false);
          return;
        }

        // Blank the screen only for the very first load: swapping the table for a
        // spinner on every page / search would unmount the search box mid-typing.
        if (loadedOnce.current) setSearching(true);
        else setLoading(true);
      }
      try {
        const result = await fetchTrainingsPage(adminToken, { ...requestOptions, page });
        if (id !== requestId.current) return;
        pages.set(page, result.items);
        setItems(result.items);
        // The server sends the total with page 1 only; keep it while paging.
        if (result.total != null) setTotal(result.total);

        // Silently pre-fetch the next page in background so tapping 'Next' renders instantly (0ms)
        const nextPage = page + 1;
        if (!pages.has(nextPage)) {
          fetchTrainingsPage(adminToken, { ...requestOptions, page: nextPage })
            .then((nextResult) => {
              if (id === requestId.current && nextResult.items.length > 0) {
                pages.set(nextPage, nextResult.items);
              }
            })
            .catch(() => {});
        }
      } catch {
        if (id === requestId.current && mode !== "silent") {
          setItems([]);
          setTotal(0);
        }
      } finally {
        if (id === requestId.current) {
          loadedOnce.current = true;
          setLoading(false);
          setSearching(false);
          setRefreshing(false);
        }
      }
    },
    [adminToken, requestOptions, page, listKey],
  );

  const exportAll = useCallback(async () => {
    if (!adminToken) return [];
    const rows: TrainingAgendaItem[] = [];
    let cursor: string | null = null;
    do {
      const result = await fetchTrainingsPage(adminToken, { ...requestOptions, cursor, limit: EXPORT_PAGE_SIZE });
      rows.push(...result.items);
      cursor = result.nextCursor;
    } while (cursor);
    return rows;
  }, [adminToken, requestOptions]);

  // Fetch when the screen is focused, when the page / filter / search / sort
  // changes (`loadPage` changes with them), and when a new training arrives over
  // the live connection.
  useFocusEffect(
    useCallback(() => {
      loadPage();
      const unsubscribe = subscribe("training_created", () => loadPage("silent"));
      return unsubscribe;
    }, [loadPage]),
  );

  const toggleSort = useCallback((columnKey: string) => {
    setSort((prev) => {
      if (!prev || prev.key !== columnKey) return { key: columnKey, direction: "asc" };
      if (prev.direction === "asc") return { key: columnKey, direction: "desc" };
      return null;
    });
  }, []);

  const sortableKeys = useMemo(() => new Set(Object.keys(SERVER_SORT_KEYS)), []);

  return {
    items,
    total,
    loading,
    searching,
    refreshing,
    page,
    setPage,
    pageSize,
    setPageSize,
    refresh: () => loadPage("refresh"),
    search,
    setSearch,
    sort,
    toggleSort,
    sortableKeys,
    exportAll,
  };
}
