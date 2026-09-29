import { ReactNode } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleProp, StyleSheet, View, ViewStyle } from "react-native";

import AppText from "@/components/ui/AppText";
import ProgressRing from "@/components/ui/ProgressRing";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";

export type AdminStatSubItem = {
  label: string;
  value: string;
  color?: string;
};

export type AdminStatCardProps = {
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  /** Card's signature colour - tints the icon tile, badge and accent bar. */
  accent: string;
  badgeLabel: string;
  bigNumber: number | string;
  bigLabel: string;
  ringPercentage: number;
  ringValue?: number | string;
  ringColor: string;
  ringTrackColor?: string;
  ringContent?: ReactNode;
  subItems: AdminStatSubItem[];
  linkLabel: string;
  onPressLink?: () => void;
  expandedContent?: ReactNode;
  isExpanded?: boolean;
  style?: StyleProp<ViewStyle>;
};

export default function AdminStatCard({
  title,
  icon,
  accent,
  badgeLabel,
  bigNumber,
  bigLabel,
  ringPercentage,
  ringValue,
  ringColor,
  ringTrackColor,
  ringContent,
  subItems,
  linkLabel,
  onPressLink,
  expandedContent,
  isExpanded,
  style,
}: AdminStatCardProps) {
  // With nothing to show (a zero total) the ring would only be an empty coloured
  // circle, so it's dropped and just the number is shown, at the same size.
  const hasData = Number(ringValue ?? bigNumber) !== 0;
  const ringLabel = ringContent ?? (
    <AppText variant="caption" weight={FontWeight.bold} color={Colors.black}>
      {ringValue}
    </AppText>
  );

  return (
    <View style={[styles.card, style]}>
      <View style={[styles.accentBar, { backgroundColor: accent }]} />
      <View style={styles.headerRow}>
        <View style={styles.titleGroup}>
          <View style={[styles.iconTile, { backgroundColor: `${accent}1F` }]}>
            <Ionicons name={icon} size={16} color={accent} />
          </View>
          <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray700} style={styles.title}>
            {title}
          </AppText>
        </View>
        <View style={[styles.badge, { backgroundColor: `${accent}1A` }]}>
          <AppText variant="tiny" weight={FontWeight.bold} color={accent}>
            {badgeLabel}
          </AppText>
        </View>
      </View>

      <View style={styles.mainRow}>
        <View style={styles.bigNumberColumn}>
          <AppText weight={FontWeight.bold} color={Colors.black} style={styles.bigNumber}>
            {bigNumber}
          </AppText>
          <AppText variant="tiny" weight={FontWeight.bold} color={Colors.gray400} style={styles.bigLabel}>
            {bigLabel}
          </AppText>
        </View>

        {hasData ? (
          <ProgressRing
            percentage={ringPercentage}
            color={ringColor}
            trackColor={ringTrackColor}
            size={50}
            strokeWidth={5.5}
          >
            {ringLabel}
          </ProgressRing>
        ) : (
          <View style={styles.emptyRing}>{ringLabel}</View>
        )}
      </View>

      <View style={styles.subRow}>
        {subItems.map((item) => (
          <View key={item.label} style={[styles.subItem, { backgroundColor: `${item.color ?? Colors.gray500}12` }]}>
            <AppText variant="tiny" weight={FontWeight.bold} color={item.color ?? Colors.gray700} numberOfLines={1}>
              {item.label}
            </AppText>
            <AppText variant="caption" weight={FontWeight.bold} color={Colors.black}>
              {item.value}
            </AppText>
          </View>
        ))}
      </View>

      {onPressLink && (
        <>
          <View style={styles.divider} />
          <Pressable onPress={onPressLink} hitSlop={6} accessibilityRole="button" accessibilityLabel={linkLabel}>
            <View style={styles.linkRow}>
              <AppText variant="caption" weight={FontWeight.bold} color={accent} align="center">
                {linkLabel}
              </AppText>
              <Ionicons name={isExpanded ? "chevron-up" : "chevron-down"} size={14} color={accent} />
            </View>
          </Pressable>
          {isExpanded && expandedContent}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  emptyRing: { width: 50, height: 50, alignItems: "center", justifyContent: "center" },
  card: {
    width: "100%",
    backgroundColor: Colors.white,
    borderRadius: Radius.xxxl,
    borderWidth: 1,
    borderColor: Colors.gray200,
    paddingVertical: 10,
    paddingLeft: 14,
    paddingRight: 12,
    overflow: "hidden",
    ...Shadows.card,
  },
  accentBar: { position: "absolute", left: 0, top: 0, bottom: 0, width: 4 },
  titleGroup: { flexDirection: "row", alignItems: "center", gap: 8 },
  iconTile: {
    width: 26,
    height: 26,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  linkRow: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4 },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    letterSpacing: 0.3,
  },
  badge: {
    borderRadius: Radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  mainRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 2,
  },
  bigNumberColumn: { gap: 0 },
  bigNumber: { fontSize: 26, lineHeight: 28 },
  bigLabel: { letterSpacing: 0.3 },
  subRow: {
    flexDirection: "row",
    marginTop: 8,
    gap: 6,
  },
  subItem: { flex: 1, gap: 1, alignItems: "center", borderRadius: Radius.xl, paddingVertical: 5 },
  divider: {
    height: 1,
    backgroundColor: Colors.slate100,
    marginTop: 7,
    marginBottom: 6,
  },
});
