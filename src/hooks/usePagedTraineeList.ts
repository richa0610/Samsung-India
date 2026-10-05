/**
 * usePagedTraineeList
 * The Trainee / Pending Trainee list, shown a page at a time like the Training and
 * Attendance lists. The server authorizes the rows (an admin's grant, or a trainer's
 * assigned / rostered trainees), counts, searches, sorts and pages them
 * (GET /admin/trainees/page), so the phone only ever holds the current page.
 * Any change to the registration date range, search text, sort or rows-per-page returns to page 1.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useFocusEffect } from "expo-router";

import { TraineeListItem, TraineeSortKey, fetchTraineesPage } from "@/api/trainee";
import { AdminFilterScope, useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import { PAGE_SIZE_OPTIONS } from "@/hooks/usePagedTrainingList";
import { subscribe } from "@/services/liveEvents";

export { PAGE_SIZE_OPTIONS };
const DEFAULT_PAGE_SIZE = 10;
const EXPORT_PAGE_SIZE = 200;

/** Table column key -> the server sort it maps to. Columns not listed can't be sorted. */
const SERVER_SORT_KEYS: Record<string, TraineeSortKey> = {
  status: "status",
  traineeUid: "traineeUid",
  name: "name",
  trainerName: "trainerName",
  supervisorName: "supervisorName",
  district: "district",
  updatedBy: "updatedBy",
  timestamp: "timestamp",
};

type SortState = { key: string; direction: "asc" | "desc" } | null;

export type PagedTraineeList = {
  items: TraineeListItem[];
  /** All rows matching the search (null until page 1 arrives). */
  total: number | null;
  loading: boolean;
  searching: boolean;
  refreshing: boolean;
  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (size: number) => void;
  refresh: () => void;
  search: string;
  setSearch: (value: string) => void;
  sort: SortState;
  toggleSort: (columnKey: string) => void;
  sortableKeys: ReadonlySet<string>;
  exportAll: () => Promise<TraineeListItem[]>;
};

/** `filterScope`'s date range narrows the list to trainees registered in it (the trainer's
 *  lists use "trainerLists"; only its From/To dates apply to trainees). */
export function usePagedTraineeList(pendingOnly: boolean, filterScope: AdminFilterScope = "lists"): PagedTraineeList {
  const { adminToken } = useAuth();
  const { applied } = useAdminFilters(filterScope);
  const mode: "all" | "pending" = pendingOnly ? "pending" : "all";

  const [items, setItems] = useState<TraineeListItem[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searching, setSearching] = useState(false);
  const loadedOnce = useRef(false);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortState>(null);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const sortKey = sort ? SERVER_SORT_KEYS[sort.key] : undefined;
  const sortDir = sort?.direction;

  const start = applied.start || undefined;
  const end = applied.end || undefined;
  const requestOptions = useMemo(
    () => ({ mode, q: search, sort: sortKey, dir: sortDir, limit: pageSize, start, end }),
    [mode, search, sortKey, sortDir, pageSize, start, end],
  );
  const listKey = useMemo(() => JSON.stringify(requestOptions), [requestOptions]);

  // The chosen page belongs to one list; for any other list it is page 1.
  const [chosenPage, setChosenPage] = useState({ listKey, page: 1 });
  const page = chosenPage.listKey === listKey ? chosenPage.page : 1;
  const setPage = useCallback((next: number) => setChosenPage({ listKey, page: Math.max(next, 1) }), [listKey]);

  // Only the latest request may update the screen - a slow reply for an old page or search is
  // dropped, and the older request is aborted so it stops using the connection.
  const requestId = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  useEffect(() => () => inFlight.current?.abort(), []);

  const loadPage = useCallback(
    async (loadMode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      const id = ++requestId.current;
      inFlight.current?.abort();
      const controller = new AbortController();
      inFlight.current = controller;
      if (loadMode === "refresh") setRefreshing(true);
      else if (loadMode === "load") {
        if (loadedOnce.current) setSearching(true);
        else setLoading(true);
      }
      try {
        const result = await fetchTraineesPage(adminToken, { ...requestOptions, page, signal: controller.signal });
        if (id !== requestId.current) return;
        setItems(result.items);
        // The server sends the total with page 1 only; keep it while paging.
        if (result.total != null) setTotal(result.total);
      } catch {
        if (controller.signal.aborted) return; // superseded by a newer request
        if (id === requestId.current && loadMode !== "silent") {
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
    [adminToken, requestOptions, page],
  );

  const exportAll = useCallback(async () => {
    if (!adminToken) return [];
    const rows: TraineeListItem[] = [];
    let cursor: string | null = null;
    do {
      const result = await fetchTraineesPage(adminToken, { ...requestOptions, cursor, limit: EXPORT_PAGE_SIZE });
      rows.push(...result.items);
      cursor = result.nextCursor;
    } while (cursor);
    return rows;
  }, [adminToken, requestOptions]);

  useFocusEffect(
    useCallback(() => {
      loadPage();
      const unsubscribe = subscribe("trainee_created", () => loadPage("silent"));
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
