import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";

type Props = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  onPress: () => void;
};

/** One of the side-by-side sign-in choices: an icon, a hairline, and its label. */
export default function LoginOptionButton({ icon, label, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.button, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      <Ionicons name={icon} size={24} color={Colors.mainColour1} />
      <View style={styles.separator} />
      <AppText
        variant="label"
        color={Colors.textHeading}
        style={styles.label}
        numberOfLines={1}
        adjustsFontSizeToFit
        minimumFontScale={0.85}
      >
        {label}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    height: 58,
    paddingHorizontal: 16,
    borderRadius: Radius.xxxl,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
    backgroundColor: Colors.white,
    ...Shadows.card,
  },
  pressed: { backgroundColor: Colors.brandTintSoft, transform: [{ scale: 0.98 }] },
  separator: { width: 1, height: 24, backgroundColor: Colors.surfaceBorder },
  label: { flexShrink: 1, fontWeight: "500" },
});
