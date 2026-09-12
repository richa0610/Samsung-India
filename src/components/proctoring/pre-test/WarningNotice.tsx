import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { MAX_WARNINGS } from "./constants";

export default function WarningNotice() {
  return (
    <View style={styles.warningBox}>
      <Ionicons name="warning" size={18} color="#B45309" />
      <AppText style={styles.warningText} color="#92400E">
        You will receive a maximum of {MAX_WARNINGS} warnings. After the {MAX_WARNINGS === 3 ? "third" : `${MAX_WARNINGS}th`}{" "}
        warning, your test will be submitted automatically.
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  warningBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    backgroundColor: "#FEF3C7",
    borderRadius: Radius.xl,
    padding: 12,
  },
  warningText: { flex: 1, fontSize: Fonts.bodySm, lineHeight: 19 },
});
