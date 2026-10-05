/**
 * usePagedAttendanceList
 * The admin Attendance List / Pending Attendance / Confirmed Attendance, shown a page
 * at a time exactly like the Training List: "Show N rows", numbered pages, "Showing 1
 * to 10 of 121 entries". The server does the mode split, searching, sorting and paging
 * (GET /admin/attendance/page), so the phone only ever holds the current page. Any
 * change to the filter, search text, sort or rows-per-page returns to page 1.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useFocusEffect } from "expo-router";

import {
  ApiError,
  AttendanceListItem,
  AttendanceMode,
  AttendanceSortKey,
  fetchAttendancePage,
} from "@/api/attendanceList";
import { AdminFilterScope, useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import { subscribe } from "@/services/liveEvents";

export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 200];
const DEFAULT_PAGE_SIZE = 10;
const EXPORT_PAGE_SIZE = 200;

/** Table column key -> the server sort it maps to. Columns not listed can't be sorted. */
export const SERVER_SORT_KEYS: Record<string, AttendanceSortKey> = {
  region: "region",
  product: "product",
  session: "session",
  sessionTypeMethod: "session",
  audienceType: "audienceType",
  conferenceDate: "conferenceDate",
  trainerName: "trainerName",
  trainerHoId: "trainerHoId",
  participantHoId: "participantHoId",
  participantName: "participantName",
  phone: "phone",
  state: "state",
  reportingManagerOfPromoter: "reportingManagerOfPromoter",
  attendanceStatus: "attendanceStatus",
  checkIn: "checkIn",
  checkOut: "checkOut",
  attendanceId: "attendanceId",
  conferenceId: "conferenceId",
};

type SortState = { key: string; direction: "asc" | "desc" } | null;

export type PagedAttendanceList = {
  /** Just the current page's rows. */
  items: AttendanceListItem[];
  /** All rows matching the mode / filter / search (null until page 1 arrives). */
  total: number | null;
  /** True only until the very first page arrives - after that the table stays on screen. */
  loading: boolean;
  /** A new page / search / sort / filter is being fetched (the previous rows stay visible meanwhile). */
  searching: boolean;
  refreshing: boolean;
  /** Set when the last request failed; the previous rows stay on screen. */
  error: string | null;
  retry: () => void;
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
  /** Every matching row (all pages), fetched through the same authorised endpoint. */
  exportAll: () => Promise<AttendanceListItem[]>;
};

/** `filterScope` is whose filter applies: the admin lists' ("lists") or the trainer's ("trainerLists"). */
export function usePagedAttendanceList(mode: AttendanceMode, filterScope: AdminFilterScope = "lists"): PagedAttendanceList {
  const { adminToken } = useAuth();
  const { applied, appliedKey } = useAdminFilters(filterScope);

  const [items, setItems] = useState<AttendanceListItem[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  // Everything except the page number: when any of it changes we are looking at a
  // different list, so the page number starts again at 1.
  const requestOptions = useMemo(
    () => ({ mode, filters: applied, q: query, sort: sortKey, dir: sortDir, limit: pageSize }),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `appliedKey` is `applied`, serialised so an equal filter doesn't refetch
    [mode, appliedKey, query, sortKey, sortDir, pageSize],
  );
  const listKey = useMemo(
    () => JSON.stringify([mode, appliedKey, query, sortKey, sortDir, pageSize]),
    [mode, appliedKey, query, sortKey, sortDir, pageSize],
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
  const pageCache = useRef<{ listKey: string; pages: Map<number, AttendanceListItem[]> }>({ listKey, pages: new Map() });

  // A response only counts if it belongs to the latest request - a slow reply for an
  // old page or search must never overwrite the newer one. The older request is also
  // aborted, so it stops using the connection.
  const requestId = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  useEffect(() => () => inFlight.current?.abort(), []);

  const loadPage = useCallback(
    async (loadMode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      const id = ++requestId.current;
      if (pageCache.current.listKey !== listKey) pageCache.current = { listKey, pages: new Map() };
      const pages = pageCache.current.pages;
      inFlight.current?.abort();

      if (loadMode === "refresh") {
        pages.clear();
        setRefreshing(true);
      } else if (loadMode === "silent") {
        pages.clear();
      } else if (loadMode === "load") {
        const cached = pages.get(page);
        if (cached) {
          setItems(cached);
          setError(null);
          setLoading(false);
          setSearching(false);
          return;
        }

        // Blank the screen only for the very first load: swapping the table for a
        // spinner on every page / search would unmount the search box mid-typing.
        if (loadedOnce.current) setSearching(true);
        else setLoading(true);
      }

      const controller = new AbortController();
      inFlight.current = controller;
      try {
        // Only the page asked for: a next page is fetched when it is opened (then kept, so going
        // back to it is instant), never speculatively.
        const result = await fetchAttendancePage(adminToken, { ...requestOptions, page, signal: controller.signal });
        if (id !== requestId.current) return;
        pages.set(page, result.items);
        setItems(result.items);
        setError(null);
        // The server sends the total with page 1 only; keep it while paging.
        if (result.total != null) setTotal(result.total);
      } catch (err) {
        if (controller.signal.aborted || id !== requestId.current) return; // superseded by a newer request
        if (loadMode !== "silent") {
          setError(err instanceof ApiError ? err.message : "Couldn't load the attendance list.");
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
    const rows: AttendanceListItem[] = [];
    let cursor: string | null = null;
    do {
      const result = await fetchAttendancePage(adminToken, { ...requestOptions, cursor, limit: EXPORT_PAGE_SIZE });
      rows.push(...result.items);
      cursor = result.nextCursor;
    } while (cursor);
    return rows;
  }, [adminToken, requestOptions]);

  // Fetch when the screen is focused, when the page / filter / search / sort changes
  // (`loadPage` changes with them), and when attendance is marked over the live connection.
  useFocusEffect(
    useCallback(() => {
      loadPage();
      const unsubscribe = subscribe("attendance_marked", () => loadPage("silent"));
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
    error,
    retry: () => loadPage("load"),
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
