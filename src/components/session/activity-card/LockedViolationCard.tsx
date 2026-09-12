import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/typography";

export default function LockedViolationCard() {
  return (
    <View style={styles.lockedBanner}>
      <View style={styles.lockedIconWrap}>
        <Ionicons name="lock-closed" size={16} color="#EF4444" />
      </View>
      <View style={styles.lockedTextColumn}>
        <AppText variant="caption" color="#EF4444" weight={FontWeight.bold}>
          Security Violation
        </AppText>
        <AppText variant="overline" color="#B91C1C">
          Test was locked due to proctoring violation.
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  lockedBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#FEE2E2",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 10,
    borderWidth: 1,
    borderColor: "#FECACA",
    width: "100%",
  },
  lockedIconWrap: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: "#FCD8D8",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  lockedTextColumn: {
    flex: 1,
    flexShrink: 1,
    gap: 2,
  },
});
