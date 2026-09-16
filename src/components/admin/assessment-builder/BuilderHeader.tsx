import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type BuilderHeaderProps = {
  onBack: () => void;
};

export default function BuilderHeader({ onBack }: BuilderHeaderProps) {
  return (
    <View style={styles.header}>
      <Pressable style={styles.iconButton} onPress={onBack} hitSlop={8}>
        <Ionicons name="arrow-back" size={20} color={Colors.mainColour1} />
      </Pressable>
      <AppText style={styles.headerTitle} weight={FontWeight.semiBold}>
        Assessment Builder
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: { fontSize: Fonts.h3 },
});
