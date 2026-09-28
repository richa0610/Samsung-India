import { ReactNode } from "react";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import { DataTable, DataTableColumn, DataTableServerMode } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { AttendanceListItem } from "@/api/attendanceList";
import { PAGE_SIZE_OPTIONS, type PagedAttendanceList } from "@/hooks/usePagedAttendanceList";
import { useAttendanceListColumns } from "./attendance-list/useAttendanceListColumns";

type AttendanceListViewProps = {
  title: string;
  subtitle: string;
  items: AttendanceListItem[];
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  onBack: () => void;
  exportFileName: string;
  emptyLabel: string;
  /** Overrides the default (trainer) columns - e.g. the admin's org-wide table. */
  columns?: DataTableColumn<AttendanceListItem>[];
  /** A bottom nav sits below this screen and already clears the safe area - don't reserve it twice. */
  hasBottomNav?: boolean;
  /** Rendered at the top of the scrolling card - the admin filter bar. */
  topContent?: ReactNode;
  /** Server-driven mode (admin): the list loads a page at a time and the server searches / sorts.
   *  Omitted for the trainer's own screens, which keep loading everything at once. */
  paged?: PagedAttendanceList;
};

export function AttendanceListView({
  title,
  subtitle,
  items,
  loading,
  refreshing,
  onRefresh,
  onBack,
  exportFileName,
  emptyLabel,
  columns: customColumns,
  hasBottomNav = false,
  topContent,
  paged,
}: AttendanceListViewProps) {
  const insets = useSafeAreaInsets();
  const defaultColumns = useAttendanceListColumns();
  const columns = customColumns ?? defaultColumns;

  const server: DataTableServerMode<AttendanceListItem> | undefined = paged && {
    total: paged.total,
    page: paged.page,
    onPageChange: paged.setPage,
    pageSize: paged.pageSize,
    pageSizeOptions: PAGE_SIZE_OPTIONS,
    onPageSizeChange: paged.setPageSize,
    search: paged.search,
    onSearchChange: paged.setSearch,
    sort: paged.sort,
    onSortChange: paged.toggleSort,
    sortableKeys: paged.sortableKeys,
    onExportAll: paged.exportAll,
  };

  return (
    <SafeAreaView style={styles.container} edges={hasBottomNav ? [] : ["bottom"]}>
      <ScreenBanner backgroundColor={Colors.mainColour1} style={[styles.banner, { paddingTop: insets.top + 12 }]}>
        <View style={styles.bannerRow}>
          <Pressable onPress={onBack} hitSlop={8}>
            <Ionicons name="arrow-back" size={18} color={Colors.white} />
          </Pressable>
          <View>
            <AppText style={styles.bannerTitle} color={Colors.white} weight={FontWeight.semiBold}>{title}</AppText>
            <AppText style={styles.bannerSubtitle} color={Colors.white}>{subtitle}</AppText>
          </View>
        </View>
      </ScreenBanner>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />}
      >
        {topContent}
        {paged?.error && (
          <View style={styles.errorBox}>
            <AppText style={styles.errorText} color={Colors.danger}>{paged.error}</AppText>
            <Pressable style={styles.retryButton} onPress={paged.retry} accessibilityRole="button">
              <AppText style={styles.retryText} color={Colors.white} weight={FontWeight.semiBold}>Retry</AppText>
            </Pressable>
          </View>
        )}
        {loading ? (
          // Paged (admin) lists show the screen-centred loader below instead.
          paged ? null : (
            <View style={styles.centered}>
              <ActivityIndicator color={Colors.mainColour1} />
            </View>
          )
        ) : (
          <>
            <View style={paged ? [styles.tableWrap, paged.searching && styles.searching] : undefined}>
              <DataTable
                title={title}
                columns={columns}
                data={items}
                keyExtractor={(row) => row.attendanceId}
                exportFileName={exportFileName}
                server={server}
                searchPlaceholder="Search..."
                emptyLabel={emptyLabel}
              />
            </View>
            <View style={styles.secureFooter}>
              <Ionicons name="lock-closed" size={12} color={Colors.gray400} />
              <AppText style={styles.secureFooterText} color={Colors.gray400}>Your information is secure</AppText>
            </View>
          </>
        )}
      </ScrollView>

      {/* Loader in the middle of the SCREEN (not the scrolling page): first load, and while a
          new page / search / sort / rows-per-page is fetched - the old rows stay dimmed
          underneath and the table stays mounted so the search box keeps focus. */}
      {paged && (loading || paged.searching) && (
        <View style={styles.loadingOverlay} pointerEvents="none">
          <View style={styles.loadingPill}>
            <ActivityIndicator size="small" color={Colors.mainColour1} />
            <AppText style={styles.loadingText} color={Colors.gray600}>Loading...</AppText>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },

  banner: { paddingBottom: 70 },
  bannerRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  bannerTitle: { fontSize: Fonts.h3 },
  bannerSubtitle: { fontSize: Fonts.overline, marginTop: 2, opacity: 0.9 },

  scroll: { marginTop: -50, zIndex: 1, elevation: 1 },
  content: { paddingHorizontal: 8, paddingVertical: 16, flexGrow: 1 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", paddingVertical: 60 },
  // Grows to fill the screen, so with only a few rows the card still reaches the bottom.
  tableWrap: { flex: 1 },
  searching: { opacity: 0.55 },
  loadingText: { fontSize: Fonts.bodySm },
  loadingOverlay: { ...StyleSheet.absoluteFill, alignItems: "center", justifyContent: "center" },
  loadingPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.white,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
    backgroundColor: Colors.dangerBgSoft,
    borderRadius: 10,
    padding: 10,
    marginBottom: 8,
  },
  errorText: { flex: 1, fontSize: Fonts.bodySm },
  retryButton: { backgroundColor: Colors.mainColour1, borderRadius: 8, paddingHorizontal: 14, paddingVertical: 6 },
  retryText: { fontSize: Fonts.bodySm },

  secureFooter: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, paddingVertical: 10 },
  secureFooterText: { fontSize: Fonts.overline },
});
