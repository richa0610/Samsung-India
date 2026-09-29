import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { RULES } from "./constants";

export default function RulesCard() {
  return (
    <View style={styles.card}>
      {RULES.map((rule) => (
        <View key={rule} style={styles.ruleRow}>
          <Ionicons name="checkmark-circle" size={16} color={Colors.success} />
          <AppText style={styles.ruleText}>{rule}</AppText>
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
  ruleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  ruleText: { fontSize: Fonts.bodySm },
});
