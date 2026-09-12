import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { POSE_ROWS } from "./constants";

export default function PoseChecklistCard() {
  return (
    <View style={styles.card}>
      {POSE_ROWS.map((row) => (
        <View key={row.key} style={styles.poseRow}>
          <View style={styles.statusBadge}>
            <Ionicons
              name={row.ok ? "checkmark-circle" : "close-circle"}
              size={30}
              color={row.ok ? Colors.success : Colors.danger}
            />
          </View>
          <Ionicons name={row.icon} size={16} color={row.ok ? Colors.success : Colors.danger} />
          <AppText style={styles.poseLabel}>{row.label}</AppText>
          <Ionicons name={row.ok ? "checkmark" : "close"} size={16} color={row.ok ? Colors.success : Colors.danger} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xxl,
    padding: 14,
    gap: 10,
  },
  poseRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  statusBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  poseLabel: { fontSize: Fonts.bodySm, flex: 1 },
});
