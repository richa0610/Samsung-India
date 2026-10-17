import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { ModuleDetailCard, StatusNoticeCard } from "@/components/trainee/training-detail";
import { statusMetaFor } from "@/components/trainee/training-detail/statusMeta";
import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { useTrainingDetail } from "@/hooks/useTrainingDetail";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { trainingStatusLabel } from "@/utils/trainingStatusLabel";

export default function TrainingDetailScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { onBack, detail, loading, error, reload, expandedKeys, toggleModule } = useTrainingDetail();
  const overallMeta = detail ? statusMetaFor(detail.status) : null;

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScreenBanner backgroundColor={Colors.mainColour1} statusBarStyle="light" style={[styles.banner, { paddingTop: insets.top + 12 }]}>
        <View style={styles.bannerRow}>
          <Pressable onPress={onBack} hitSlop={8} accessibilityRole="button" accessibilityLabel="Back" style={styles.backBtnWrap}>
            <Ionicons name="arrow-back" size={18} color={Colors.white} />
          </Pressable>
          <View style={styles.bannerTextColumn}>
            <AppText style={styles.bannerTitle} color={Colors.white} weight={FontWeight.semiBold} numberOfLines={1}>
              {detail?.title ?? "Training Detail"}
            </AppText>
            {detail && (
              <AppText style={styles.bannerSubtitle} color={Colors.white} numberOfLines={1}>
                {[detail.date, detail.location].filter(Boolean).join(" · ") || "Session details"}
              </AppText>
            )}
          </View>
        </View>
      </ScreenBanner>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator color={Colors.mainColour1} size="large" />
        </View>
      ) : error || !detail ? (
        <View style={styles.centered}>
          <AppText variant="body" color={Colors.gray600} align="center">
            {error ?? "This training couldn't be found."}
          </AppText>
          <Pressable style={styles.retryButton} onPress={reload} accessibilityRole="button" accessibilityLabel="Retry">
            <AppText variant="label" color={Colors.white}>
              Retry
            </AppText>
          </Pressable>
        </View>
      ) : detail.status === "Missed" ? (
        <StatusNoticeCard
          status="Missed"
          title="Session Missed"
          message="You missed this training. Try to join your next scheduled session on time."
          sessionTitle={detail.title}
          date={detail.date}
          location={detail.location}
          trainerName={detail.trainerName}
          onBack={onBack}
          onGoDashboard={() => router.replace("/trainee_dashboard")}
        />
      ) : detail.status === "Absent" ? (
        <StatusNoticeCard
          status="Absent"
          title="Marked Absent"
          message="You were marked absent for this training, so its details aren't available. Try to attend your next scheduled session."
          sessionTitle={detail.title}
          date={detail.date}
          location={detail.location}
          trainerName={detail.trainerName}
          onBack={onBack}
          onGoDashboard={() => router.replace("/trainee_dashboard")}
        />
      ) : detail.status === "Ongoing" ? (
        <StatusNoticeCard
          status="Ongoing"
          title="Training In Progress"
          message="This training is still going on. Its full details will be available here once it's completed."
          sessionTitle={detail.title}
          date={detail.date}
          location={detail.location}
          trainerName={detail.trainerName}
          onBack={onBack}
          onGoDashboard={() => router.replace("/trainee_dashboard")}
        />
      ) : (
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.summaryCard}>
            {detail.trainerName && (
              <>
                <View style={styles.summaryRow}>
                  <View style={styles.summaryIconWrap}>
                    <Ionicons name="person" size={16} color={Colors.blueAccent} />
                  </View>
                  <View style={styles.summaryTextColumn}>
                    <AppText variant="tiny" weight={FontWeight.bold} color={Colors.gray400} style={styles.summaryLabel}>
                      TRAINER
                    </AppText>
                    <AppText variant="body" weight={FontWeight.bold} color={Colors.black}>
                      {detail.trainerName}
                    </AppText>
                  </View>
                </View>
                <View style={styles.summaryDivider} />
              </>
            )}

            <View style={styles.summaryRow}>
              <View style={[styles.summaryIconWrap, overallMeta && { backgroundColor: overallMeta.bg }]}>
                <Ionicons name="shield-checkmark" size={16} color={overallMeta?.color ?? Colors.blueAccent} />
              </View>
              <View style={styles.summaryTextColumn}>
                <AppText variant="tiny" weight={FontWeight.bold} color={Colors.gray400} style={styles.summaryLabel}>
                  OVERALL STATUS
                </AppText>
                <AppText variant="body" weight={FontWeight.bold} color={overallMeta?.color ?? Colors.black}>
                  {trainingStatusLabel(detail.status)}
                </AppText>
              </View>
              {overallMeta && (
                <View style={[styles.statusPill, { backgroundColor: overallMeta.bg }]}>
                  <Ionicons name={overallMeta.icon} size={16} color={overallMeta.color} />
                </View>
              )}
            </View>
          </View>

          <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray400} style={styles.sectionLabel}>
            MODULES
          </AppText>

          {detail.modules.length === 0 ? (
            <AppText variant="caption" color={Colors.gray400}>
              No modules were configured for this training.
            </AppText>
          ) : (
            detail.modules.map((module) => (
              <ModuleDetailCard
                key={module.key}
                module={module}
                expanded={expandedKeys.has(module.key)}
                onToggle={() => toggleModule(module.key)}
              />
            ))
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  banner: {
    paddingBottom: 22,
    borderBottomLeftRadius: Radius.header,
    borderBottomRightRadius: Radius.header,
  },
  bannerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  backBtnWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(255, 255, 255, 0.16)",
    alignItems: "center",
    justifyContent: "center",
  },
  bannerTextColumn: { flex: 1 },
  bannerTitle: { fontSize: 18, letterSpacing: -0.2 },
  bannerSubtitle: { fontSize: 12, opacity: 0.9, marginTop: 2 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, paddingHorizontal: 24 },
  retryButton: {
    backgroundColor: Colors.mainColour1,
    paddingHorizontal: 22,
    paddingVertical: 10,
    borderRadius: 8,
    minWidth: 105,
    minHeight: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  content: { padding: 16, paddingBottom: 32 },
  summaryCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.gray200,
    padding: 14,
    marginBottom: 16,
    ...Shadows.card,
  },
  summaryRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  summaryIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
  },
  summaryTextColumn: { flex: 1, gap: 2 },
  summaryLabel: { letterSpacing: 0.4 },
  summaryDivider: { height: 1, backgroundColor: Colors.slate100, marginVertical: 12 },
  statusPill: {
    width: 32,
    height: 32,
    borderRadius: Radius.pill,
    alignItems: "center",
    justifyContent: "center",
  },
  sectionLabel: { letterSpacing: 0.6, textTransform: "uppercase", marginBottom: 10 },
});
