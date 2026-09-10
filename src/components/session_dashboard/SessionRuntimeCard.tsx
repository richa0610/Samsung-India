import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";
import Svg, { Circle } from "react-native-svg";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type SessionRuntimeCardProps = {
  actualRuntime?: string;
  assignedTime?: string;
  consumedTime?: string;
  timeUsedPercent?: number;
  moduleCompletionPercent?: number;
};

export default function SessionRuntimeCard({
  actualRuntime = "0h 00m 00s",
  assignedTime = "0h 00m",
  consumedTime = "0h 00m",
  timeUsedPercent = 0,
  moduleCompletionPercent = 0,
}: SessionRuntimeCardProps) {
  const donutSize = 56;
  const strokeWidth = 6;
  const radius = (donutSize - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    circumference - (circumference * timeUsedPercent) / 100;

  return (
    <View style={styles.container}>
      {/* Top Runtime Card */}
      <View style={styles.runtimeCard}>
        <View style={styles.runtimeLeft}>
          <View style={styles.runtimeHeader}>
            <Ionicons name="time-outline" size={16} color="#0066FF" />
            <AppText style={styles.runtimeTitle}>ACTUAL SESSION RUNTIME</AppText>
          </View>
          <AppText style={styles.runtimeValue}>{actualRuntime}</AppText>
          <View style={styles.assignedConsumedRow}>
            <AppText style={styles.subTimeText}>Assigned: {assignedTime}</AppText>
            <AppText style={styles.subTimeText}>Consumed: {consumedTime}</AppText>
          </View>
        </View>

        <View style={styles.runtimeRight}>
          <View style={styles.donutWrapper}>
            <Svg width={donutSize} height={donutSize}>
              <Circle
                cx={donutSize / 2}
                cy={donutSize / 2}
                r={radius}
                stroke="#EFF6FF"
                strokeWidth={strokeWidth}
                fill="none"
              />
              <Circle
                cx={donutSize / 2}
                cy={donutSize / 2}
                r={radius}
                stroke="#0066FF"
                strokeWidth={strokeWidth}
                strokeDasharray={`${circumference} ${circumference}`}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="none"
                transform={`rotate(-90 ${donutSize / 2} ${donutSize / 2})`}
              />
            </Svg>
            <View style={styles.donutCenter}>
              <AppText style={styles.donutPercentText}>{timeUsedPercent}%</AppText>
            </View>
          </View>
          <AppText style={styles.timeUsedLabel}>TOTAL TIME USED</AppText>
          <View style={styles.timeProgressBar}>
            <View
              style={[
                styles.timeProgressFill,
                { width: `${timeUsedPercent}%` },
              ]}
            />
          </View>
        </View>
      </View>

      {/* Bottom Completion Card */}
      <View style={styles.completionCard}>
        <View style={styles.completionHeader}>
          <Ionicons
            name="checkbox-outline"
            size={17}
            color="#10B981"
          />
          <AppText style={styles.completionTitle}>MODULE COMPLETION</AppText>
        </View>
        <AppText style={styles.completionPercent}>
          {moduleCompletionPercent}%
        </AppText>
        <View style={styles.completionProgressBar}>
          <View
            style={[
              styles.completionProgressFill,
              { width: `${moduleCompletionPercent}%` },
            ]}
          />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 14,
    marginTop: 10,
    gap: 8,
  },
  runtimeCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    ...Shadows.card,
  },
  runtimeLeft: {
    flex: 1,
  },
  runtimeHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  runtimeTitle: {
    fontSize: 9.5,
    fontWeight: "800",
    color: "#4B5563",
    letterSpacing: 0.3,
  },
  runtimeValue: {
    fontSize: 16,
    fontWeight: "800",
    color: "#111827",
    marginVertical: 3,
  },
  assignedConsumedRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 2,
  },
  subTimeText: {
    fontSize: 9,
    color: "#6B7280",
    fontWeight: "500",
  },
  runtimeRight: {
    alignItems: "center",
    width: 86,
  },
  donutWrapper: {
    position: "relative",
    width: 56,
    height: 56,
    alignItems: "center",
    justifyContent: "center",
  },
  donutCenter: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  donutPercentText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#0066FF",
  },
  timeUsedLabel: {
    fontSize: 7.5,
    color: "#6B7280",
    fontWeight: "700",
    marginTop: 3,
  },
  timeProgressBar: {
    width: "100%",
    height: 4.5,
    backgroundColor: "#F3F4F6",
    borderRadius: 2.5,
    marginTop: 2,
    overflow: "hidden",
  },
  timeProgressFill: {
    height: "100%",
    backgroundColor: "#0066FF",
    borderRadius: 2.5,
  },
  completionCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    ...Shadows.card,
  },
  completionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  completionTitle: {
    fontSize: 9.5,
    fontWeight: "800",
    color: "#4B5563",
    letterSpacing: 0.3,
  },
  completionPercent: {
    fontSize: 15,
    fontWeight: "800",
    color: "#10B981",
    marginTop: 3,
  },
  completionProgressBar: {
    width: "100%",
    height: 5,
    backgroundColor: "#F3F4F6",
    borderRadius: 2.5,
    marginTop: 4,
    overflow: "hidden",
  },
  completionProgressFill: {
    height: "100%",
    backgroundColor: "#10B981",
    borderRadius: 2.5,
  },
});
