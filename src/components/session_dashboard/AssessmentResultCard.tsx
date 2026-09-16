import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";
import Svg, { Circle } from "react-native-svg";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type AssessmentResultCardProps = {
  passCount?: number;
  failCount?: number;
  passRate?: number;
  totalAttempts?: number;
  hasStarted?: boolean;
};

export default function AssessmentResultCard({
  passCount: passCountProp = 0,
  failCount: failCountProp = 0,
  passRate: passRateProp = 0,
  totalAttempts: totalAttemptsProp = 0,
  hasStarted = true,
}: AssessmentResultCardProps) {
  const passCount = hasStarted ? passCountProp : 0;
  const failCount = hasStarted ? failCountProp : 0;
  const totalAttempts = hasStarted ? totalAttemptsProp : 0;
  const passRate = hasStarted ? passRateProp : 0;
  const hasAttempts = totalAttempts > 0;
  const size = 96;
  const strokeWidth = 11;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Single green arc sweeping `passRate`% of the circle from 12 o'clock, over
  // a grey track for the failing remainder.
  const passLength = circumference * (Math.min(100, Math.max(0, passRate)) / 100);

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="time-outline" size={16} color={Colors.mainColour1} />
        <AppText style={styles.title}>ASSESSMENT RESULT</AppText>
      </View>

      {/* Content */}
      <View style={styles.contentRow}>
        {/* Left Circular Gauge */}
        <View style={styles.chartWrapper}>
          <Svg width={size} height={size}>
            <Circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke="#F3F4F6"
              strokeWidth={strokeWidth}
              fill="none"
            />
            {/* Pass Segment - sweeps `passRate`% from the top */}
            {hasAttempts && passLength > 0 && (
              <Circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke="#10B981"
                strokeWidth={strokeWidth}
                strokeDasharray={`${passLength} ${circumference}`}
                strokeDashoffset={0}
                strokeLinecap="round"
                fill="none"
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
              />
            )}
          </Svg>

          <View style={styles.chartCenter}>
            <AppText style={styles.chartCenterText}>
              {hasAttempts ? `${passRate}% PASS` : "No attempts"}
            </AppText>
          </View>
        </View>

        {/* Right Metric Boxes */}
        <View style={styles.metricsColumn}>
          <View style={styles.topBoxesRow}>
            {/* PASS Box */}
            <View style={styles.passBox}>
              <AppText style={styles.passLabel}>PASS</AppText>
              <AppText style={styles.passValue}>{passCount}</AppText>
            </View>

            {/* FAIL Box */}
            <View style={styles.failBox}>
              <AppText style={styles.failLabel}>FAIL</AppText>
              <AppText style={styles.failValue}>{failCount}</AppText>
            </View>
          </View>

          {/* Pass Rate Badge */}
          <View style={styles.passRateBadge}>
            <Ionicons name="trending-up" size={13} color="#10B981" />
            <AppText style={styles.passRateText}>Pass Rate : {passRate}%</AppText>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    marginHorizontal: 14,
    marginTop: 10,
    ...Shadows.card,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 10,
  },
  title: {
    fontSize: 11.5,
    fontWeight: "800",
    color: "#111827",
    letterSpacing: 0.3,
  },
  contentRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  chartWrapper: {
    position: "relative",
    width: 96,
    height: 96,
    alignItems: "center",
    justifyContent: "center",
  },
  chartCenter: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  chartCenterText: {
    fontSize: 9.5,
    fontWeight: "800",
    color: "#111827",
  },
  metricsColumn: {
    flex: 1,
    marginLeft: 14,
    gap: 8,
  },
  topBoxesRow: {
    flexDirection: "row",
    gap: 8,
  },
  passBox: {
    flex: 1,
    backgroundColor: "#ECFDF5",
    borderWidth: 1.2,
    borderColor: "#A7F3D0",
    borderRadius: 10,
    paddingVertical: 6,
    alignItems: "center",
  },
  passLabel: {
    fontSize: 8.5,
    fontWeight: "700",
    color: "#10B981",
  },
  passValue: {
    fontSize: 15,
    fontWeight: "800",
    color: "#111827",
    marginTop: 1,
  },
  failBox: {
    flex: 1,
    backgroundColor: "#FEF2F2",
    borderWidth: 1.2,
    borderColor: "#FECACA",
    borderRadius: 10,
    paddingVertical: 6,
    alignItems: "center",
  },
  failLabel: {
    fontSize: 8.5,
    fontWeight: "700",
    color: "#EF4444",
  },
  failValue: {
    fontSize: 15,
    fontWeight: "800",
    color: "#111827",
    marginTop: 1,
  },
  passRateBadge: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    backgroundColor: "#ECFDF5",
    borderRadius: 8,
    paddingVertical: 5,
  },
  passRateText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#10B981",
  },
});
