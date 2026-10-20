import { Ionicons } from "@expo/vector-icons";
import { ReactNode } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";

/** A role card's palette (see the role* colours in the theme). */
export type RoleTone = {
  background: string;
  border: string;
  tile: string;
  chevron: string;
  text: string;
};

export const ROLE_TONES = {
  trainer: {
    background: Colors.roleTrainerBg,
    border: Colors.roleTrainerBorder,
    tile: Colors.roleTrainerTile,
    chevron: Colors.roleTrainerChevron,
    text: Colors.roleTrainerText,
  },
  admin: {
    background: Colors.roleAdminBg,
    border: Colors.roleAdminBorder,
    tile: Colors.roleAdminTile,
    chevron: Colors.roleAdminChevron,
    text: Colors.roleAdminText,
  },
} satisfies Record<string, RoleTone>;

type Props = {
  icon: ReactNode;
  title: string;
  body: string;
  tone: RoleTone;
  onPress: () => void;
};

/** One role in the "Login as" sheet: an icon tile, the role and what it does, and a chevron. */
export default function RoleOptionCard({ icon, title, body, tone, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { backgroundColor: tone.background, borderColor: tone.border },
        pressed && styles.pressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`${title}. ${body}`}
    >
      <View style={[styles.tile, { backgroundColor: tone.tile }]}>{icon}</View>
      <View style={styles.text}>
        <AppText color={Colors.roleCardTitle} style={styles.title}>
          {title}
        </AppText>
        <AppText color={tone.text} style={styles.body}>
          {body}
        </AppText>
      </View>
      <Ionicons name="chevron-forward" size={20} color={tone.chevron} style={styles.chevron} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 11,
    paddingLeft: 12,
    paddingRight: 10,
  },
  pressed: { opacity: 0.85, transform: [{ scale: 0.99 }] },
  tile: { width: 56, height: 56, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  text: { flex: 1, marginLeft: 18 },
  title: { fontSize: 16, lineHeight: 20, fontWeight: "700" },
  body: { fontSize: 13, lineHeight: 17, fontWeight: "400", marginTop: 4 },
  chevron: { marginLeft: 8 },
});
