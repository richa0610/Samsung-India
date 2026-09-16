import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

export default function MissedBanner() {
  return (
    <View style={styles.missedBanner}>
      <View style={styles.missedIconWrap}>
        <Ionicons name="close-circle" size={18} color={Colors.danger} />
      </View>
      <View style={styles.missedTextColumn}>
        <AppText variant="caption" color={Colors.danger} weight={FontWeight.bold}>
          Missed
        </AppText>
        <AppText variant="overline" color={Colors.danger}>
          You missed this session, try next time.
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  missedBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#FEE2E2",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 10,
    width: "100%",
  },
  missedIconWrap: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: "#FCD8D8",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  missedTextColumn: {
    flex: 1,
    flexShrink: 1,
    gap: 2,
  },
});
