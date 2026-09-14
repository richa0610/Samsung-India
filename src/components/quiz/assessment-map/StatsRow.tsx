import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type StatsRowProps = {
  attemptedCount: number;
  skippedCount: number;
  expiredCount: number;
};

export default function StatsRow({ attemptedCount, skippedCount, expiredCount }: StatsRowProps) {
  return (
    <View style={styles.statsRow}>
      <View style={styles.statCol}>
        <AppText style={[styles.statValue, { color: Colors.recordedGreen }]} weight={FontWeight.bold}>
          {attemptedCount}
        </AppText>
        <AppText style={styles.statLabel} weight={FontWeight.bold}>
          DONE
        </AppText>
      </View>

      <View style={styles.statDivider} />

      <View style={styles.statCol}>
        <AppText style={[styles.statValue, { color: "#FBBF24" }]} weight={FontWeight.bold}>
          {skippedCount}
        </AppText>
        <AppText style={styles.statLabel} weight={FontWeight.bold}>
          SKIPPED
        </AppText>
      </View>

      <View style={styles.statDivider} />

      <View style={styles.statCol}>
        <AppText style={[styles.statValue, { color: Colors.danger }]} weight={FontWeight.bold}>
          {expiredCount}
        </AppText>
        <AppText style={styles.statLabel} weight={FontWeight.bold}>
          EXPIRED
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  statsRow: {
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  statCol: {
    alignItems: "center",
    flex: 1,
  },
  statValue: {
    fontSize: 26,
    lineHeight: 30,
  },
  statLabel: {
    fontSize: 11,
    color: Colors.gray600,
    marginTop: 2,
    letterSpacing: 0.3,
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: "#E5E7EB",
  },
});
