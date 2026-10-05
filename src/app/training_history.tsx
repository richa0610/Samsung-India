import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import {
  ActivityIndicator,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { TrainingDetailsTable, TrainingHistoryFilterBar, toTrainingRows } from "@/components/trainee/dashboard";
import { useTrainingHistory } from "@/hooks/useTrainingHistory";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

// Start loading the next page this far (px) before the bottom, so scrolling rarely has to wait.
const LOAD_MORE_THRESHOLD = 400;

export default function TrainingHistoryScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const {
    onBack,
    trainings,
    loading,
    refreshing,
    loadingMore,
    hasMore,
    loadMore,
    onRefresh,
    fromDate,
    toDate,
    setFromDate,
    setToDate,
    status,
    setStatus,
    cardLabel,
    clearCard,
    clearFilters,
    hasFilter,
    filterOpen,
    toggleFilter,
  } = useTrainingHistory();

  const handleScroll = ({ nativeEvent }: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { layoutMeasurement, contentOffset, contentSize } = nativeEvent;
    if (hasMore && layoutMeasurement.height + contentOffset.y >= contentSize.height - LOAD_MORE_THRESHOLD) {
      loadMore();
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScreenBanner backgroundColor={Colors.mainColour1} statusBarStyle="light" style={[styles.banner, { paddingTop: insets.top + 12 }]}>
        <View style={styles.bannerRow}>
          <Pressable onPress={onBack} hitSlop={8} accessibilityRole="button" accessibilityLabel="Back">
            <Ionicons name="arrow-back" size={18} color={Colors.white} />
          </Pressable>
          <View style={styles.bannerTextColumn}>
            <AppText style={styles.bannerTitle} color={Colors.white} weight={FontWeight.semiBold}>
              Training History
            </AppText>
            <AppText style={styles.bannerSubtitle} color={Colors.white}>
              {cardLabel ? `Your trainings: ${cardLabel}` : "All of your trainings"}
            </AppText>
          </View>
          {/* Opens / closes the filter panel - same as the trainer's Sessions header. */}
          <Pressable
            style={[styles.filterButton, filterOpen && styles.filterButtonActive]}
            onPress={toggleFilter}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel={filterOpen ? "Hide filters" : "Show filters"}
            accessibilityState={{ expanded: filterOpen }}
          >
            <Ionicons name="filter" size={17} color={Colors.white} />
            {/* Filters still apply while the panel is closed - the dot says so. */}
            {hasFilter && !filterOpen && <View style={styles.filterDot} testID="filters-applied-dot" />}
          </Pressable>
        </View>
      </ScreenBanner>

      {filterOpen && (
        <TrainingHistoryFilterBar
          fromDate={fromDate}
          toDate={toDate}
          onFromDateChange={setFromDate}
          onToDateChange={setToDate}
          status={status}
          onStatusChange={setStatus}
          cardLabel={cardLabel}
          onClearCard={clearCard}
          onClear={clearFilters}
          hasFilter={hasFilter}
        />
      )}

      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator color={Colors.mainColour1} size="large" />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.content}
          onScroll={handleScroll}
          scrollEventThrottle={200}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />}
        >
          <TrainingDetailsTable
            trainings={toTrainingRows(trainings)}
            onPressRow={(conferenceUid) => router.push({ pathname: "/training_detail", params: { conferenceUid } })}
          />
          {loadingMore && <ActivityIndicator color={Colors.mainColour1} style={styles.loadingMore} />}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  banner: { paddingBottom: 20 },
  bannerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  bannerTextColumn: { flex: 1 },
  filterButton: {
    width: 36,
    height: 36,
    borderRadius: 9,
    backgroundColor: "rgba(255, 255, 255, 0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  filterButtonActive: { backgroundColor: "rgba(255, 255, 255, 0.35)" },
  filterDot: {
    position: "absolute",
    top: 7,
    right: 7,
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: Colors.warning,
  },
  bannerTitle: { fontSize: 17 },
  bannerSubtitle: { fontSize: 12, opacity: 0.9, marginTop: 2 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { paddingBottom: 32 },
  loadingMore: { marginTop: 12 },
});
