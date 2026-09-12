import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { useLiveRuntime } from "@/hooks/useLiveRuntime";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type ActiveModuleCardProps = {
  moduleLabel: string;
  startedAt: string | null;
  questionCount: number | null;
  // Force-ends this module only. It does NOT start the next module (the
  // trainer taps that module's Start button) and it does NOT end the
  // session (only the red "End Session" button does that).
  onEndModule: () => void;
};

function clock(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  return [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
}

export default function ActiveModuleCard({
  moduleLabel,
  startedAt,
  questionCount,
  onEndModule,
}: ActiveModuleCardProps) {
  const seconds = useLiveRuntime(startedAt, null);
  const buttonLabel = `END ${moduleLabel.toUpperCase()}`;

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.liveBadge}>
          <View style={styles.liveDot} />
          <AppText style={styles.liveText}>LIVE SESSION BROADCASTING</AppText>
        </View>
        <View style={styles.timerPill}>
          <AppText style={styles.timerText}>{clock(seconds)}</AppText>
        </View>
      </View>

      <View style={styles.titleSection}>
        <AppText style={styles.activeModuleLabel}>ACTIVE MODULE</AppText>
        <AppText style={styles.moduleTitle}>{moduleLabel}</AppText>
        {questionCount != null && (
          <View style={styles.pill}>
            <AppText style={styles.pillText}>Targeted {questionCount} QPs</AppText>
          </View>
        )}
      </View>

      <Pressable
        style={styles.primaryBtn}
        onPress={onEndModule}
        accessibilityRole="button"
        accessibilityLabel={buttonLabel}
      >
        <Ionicons name="power" size={16} color="#0066FF" />
        <AppText style={styles.primaryBtnText} numberOfLines={2}>{buttonLabel}</AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#0066FF",
    borderRadius: 18,
    padding: 14,
    marginHorizontal: 14,
    marginTop: 10,
    ...Shadows.raised,
  },
  headerRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  liveBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "#EF4444" },
  liveText: { fontSize: 8.5, fontWeight: "700", color: Colors.white, letterSpacing: 0.3 },
  timerPill: {
    backgroundColor: "rgba(255, 255, 255, 0.2)",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  timerText: { fontSize: 11, fontWeight: "800", color: Colors.white, letterSpacing: 0.5 },
  titleSection: { marginTop: 12, gap: 4 },
  activeModuleLabel: {
    fontSize: 9,
    fontWeight: "600",
    color: "rgba(255, 255, 255, 0.75)",
    letterSpacing: 0.5,
  },
  moduleTitle: { fontSize: 15, fontWeight: "800", color: Colors.white, lineHeight: 20 },
  pill: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    marginTop: 4,
  },
  pillText: { fontSize: 9.5, fontWeight: "600", color: Colors.white },
  primaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: Colors.white,
    borderRadius: 12,
    paddingVertical: 11,
    paddingHorizontal: 10,
    marginTop: 14,
    ...Shadows.card,
  },
  primaryBtnText: {
    fontSize: 12,
    fontWeight: "800",
    color: "#0066FF",
    letterSpacing: 0.3,
    textAlign: "center",
    flexShrink: 1,
  },
});
