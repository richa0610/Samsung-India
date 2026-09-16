import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import Svg, { Circle } from "react-native-svg";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { DashboardStats } from "./dashboardUtils";

type TrainingEfficiencyCardProps = {
  stats: DashboardStats;
};

export default function TrainingEfficiencyCard({
  stats,
}: TrainingEfficiencyCardProps) {
  const size = 110;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const executedPercent = stats.executedPercentage;
  const pendingPercent = stats.pendingPercentage;

  const blueDash = (circumference * pendingPercent) / 100;
  const greenDash = (circumference * executedPercent) / 100;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerRow}>
        <AppText style={styles.title}>Training Efficiency</AppText>
      </View>

      {/* Content: Donut Chart + Middle Divider + Stats */}
      <View style={styles.contentRow}>
        {/* Donut Chart */}
        <View style={styles.chartWrapper}>
          <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
            {/* Blue Arc (Pending) - 70% */}
            <Circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="#0066FF"
              strokeWidth={strokeWidth}
              strokeDasharray={`${blueDash} ${circumference}`}
              strokeDashoffset={0}
              strokeLinecap="butt"
              fill="none"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
            {/* Green Arc (Executed) - 30% */}
            <Circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="#00BA5D"
              strokeWidth={strokeWidth}
              strokeDasharray={`${greenDash} ${circumference}`}
              strokeDashoffset={0}
              strokeLinecap="butt"
              fill="none"
              transform={`rotate(${
                (pendingPercent / 100) * 360 - 90
              } ${size / 2} ${size / 2})`}
            />
          </Svg>

          <View style={styles.chartCenterText}>
            
            <AppText style={styles.centerValue}>{stats.totalSessions}</AppText>
            <AppText style={styles.centerLabel}>Total</AppText>
            <AppText style={styles.centerLabel}> Sessions</AppText>
          </View>
        </View>

        {/* Middle Vertical Divider Line */}
        <View style={styles.verticalDivider} />

        {/* Breakdown Progress Bars */}
        <View style={styles.statsColumn}>
          {/* Executed Section */}
          <View style={styles.statItem}>
            <View style={styles.statHeader}>
              <View style={styles.statLabelRow}>
                <View style={[styles.dot, { backgroundColor: "#00BA5D" }]} />
                <AppText style={styles.statLabel}>Executed</AppText>
              </View>
            </View>
            <View style={styles.valueRow}>
              <AppText style={styles.executedValue}>
                {stats.completed}{" "}
                <AppText style={styles.executedPercentText}>
                  ({executedPercent}%)
                </AppText>
              </AppText>
            </View>
            <View style={styles.progressBarTrack}>
              <View
                style={[
                  styles.progressBarFill,
                  {
                    width: `${executedPercent}%`,
                    backgroundColor: "#00BA5D",
                  },
                ]}
              />
            </View>
          </View>

          {/* Pending Section */}
          <View style={[styles.statItem, { marginTop: 12 }]}>
            <View style={styles.statHeader}>
              <View style={styles.statLabelRow}>
                <View style={[styles.dot, { backgroundColor: "#0066FF" }]} />
                <AppText style={styles.statLabel}>Pending</AppText>
              </View>
            </View>
            <View style={styles.valueRow}>
              <AppText style={styles.pendingValue}>
                {stats.pending}{" "}
                <AppText style={styles.pendingPercentText}>
                  ({pendingPercent}%)
                </AppText>
              </AppText>
            </View>
            <View style={styles.progressBarTrack}>
              <View
                style={[
                  styles.progressBarFill,
                  {
                    width: `${pendingPercent}%`,
                    backgroundColor: "#0066FF",
                  },
                ]}
              />
            </View>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 15,
    marginHorizontal: 10,
    marginTop: 10,
    ...Shadows.card,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  title: {
    fontSize: 12,
    fontWeight: "500",
    color: "#000000",
  },
  contentRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
  },
  chartWrapper: {
    flex: 1,
    position: "relative",
    alignItems: "flex-start",
    justifyContent: "center",
  },
  chartCenterText: {
    position: "absolute",
    width: 108,
    height: 108,
    alignItems: "center",
    justifyContent: "center",
  },
  centerValue: {
    fontSize: 18,
    fontWeight: "800",
    color: "#111827",
  },
  centerLabel: {
    fontSize: 9,
    fontWeight: "600",
    color: "#111827",
  },
  verticalDivider: {
    width: 2,
    height: 80,
    backgroundColor: "#E5E7EB",
    marginHorizontal: 15,
  },
  statsColumn: {
    flex: 1,
    justifyContent: "center",
  },
  statItem: {},
  statHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  statLabelRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statLabel: {
    fontSize: 10,
    fontWeight: "600",
    color: "#111827",
  },
  valueRow: {
    marginTop: 2,
    marginBottom: 4,
  },
  executedValue: {
    fontSize: 14,
    fontWeight: "700",
    color: "#00BA5D",
  },
  executedPercentText: {
    fontSize: 11,
    fontWeight: "500",
    color: "#00BA5D",
  },
  pendingValue: {
    fontSize: 14,
    fontWeight: "700",
    color: "#0066FF",
  },
  pendingPercentText: {
    fontSize: 11,
    fontWeight: "500",
    color: "#0066FF",
  },
  progressBarTrack: {
    height: 5,
    backgroundColor: "#F3F4F6",
    borderRadius: 2.5,
    overflow: "hidden",
  },
  progressBarFill: {
    height: 5,
    borderRadius: 2.5,
  },
});
