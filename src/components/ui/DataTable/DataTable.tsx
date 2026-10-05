import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Animated, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import {
  copyTableToClipboard,
  exportTableAsCsv,
  exportTableAsExcel,
  exportTableAsPdf,
  printTable,
} from "@/services/exportService";
import DataTableToolbar from "./DataTableToolbar";
import Pagination from "./Pagination";
import { DataTableColumn, DataTablePageSize, DataTableServerMode, DataTableToolbarVariant, ExportAction } from "./types";

const DEFAULT_PAGE_SIZE_OPTIONS: DataTablePageSize[] = [10, 25, 50, 100, "all"];
// Row-slot count to fall back on for an empty table when pageSize is "all" (no
// natural page length to match), so the empty state's height still matches a
// typical filled page instead of collapsing to just the header row.
const FALLBACK_EMPTY_ROW_COUNT = 10;

// Blank / placeholder values read as an explicit "NOT AVAILABLE" instead of an
// empty cell or a stray dash.
function displayCellText(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  return text === "" || text === "--" || text === "-" ? "NOT AVAILABLE" : text;
}

function cellValue<T>(column: DataTableColumn<T>, row: T) {
  return column.searchValue ? column.searchValue(row) : column.exportValue ? column.exportValue(row, 0) : "";
}

function TableSkeletonRows<T>({
  count,
  columns,
}: {
  count: number;
  columns: DataTableColumn<T>[];
}) {
  // One Animated.Value for the component's lifetime (useState's initializer runs once).
  const [pulse] = useState(() => new Animated.Value(0.35));

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 0.85,
          duration: 650,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 0.35,
          duration: 650,
          useNativeDriver: true,
        }),
      ]),
    );
    anim.start();
    return () => anim.stop();
  }, [pulse]);

  return (
    <>
      {Array.from({ length: count }).map((_, rowIndex) => (
        <View key={`skeleton-row-${rowIndex}`} style={styles.bodyRow}>
          {columns.map((column, colIndex) => {
            const width = column.minWidth ?? 85;
            const barWidth =
              column.key === "slNo"
                ? 24
                : column.key === "action"
                  ? 26
                  : column.key === "currentReport"
                    ? 110
                    : column.key === "status"
                      ? 74
                      : Math.max(35, Math.min(width - 24, 70 + (colIndex % 3) * 15));
            const barHeight = column.key === "action" ? 24 : 14;
            const barRadius = column.key === "action" ? Radius.md : 999;

            return (
              <View key={column.key} style={[styles.bodyCell, { width }]}>
                <Animated.View
                  style={[
                    styles.skeletonBar,
                    {
                      width: barWidth,
                      height: barHeight,
                      borderRadius: barRadius,
                      opacity: pulse,
                    },
                  ]}
                />
              </View>
            );
          })}
        </View>
      ))}
    </>
  );
}

type DataTableProps<T> = {
  title: string;
  columns: DataTableColumn<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string;
  exportFileName?: string;
  searchPlaceholder?: string;
  pageSizeOptions?: DataTablePageSize[];
  defaultPageSize?: DataTablePageSize;
  emptyLabel?: string;
  toolbarVariant?: DataTableToolbarVariant;
  headerBackgroundColor?: string;
  headerTextColor?: string;
  /** When true, renders animated skeleton placeholder rows instead of old or blank rows. */
  loading?: boolean;
  /** Server-driven mode (see DataTableServerMode) - search, sort, paging and export all go through the server. */
  server?: DataTableServerMode<T>;
};

export default function DataTable<T>({
  title,
  columns,
  data,
  keyExtractor,
  exportFileName = "export",
  searchPlaceholder = "Search...",
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
  defaultPageSize = 10,
  emptyLabel = "No results available.",
  toolbarVariant = "full",
  headerBackgroundColor,
  headerTextColor,
  loading,
  server,
}: DataTableProps<T>) {
  const isBusy = Boolean(loading || server?.loading);
  const [search, setSearch] = useState("");
  const [pageSize, setPageSize] = useState<DataTablePageSize>(defaultPageSize);
  const [page, setPage] = useState(1);
  const [hiddenColumns, setHiddenColumns] = useState<Set<string>>(new Set());
  const [busyAction, setBusyAction] = useState<ExportAction | null>(null);
  const [sort, setSort] = useState<{ key: string; direction: "asc" | "desc" } | null>(null);

  const visibleColumns = useMemo(
    () => columns.filter((column) => !hiddenColumns.has(column.key)),
    [columns, hiddenColumns]
  );

  // In server mode the rows arrive already searched and sorted, and are all shown
  // (they're loaded in pages of their own), so none of the client-side work applies.
  const activeSort = server ? server.sort : sort;
  const pageSizeValue: DataTablePageSize = server ? server.pageSize : pageSize;

  const searchedData = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (server || !query) return data;
    return data.filter((row) => visibleColumns.some((column) => cellValue(column, row).toLowerCase().includes(query)));
  }, [data, search, server, visibleColumns]);

  const filteredData = useMemo(() => {
    if (server || !sort) return searchedData;
    const column = visibleColumns.find((c) => c.key === sort.key);
    if (!column) return searchedData;
    const withValue = searchedData.map((row) => ({ row, value: cellValue(column, row) }));
    withValue.sort((a, b) => {
      const numA = Number(a.value);
      const numB = Number(b.value);
      const comparison =
        a.value !== "" && b.value !== "" && !Number.isNaN(numA) && !Number.isNaN(numB)
          ? numA - numB
          : a.value.localeCompare(b.value);
      return sort.direction === "asc" ? comparison : -comparison;
    });
    return withValue.map((entry) => entry.row);
  }, [searchedData, server, sort, visibleColumns]);

  const toggleSort = (key: string) => {
    if (server) {
      server.onSortChange(key);
      return;
    }
    setSort((prev) => {
      if (!prev || prev.key !== key) return { key, direction: "asc" };
      if (prev.direction === "asc") return { key, direction: "desc" };
      return null;
    });
    setPage(1);
  };

  // Server mode: `data` is already just the current page, so the count and the
  // range come from the server's total instead of slicing the array.
  const totalRows = server ? (server.total ?? data.length) : filteredData.length;
  const pageCount = pageSizeValue === "all" ? 1 : Math.max(Math.ceil(totalRows / pageSizeValue), 1);
  const currentPage = server ? server.page : Math.min(page, pageCount);

  const pagedData = useMemo(() => {
    if (server || pageSizeValue === "all") return filteredData;
    const start = (currentPage - 1) * pageSizeValue;
    return filteredData.slice(start, start + pageSizeValue);
  }, [filteredData, server, pageSizeValue, currentPage]);

  const toExportRows = (rows: T[]) =>
    rows.map((row, index) => {
      const record: Record<string, unknown> = {};
      visibleColumns.forEach((column) => {
        record[column.key] = column.exportValue ? column.exportValue(row, index) : "";
      });
      return record;
    });

  // Rows to export: what's on screen, or - in server mode - every matching row
  // fetched from the server (the table itself only holds the pages loaded so far).
  const exportRowsNow = async () => toExportRows(server ? await server.onExportAll() : filteredData);

  const exportColumns = visibleColumns.map((column) => ({ key: column.key, header: column.header }));

  const runExport = async (action: ExportAction, task: () => Promise<void>) => {
    if (busyAction) return;
    setBusyAction(action);
    try {
      await task();
    } catch {
      // best-effort export - the share/print sheet is the user's retry surface
    } finally {
      setBusyAction(null);
    }
  };

  const toggleColumn = (key: string) => {
    setHiddenColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
    setPage(1);
  };

  return (
    <View style={styles.container}>
      <View style={styles.panelCard}>
        <View style={styles.toolbarWrap}>
          {toolbarVariant === "download" ? (
            <View style={styles.downloadToolbar}>
              <AppText style={styles.downloadTitle} weight={FontWeight.semiBold}>{title}</AppText>
              <Pressable
                style={styles.downloadBtn}
                onPress={() => runExport("excel", async () => exportTableAsExcel(exportColumns, await exportRowsNow(), exportFileName))}
                disabled={busyAction === "excel"}
              >
                {busyAction === "excel" ? (
                  <ActivityIndicator size="small" color={Colors.white} />
                ) : (
                  <Ionicons name="download-outline" size={15} color={Colors.white} />
                )}
                <AppText style={styles.downloadBtnText} color={Colors.white} weight={FontWeight.semiBold}>
                  Download Report
                </AppText>
              </Pressable>
            </View>
          ) : (
            <DataTableToolbar
              pageSize={server ? server.pageSize : pageSize}
              pageSizeOptions={server ? server.pageSizeOptions : pageSizeOptions}
              onPageSizeChange={(size) => {
                if (server) {
                  if (typeof size === "number") server.onPageSizeChange(size);
                  return;
                }
                setPageSize(size);
                setPage(1);
              }}
              search={server ? server.search : search}
              onSearchChange={(value) => {
                if (server) {
                  server.onSearchChange(value);
                  return;
                }
                setSearch(value);
                setPage(1);
              }}
              searchPlaceholder={searchPlaceholder}
              columns={columns.map((column) => ({ key: column.key, header: column.header }))}
              hiddenColumns={hiddenColumns}
              onToggleColumn={toggleColumn}
              onCopy={() => runExport("copy", async () => copyTableToClipboard(exportColumns, await exportRowsNow()))}
              onExportCsv={() => runExport("csv", async () => exportTableAsCsv(exportColumns, await exportRowsNow(), exportFileName))}
              onExportExcel={() => runExport("excel", async () => exportTableAsExcel(exportColumns, await exportRowsNow(), exportFileName))}
              onExportPdf={() => runExport("pdf", async () => exportTableAsPdf(title, exportColumns, await exportRowsNow(), exportFileName))}
              onPrint={() => runExport("print", async () => printTable(title, exportColumns, await exportRowsNow()))}
              busyAction={busyAction}
              searchLoading={isBusy}
            />
          )}
        </View>

        <View style={styles.tableBox}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator
            style={styles.tableScroll}
            contentContainerStyle={styles.tableScrollContent}
          >
            <View style={styles.tableInner}>
              <View style={[styles.headerRow, headerBackgroundColor ? { backgroundColor: headerBackgroundColor } : null]}>
                {visibleColumns.map((column) => {
                  const isSortable = column.sortable !== false && (!server || server.sortableKeys.has(column.key));
                  const isActive = activeSort?.key === column.key;
                  const headerColor = headerTextColor ?? (isActive ? Colors.mainColour1 : Colors.gray600);
                  return (
                    <Pressable
                      key={column.key}
                      style={[styles.headerCell, { width: column.minWidth ?? 85 }]}
                      onPress={isSortable ? () => toggleSort(column.key) : undefined}
                      disabled={!isSortable}
                    >
                      <AppText
                        style={styles.headerCellText}
                        color={headerColor}
                        weight={FontWeight.semiBold}
                        numberOfLines={1}
                      >
                        {column.header}
                      </AppText>
                    </Pressable>
                  );
                })}
              </View>

              {/* Row-slot count is pinned to pageSize (or a fallback for "all") and
                  padded with blank filler rows regardless of whether there's real
                  data, so an empty table renders the exact same height as a filled
                  one instead of collapsing to just the header row. */}
              <View style={styles.rowsArea}>
                {isBusy ? (
                  <TableSkeletonRows
                    count={pageSizeValue === "all" ? FALLBACK_EMPTY_ROW_COUNT : pageSizeValue}
                    columns={visibleColumns}
                  />
                ) : (
                  <>
                    {pagedData.map((row, localIndex) => {
                      const absoluteIndex = (pageSizeValue === "all" ? 0 : (currentPage - 1) * pageSizeValue) + localIndex;
                      return (
                        <View key={keyExtractor(row, absoluteIndex)} style={styles.bodyRow}>
                          {visibleColumns.map((column) => (
                            <View key={column.key} style={[styles.bodyCell, { width: column.minWidth ?? 85 }]}>
                              {column.render ? (
                                column.render(row, absoluteIndex)
                              ) : (
                                <AppText style={styles.bodyCellText}>
                                  {displayCellText(column.exportValue ? column.exportValue(row, absoluteIndex) : "")}
                                </AppText>
                              )}
                            </View>
                          ))}
                        </View>
                      );
                    })}

                    {Array.from({
                      length: Math.max(
                        0,
                        (pageSizeValue === "all" ? FALLBACK_EMPTY_ROW_COUNT : pageSizeValue) - pagedData.length
                      ),
                    }).map((_, index) => (
                      <View key={`filler-${index}`} style={styles.bodyRow}>
                        {visibleColumns.map((column) => (
                          <View key={column.key} style={[styles.bodyCell, { width: column.minWidth ?? 85 }]} />
                        ))}
                      </View>
                    ))}
                  </>
                )}
              </View>
            </View>
          </ScrollView>

          {pagedData.length === 0 && !isBusy && (
            <View style={styles.emptyOverlay} pointerEvents="none">
              <View style={styles.emptyPill}>
                <Ionicons name="file-tray-outline" size={26} color={Colors.gray300} />
                <AppText style={styles.emptyText} color={Colors.gray500}>{emptyLabel}</AppText>
              </View>
            </View>
          )}
        </View>

        <View style={styles.paginationWrap}>
          <Pagination
            page={currentPage}
            pageCount={pageCount}
            totalRows={totalRows}
            rangeStart={totalRows === 0 ? 0 : pageSizeValue === "all" ? 1 : (currentPage - 1) * (pageSizeValue as number) + 1}
            rangeEnd={pageSizeValue === "all" ? totalRows : Math.min(currentPage * (pageSizeValue as number), totalRows)}
            onPageChange={server ? server.onPageChange : setPage}
          />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, flexGrow: 1 },
  panelCard: {
    flex: 1,
    flexGrow: 1,
    backgroundColor: Colors.white,
    borderRadius: Radius.xl,
    ...Shadows.card,
    overflow: "hidden",
  },
  toolbarWrap: { padding: 12, paddingBottom: 4 },
  downloadToolbar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    paddingBottom: 8,
  },
  downloadTitle: { fontSize: Fonts.bodySm, flexShrink: 1 },
  downloadBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
    backgroundColor: Colors.mainColour1,
    borderRadius: Radius.md,
    paddingHorizontal: 4,
    height: 25,
  },
  downloadBtnText: { fontSize: Fonts.bodySm ,flexShrink: 1,alignSelf: "center",justifyContent: "center" },
  tableBox: {
    flex: 1,
    flexGrow: 1,
    marginHorizontal: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.lg,
    overflow: "hidden",
  },
  paginationWrap: {
    padding: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.gray100,
  },
  tableScroll: { flex: 1 },
  tableScrollContent: { flexGrow: 1, minHeight: "100%" },
  tableInner: { flex: 1, minWidth: "100%", minHeight: "100%" },
  headerRow: {
    flexDirection: "row",
    backgroundColor: "rgba(198, 198, 198, 0.2)",
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray200,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 38,
  },
  headerCell: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
    paddingVertical: 8,
    minHeight: 38,
  },
  headerCellText: { fontSize: 9, letterSpacing: 0.2, textAlign: "center" },
  bodyRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray100,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 38,
  },
  bodyCell: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
    paddingVertical: 5,
    minHeight: 38,
  },
  bodyCellText: { fontSize: Fonts.overline, textAlign: "center" },
  rowsArea: { position: "relative", flex: 1, flexGrow: 1 },
  emptyOverlay: {
    position: "absolute",
    top: 38,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    zIndex: 2,
  },
  emptyPill: {
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: "rgba(255, 255, 255, 0.92)",
    borderRadius: Radius.md,
    maxWidth: "85%",
  },
  emptyText: { fontSize: Fonts.bodySm, textAlign: "center" },
  skeletonBar: {
    backgroundColor: Colors.gray200,
  },
});
