import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";

type Tone = "blue" | "green";

const TONE_STYLES: Record<Tone, { accent: string; tint: string }> = {
  blue: { accent: Colors.mainColour1, tint: "#EAF2FF" },
  green: { accent: Colors.success, tint: "#EAF9EF" },
};

type Props = {
  icon: keyof typeof Ionicons.glyphMap;
  tone: Tone;
  title: string;
  subtitle: string;
  onPress: () => void;
};

export default function RoleLoginCard({ icon, tone, title, subtitle, onPress }: Props) {
  const { accent, tint } = TONE_STYLES[tone];

  return (
    <Pressable
      style={[styles.card, { backgroundColor: tint, borderColor: accent }]}
      onPress={onPress}
    >
      <View style={[styles.iconBox, { backgroundColor: accent }]}>
        <Ionicons name={icon} size={18} color={Colors.white} />
      </View>
      <View style={styles.textColumn}>
        <AppText variant="label" color={accent}>
          {title}
        </AppText>
        <AppText variant="tiny" color={Colors.gray600}>
          {subtitle}
        </AppText>
      </View>
      <View style={[styles.chevron, { backgroundColor: accent }]}>
        <Ionicons name="chevron-forward" size={14} color={Colors.white} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderRadius: Radius.xl,
    borderWidth: 1.5,
    padding: 10,
  },
  iconBox: {
    width: 34,
    height: 34,
    borderRadius: Radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  textColumn: { flex: 1, gap: 2 },
  chevron: {
    width: 22,
    height: 22,
    borderRadius: Radius.pill,
    alignItems: "center",
    justifyContent: "center",
  },
});
