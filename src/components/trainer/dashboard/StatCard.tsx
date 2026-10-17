import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { ReactNode } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

type StatCardProps = {
  icon: ReactNode;
  iconBg: string;
  title: string;
  value: number | string;
  valueColor: string;
  subtext?: string;
  subtextColor?: string;
  isActive?: boolean;
  onPress?: () => void;
};

export default function StatCard({
  icon,
  iconBg,
  title,
  value,
  valueColor,
  subtext,
  subtextColor = Colors.gray400,
  isActive = false,
  onPress,
}: StatCardProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={({ pressed }) => [
        styles.card,
        isActive && styles.activeCard,
        pressed && styles.pressedCard,
      ]}
      accessibilityRole={onPress ? "button" : undefined}
      accessibilityLabel={`${title}: ${value}`}
    >
      <View style={[styles.iconWrapper, { backgroundColor: iconBg }]}>
        {icon}
      </View>
      <AppText style={styles.title} numberOfLines={1}>
        {title}
      </AppText>
      <AppText style={[styles.value, { color: valueColor }]}>{value}</AppText>
      {subtext ? (
        <AppText style={[styles.subtext, { color: subtextColor }]} numberOfLines={1}>
          {subtext}
        </AppText>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 14,
    borderWidth: 1.2,
    borderColor: Colors.borderLight,
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
  pressedCard: {
    opacity: 0.75,
    transform: [{ scale: 0.96 }],
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
    color: Colors.gray500,
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
