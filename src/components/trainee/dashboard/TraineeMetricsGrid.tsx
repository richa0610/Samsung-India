import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

export type TraineeMetricsProps = {
  totalTrainings?: number;
  presentCount?: number;
  absentCount?: number;
  scheduledCount?: number;
};

export default function TraineeMetricsGrid({
  totalTrainings = 0,
  presentCount = 0,
  absentCount = 0,
  scheduledCount = 0,
}: TraineeMetricsProps) {
  const cards = [
    {
      title: "Total Trainings",
      value: totalTrainings,
      subtitle: "All Time",
      valueColor: "#2563EB",
      iconName: "school" as const,
      iconColor: "#2563EB",
      iconBg: "#EFF6FF",
    },
    {
      title: "Present",
      value: presentCount,
      subtitle: "This Period",
      valueColor: "#16A34A",
      iconName: "calendar-outline" as const,
      iconColor: "#16A34A",
      iconBg: "#ECFDF5",
    },
    {
      title: "Absent",
      value: absentCount,
      subtitle: "This Period",
      valueColor: "#DC2626",
      iconName: "person-remove-outline" as const,
      iconColor: "#DC2626",
      iconBg: "#FEF2F2",
    },
    {
      title: "Assigned / Scheduled",
      value: scheduledCount,
      subtitle: "This Period",
      valueColor: "#EA580C",
      iconName: "calendar-number-outline" as const,
      iconColor: "#EA580C",
      iconBg: "#FFF7ED",
    },
  ];

  return (
    <View style={styles.grid}>
      {cards.map((card) => (
        <View key={card.title} style={styles.card}>
          <View style={[styles.iconCircle, { backgroundColor: card.iconBg }]}>
            <Ionicons name={card.iconName} size={18} color={card.iconColor} />
          </View>
          <AppText
            variant="tiny"
            color="#4B5563"
            weight={FontWeight.medium}
            style={styles.title}
            numberOfLines={1}
          >
            {card.title}
          </AppText>
          <AppText
            variant="h2"
            weight={FontWeight.bold}
            style={[styles.value, { color: card.valueColor }]}
          >
            {card.value}
          </AppText>
          <AppText variant="tiny" color="#9CA3AF" style={styles.subtitle}>
            {card.subtitle}
          </AppText>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    marginTop: 14,
  },
  card: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    paddingVertical: 12,
    paddingHorizontal: 6,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    ...Shadows.card,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 6,
  },
  title: {
    fontSize: 9.5,
    textAlign: "center",
  },
  value: {
    fontSize: 20,
    marginVertical: 2,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 8.5,
    textAlign: "center",
  },
});
