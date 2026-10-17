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
            <Ionicons name="time-outline" size={16} color={Colors.brandBlue} />
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
                stroke={Colors.blue50}
                strokeWidth={strokeWidth}
                fill="none"
              />
              <Circle
                cx={donutSize / 2}
                cy={donutSize / 2}
                r={radius}
                stroke={Colors.brandBlue}
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
            color={Colors.statusGreen}
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
    borderColor: Colors.borderLight,
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
    color: Colors.gray600,
    letterSpacing: 0.3,
  },
  runtimeValue: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.black,
    marginVertical: 3,
  },
  assignedConsumedRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 2,
  },
  subTimeText: {
    fontSize: 9,
    color: Colors.gray500,
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
    color: Colors.brandBlue,
  },
  timeUsedLabel: {
    fontSize: 7.5,
    color: Colors.gray500,
    fontWeight: "700",
    marginTop: 3,
  },
  timeProgressBar: {
    width: "100%",
    height: 4.5,
    backgroundColor: Colors.gray100,
    borderRadius: 2.5,
    marginTop: 2,
    overflow: "hidden",
  },
  timeProgressFill: {
    height: "100%",
    backgroundColor: Colors.brandBlue,
    borderRadius: 2.5,
  },
  completionCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: Colors.borderLight,
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
    color: Colors.gray600,
    letterSpacing: 0.3,
  },
  completionPercent: {
    fontSize: 15,
    fontWeight: "800",
    color: Colors.statusGreen,
    marginTop: 3,
  },
  completionProgressBar: {
    width: "100%",
    height: 5,
    backgroundColor: Colors.gray100,
    borderRadius: 2.5,
    marginTop: 4,
    overflow: "hidden",
  },
  completionProgressFill: {
    height: "100%",
    backgroundColor: Colors.statusGreen,
    borderRadius: 2.5,
  },
});
