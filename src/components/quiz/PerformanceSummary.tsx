import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export type PerformanceSummaryProps = {
  correctCount: number;
  incorrectCount: number;
  accuracy: number;
  timeTaken: string;
};

export default function PerformanceSummary({
  correctCount,
  incorrectCount,
  accuracy,
  timeTaken,
}: PerformanceSummaryProps) {
  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="stats-chart" size={16} color={Colors.headerBlue} />
        <AppText style={styles.headerTitle} weight={FontWeight.bold}>
          Performance Summary
        </AppText>
      </View>

      {/* 4-Item Grid */}
      <View style={styles.itemsRow}>
        {/* 1. Correct */}
        <View style={styles.item}>
          <View style={[styles.iconCircle, styles.correctCircle]}>
            <Ionicons name="checkmark" size={18} color="#2563EB" />
          </View>
          <AppText style={styles.itemValue} weight={FontWeight.bold}>
            {correctCount}
          </AppText>
          <AppText style={styles.itemLabel}>Correct</AppText>
        </View>

        {/* 2. Incorrect */}
        <View style={styles.item}>
          <View style={[styles.iconCircle, styles.incorrectCircle]}>
            <Ionicons name="close" size={18} color="#EF4444" />
          </View>
          <AppText style={styles.itemValue} weight={FontWeight.bold}>
            {incorrectCount}
          </AppText>
          <AppText style={styles.itemLabel}>Incorrect</AppText>
        </View>

        {/* 3. Accuracy */}
        <View style={styles.item}>
          <View style={[styles.iconCircle, styles.accuracyCircle]}>
            <AppText style={styles.percentIcon} weight={FontWeight.bold}>
              %
            </AppText>
          </View>
          <AppText style={styles.itemValue} weight={FontWeight.bold}>
            {accuracy}%
          </AppText>
          <AppText style={styles.itemLabel}>Accuracy</AppText>
        </View>

        {/* 4. Time Taken */}
        <View style={styles.item}>
          <View style={[styles.iconCircle, styles.timeCircle]}>
            <Ionicons name="time-outline" size={18} color="#059669" />
          </View>
          <AppText style={styles.itemValue} weight={FontWeight.bold}>
            {timeTaken}
          </AppText>
          <AppText style={styles.itemLabel}>Time Taken</AppText>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 16,
    marginTop: 14,
    ...createShadow({ x: 0, y: 2, blur: 6, opacity: 0.05, elevation: 2 }),
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 14,
  },
  headerTitle: {
    fontSize: 11,
    color: "#111827",
    letterSpacing: 0.5,
  },
  itemsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  item: {
    alignItems: "center",
    flex: 1,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 6,
  },
  correctCircle: {
    backgroundColor: "#DBEAFE",
  },
  incorrectCircle: {
    backgroundColor: "#FEE2E2",
  },
  accuracyCircle: {
    backgroundColor: "#FEF9C3",
  },
  timeCircle: {
    backgroundColor: "#D1FAE5",
  },
  percentIcon: {
    color: "#D97706",
    fontSize: 16,
  },
  itemValue: {
    fontSize: 17,
    color: "#111827",
  },
  itemLabel: {
    fontSize: 10.5,
    color: Colors.gray600,
    marginTop: 2,
  },
});
