import { Ionicons } from "@expo/vector-icons";
import { ReactNode } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";

type DashboardSectionCardProps = {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  badge?: ReactNode;
  loading: boolean;
  isEmpty: boolean;
  emptyIcon: keyof typeof Ionicons.glyphMap;
  emptyText: string;
  children: ReactNode;
};

export default function DashboardSectionCard({
  icon,
  title,
  badge,
  loading,
  isEmpty,
  emptyIcon,
  emptyText,
  children,
}: DashboardSectionCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHeaderRow}>
        <Ionicons name={icon} size={18} color={Colors.mainColour1} />
        <AppText style={styles.cardTitle} weight={FontWeight.medium}>
          {title}
        </AppText>
        {badge}
      </View>

      {loading ? (
        <ActivityIndicator color={Colors.mainColour1} style={styles.loadingSpinner} />
      ) : isEmpty ? (
        <View style={styles.emptyState}>
          <Ionicons name={emptyIcon} size={32} color={Colors.gray400} />
          <AppText style={styles.emptyText} color={Colors.gray600}>
            {emptyText}
          </AppText>
        </View>
      ) : (
        children
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xxl,
    padding: 16,
    ...Shadows.card,
  },
  cardHeaderRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  cardTitle: { fontSize: Fonts.body, flex: 1 },
  loadingSpinner: { marginVertical: 20 },
  emptyState: { alignItems: "center", gap: 6, paddingVertical: 20 },
  emptyText: { fontSize: Fonts.bodySm, textAlign: "center" },
});
