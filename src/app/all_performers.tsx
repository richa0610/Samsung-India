import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { TopPerformer, fetchAllPerformers } from "@/api/training";
import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

// Same cadence as the Session Dashboard's own poll (see
// useSessionDashboardScreen) - keeps this list moving while a Live Quiz is
// still running rather than only refreshing on pull-to-refresh.
const POLL_INTERVAL_MS = 5000;

export default function AllPerformersScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ conferenceUid?: string; title?: string }>();
  const conferenceUid = params.conferenceUid || "";
  const { adminToken } = useAuth();

  const [performers, setPerformers] = useState<TopPerformer[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken || !conferenceUid) return;
      if (mode === "refresh") setRefreshing(true);
      try {
        setPerformers(await fetchAllPerformers(adminToken, conferenceUid));
      } catch {
        // Keep whatever was last shown rather than blanking the list on a
        // transient network hiccup.
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoading(false);
      }
    },
    [adminToken, conferenceUid],
  );

  useFocusEffect(
    useCallback(() => {
      loadData();
      const interval = setInterval(() => loadData("silent"), POLL_INTERVAL_MS);
      return () => clearInterval(interval);
    }, [loadData]),
  );

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScreenBanner backgroundColor={Colors.mainColour1} statusBarStyle="light" style={[styles.banner, { paddingTop: insets.top + 4 }]}>
        <View style={styles.headerRow}>
          <Pressable
            style={styles.backCircleBtn}
            onPress={() => router.back()}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel="Back"
          >
            <Ionicons name="chevron-back" size={20} color={Colors.white} />
          </Pressable>
          <View style={styles.titleWrapper}>
            <AppText style={styles.title} color={Colors.white} weight={FontWeight.bold}>
              TOP PERFORMERS
            </AppText>
            <AppText style={styles.subtitle} color={Colors.white} numberOfLines={1}>
              {params.title || "All trainees, ranked"}
            </AppText>
          </View>
        </View>
      </ScreenBanner>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator color={Colors.mainColour1} size="large" />
        </View>
      ) : performers.length === 0 ? (
        <View style={styles.centered}>
          <AppText style={styles.emptyTrophy}>🏆</AppText>
          <AppText style={styles.emptyTitle} weight={FontWeight.bold}>
            No results yet
          </AppText>
          <AppText style={styles.emptySubtitle} color={Colors.gray600}>
            Scores will appear here as participants finish.
          </AppText>
        </View>
      ) : (
        <FlatList
          data={performers}
          keyExtractor={(item, index) => `${item.traineeUid}-${index}`}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => loadData("refresh")}
              colors={[Colors.mainColour1]}
              tintColor={Colors.mainColour1}
            />
          }
          renderItem={({ item, index }) => (
            <View style={styles.row}>
              <View style={styles.rankBadge}>
                <AppText style={styles.rankText} weight={FontWeight.bold}>
                  {index + 1}
                </AppText>
              </View>
              <View style={styles.avatarCircle}>
                <Ionicons name="person" size={13} color="#8B5CF6" />
              </View>
              <AppText style={styles.name} numberOfLines={1}>
                {item.name}
              </AppText>
              <AppText style={styles.scoreText}>
                {Math.round(item.score)}/{Math.round(item.maxScore)}{" "}
                <AppText style={styles.percentageText}>[{Math.round(item.percentage)}%]</AppText>
              </AppText>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  banner: { paddingBottom: 20 },
  headerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  backCircleBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.2,
    borderColor: "rgba(255, 255, 255, 0.4)",
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  titleWrapper: { flex: 1, gap: 0 },
  title: { fontSize: 15, letterSpacing: 0.3 },
  subtitle: { fontSize: 11, opacity: 0.9, marginTop: 1 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", gap: 4, paddingHorizontal: 24 },
  emptyTrophy: { fontSize: 36, marginBottom: 4 },
  emptyTitle: { fontSize: 14, color: "#111827" },
  emptySubtitle: { fontSize: 12, textAlign: "center" },
  list: { padding: 14, gap: 8 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  rankBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  rankText: { fontSize: 10.5, color: "#6B7280" },
  avatarCircle: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "#EDE9FE",
    alignItems: "center",
    justifyContent: "center",
  },
  name: { flex: 1, fontSize: 12.5, fontWeight: "700", color: "#111827" },
  scoreText: { fontSize: 12, fontWeight: "800", color: "#0066FF" },
  percentageText: { fontSize: 10.5, fontWeight: "600", color: "#6B7280" },
});
