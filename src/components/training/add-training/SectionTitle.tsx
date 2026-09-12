import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { ICON_BADGE_BG } from "./constants";

export function SectionTitle({ index, title, icon }: { index: number; title: string; icon: keyof typeof Ionicons.glyphMap }) {
  return (
    <View style={styles.sectionHeader}>
      <View style={styles.sectionIconBadge}>
        <Ionicons name={icon} size={15} color={Colors.mainColour1} />
      </View>
      <AppText style={styles.sectionTitle} color={Colors.mainColour1} weight={FontWeight.semiBold}>
        {index}. {title}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  sectionHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 14 },
  sectionIconBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: ICON_BADGE_BG,
    alignItems: "center",
    justifyContent: "center",
  },
  sectionTitle: { fontSize: Fonts.bodyLg },
});
