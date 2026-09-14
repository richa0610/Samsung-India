import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type ProfileSectionProps = {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  editing: boolean;
  saving?: boolean;
  onToggleEdit: () => void;
  children: React.ReactNode;
};

export function ProfileSection({ icon, title, editing, saving, onToggleEdit, children }: ProfileSectionProps) {
  return (
    <AppCard style={styles.card}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Ionicons name={icon} size={16} color={Colors.mainColour1} />
          <AppText style={styles.title} color={Colors.mainColour1} weight={FontWeight.semiBold}>
            {title}
          </AppText>
        </View>
        <Pressable style={styles.editButton} onPress={onToggleEdit} disabled={saving} hitSlop={4}>
          {saving ? (
            <ActivityIndicator size="small" color={Colors.gray600} />
          ) : (
            <>
              <Ionicons name={editing ? "checkmark" : "create-outline"} size={13} color={Colors.gray600} />
              <AppText style={styles.editButtonText} color={Colors.gray600}>{editing ? "SAVE" : "EDIT"}</AppText>
            </>
          )}
        </Pressable>
      </View>
      {children}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16, marginBottom: 14 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 14 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  title: { fontSize: Fonts.bodyLg },
  editButton: { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, paddingVertical: 4 },
  editButtonText: { fontSize: Fonts.overline },
});
