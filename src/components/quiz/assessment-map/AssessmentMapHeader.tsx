import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type AssessmentMapHeaderProps = {
  answeredCount: number;
  totalQuestions: number;
  /** Total response time across answered questions, e.g. "3:12". */
  timeTakenLabel?: string | null;
  connected?: boolean;
};

export default function AssessmentMapHeader({
  answeredCount,
  totalQuestions,
  timeTakenLabel,
  connected = true,
}: AssessmentMapHeaderProps) {
  const progress =
    totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0;

  return (
    <View style={styles.container}>
      <View style={styles.pill}>
        <Ionicons name="time-outline" size={16} color={Colors.headerBlue} />
        <View>
          <AppText style={styles.pillValue} color={Colors.headerBlue} weight={FontWeight.bold}>
            {timeTakenLabel || "--:--"}
          </AppText>
          <AppText style={styles.pillSub}>Time Taken</AppText>
        </View>
      </View>

      <View style={styles.progressPill}>
        <View style={styles.progressLabelRow}>
          <AppText style={styles.progressLabel} color={Colors.headerBlue} weight={FontWeight.semiBold}>
            Overall Progress
          </AppText>
          <AppText style={styles.progressLabel} color={Colors.headerBlue} weight={FontWeight.bold}>
            {progress}%
          </AppText>
        </View>
        <View style={styles.track}>
          <View style={[styles.fill, { width: `${Math.min(100, Math.max(0, progress))}%` }]} />
        </View>
      </View>

      <View style={[styles.wifiBadge, !connected && styles.wifiBadgeOff]}>
        <Ionicons name={connected ? "wifi" : "cloud-offline-outline"} size={15} color={Colors.white} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.headerBlue,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  pill: {
    backgroundColor: Colors.white,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  pillValue: { fontSize: 12, lineHeight: 14 },
  pillSub: { fontSize: 8, color: Colors.gray600, marginTop: -2 },
  progressPill: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    justifyContent: "center",
  },
  progressLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  progressLabel: { fontSize: 9.5 },
  track: { height: 4, borderRadius: 2, backgroundColor: "#E5E7EB", overflow: "hidden" },
  fill: { height: "100%", borderRadius: 2, backgroundColor: Colors.headerBlue },
  wifiBadge: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: Colors.recordedGreen,
    alignItems: "center",
    justifyContent: "center",
  },
  wifiBadgeOff: { backgroundColor: Colors.gray600 },
});
