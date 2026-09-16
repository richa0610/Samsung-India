import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { TrainingDetailsTable, TrainingHistoryFilterBar, toTrainingRows } from "@/components/trainee/dashboard";
import { useTrainingHistory } from "@/hooks/useTrainingHistory";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export default function TrainingHistoryScreen() {
  const insets = useSafeAreaInsets();
  const {
    onBack,
    trainings,
    loading,
    refreshing,
    onRefresh,
    fromDate,
    toDate,
    setFromDate,
    setToDate,
    clearFilters,
    hasFilter,
  } = useTrainingHistory();

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScreenBanner backgroundColor={Colors.mainColour1} statusBarStyle="light" style={[styles.banner, { paddingTop: insets.top + 12 }]}>
        <View style={styles.bannerRow}>
          <Pressable onPress={onBack} hitSlop={8} accessibilityRole="button" accessibilityLabel="Back">
            <Ionicons name="arrow-back" size={18} color={Colors.white} />
          </Pressable>
          <View>
            <AppText style={styles.bannerTitle} color={Colors.white} weight={FontWeight.semiBold}>
              Training History
            </AppText>
            <AppText style={styles.bannerSubtitle} color={Colors.white}>
              All of your trainings
            </AppText>
          </View>
        </View>
      </ScreenBanner>

      <TrainingHistoryFilterBar
        fromDate={fromDate}
        toDate={toDate}
        onFromDateChange={setFromDate}
        onToDateChange={setToDate}
        onClear={clearFilters}
        hasFilter={hasFilter}
      />

      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator color={Colors.mainColour1} size="large" />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />}
        >
          <TrainingDetailsTable trainings={toTrainingRows(trainings)} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  banner: { paddingBottom: 20 },
  bannerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  bannerTitle: { fontSize: 17 },
  bannerSubtitle: { fontSize: 12, opacity: 0.9, marginTop: 2 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { paddingBottom: 32 },
});
