import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { ReactNode } from "react";
import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

type StatCardProps = {
  icon: ReactNode;
  iconBg: string;
  title: string;
  value: number | string;
  valueColor: string;
  subtext: string;
  subtextColor?: string;
  isActive?: boolean;
};

export default function StatCard({
  icon,
  iconBg,
  title,
  value,
  valueColor,
  subtext,
  subtextColor = "#9CA3AF",
  isActive = false,
}: StatCardProps) {
  return (
    <View style={[styles.card, isActive && styles.activeCard]}>
      <View style={[styles.iconWrapper, { backgroundColor: iconBg }]}>
        {icon}
      </View>
      <AppText style={styles.title} numberOfLines={1}>
        {title}
      </AppText>
      <AppText style={[styles.value, { color: valueColor }]}>{value}</AppText>
      <AppText style={[styles.subtext, { color: subtextColor }]} numberOfLines={1}>
        {subtext}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 14,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    paddingVertical: 3,
    paddingHorizontal: 2,
    gap: 1,
    alignItems: "center",
    justifyContent: "center",
    ...Shadows.card,
  },
  activeCard: {
    borderColor: Colors.mainColour1,
    borderWidth: 1.6,
  },
  iconWrapper: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 8.5,
    color: "#6B7280",
    marginTop: 5,
    textAlign: "center",
    fontWeight: "500",
  },
  value: {
    fontSize: 15,
    fontWeight: "700",
    marginTop: 2,
    textAlign: "center",
  },
  subtext: {
    fontSize: 8,
    marginTop: 1,
    textAlign: "center",
    fontWeight: "400",
  },
});
