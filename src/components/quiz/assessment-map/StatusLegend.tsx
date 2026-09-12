import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export default function StatusLegend() {
  return (
    <View style={styles.legendRow}>
      <View style={styles.legendItem}>
        <View style={[styles.legendDot, { backgroundColor: Colors.recordedGreen }]} />
        <AppText style={styles.legendText} weight={FontWeight.medium}>
          Attempted
        </AppText>
      </View>

      <View style={styles.legendItem}>
        <View style={[styles.legendDot, { backgroundColor: "#FBBF24" }]} />
        <AppText style={styles.legendText} weight={FontWeight.medium}>
          Skipped
        </AppText>
      </View>

      <View style={styles.legendItem}>
        <View style={[styles.legendDot, { backgroundColor: Colors.danger }]} />
        <AppText style={styles.legendText} weight={FontWeight.medium}>
          Timed Out
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  legendRow: {
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    marginVertical: 14,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 11,
    color: "#1F2937",
  },
});
