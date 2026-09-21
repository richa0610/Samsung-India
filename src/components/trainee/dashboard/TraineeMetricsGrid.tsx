import { Ionicons } from "@expo/vector-icons";
import { ScrollView, StyleSheet, View } from "react-native";

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
  notStartedCount?: number;
  ongoingCount?: number;
};

export default function TraineeMetricsGrid({
  totalTrainings = 0,
  presentCount = 0,
  absentCount = 0,
  scheduledCount = 0,
  notStartedCount = 0,
  ongoingCount = 0,
}: TraineeMetricsProps) {
  const cards = [
    {
      title: "Total Trainings",
      value: totalTrainings,
      valueColor: "#2563EB",
      iconName: "school" as const,
      iconColor: "#2563EB",
      iconBg: "#EFF6FF",
    },
    {
      title: "Present",
      value: presentCount,
      valueColor: "#16A34A",
      iconName: "calendar-outline" as const,
      iconColor: "#16A34A",
      iconBg: "#ECFDF5",
    },
    {
      title: "Absent",
      value: absentCount,
      valueColor: "#DC2626",
      iconName: "person-remove-outline" as const,
      iconColor: "#DC2626",
      iconBg: "#FEF2F2",
    },
    {
      title: "Scheduled",
      value: scheduledCount,
      valueColor: "#EA580C",
      iconName: "calendar-number-outline" as const,
      iconColor: "#EA580C",
      iconBg: "#FFF7ED",
    },
    {
      title: "Ongoing",
      value: ongoingCount,
      valueColor: "#0EA5E9",
      iconName: "radio-outline" as const,
      iconColor: "#0EA5E9",
      iconBg: "#F0F9FF",
    },
    {
      title: "Not Started",
      value: notStartedCount,
      valueColor: "#7C3AED",
      iconName: "alert-circle-outline" as const,
      iconColor: "#7C3AED",
      iconBg: "#F5F3FF",
    },
  ];

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.grid}
      style={styles.scroll}
    >
      {cards.map((card) => (
        <View key={card.title} style={styles.card}>
          <View style={[styles.iconCircle, { backgroundColor: card.iconBg }]}>
            <Ionicons name={card.iconName} size={15} color={card.iconColor} />
          </View>
          <AppText
            variant="h2"
            weight={FontWeight.bold}
            style={[styles.value, { color: card.valueColor }]}
          >
            {card.value}
          </AppText>
          <AppText
            variant="tiny"
            color="#4B5563"
            weight={FontWeight.medium}
            style={styles.title}
            numberOfLines={1}
          >
            {card.title}
          </AppText>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 0, marginTop: 10 },
  grid: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  card: {
    width: 84,
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    paddingVertical: 8,
    paddingHorizontal: 4,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    ...Shadows.card,
  },
  iconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  value: {
    fontSize: 18,
    textAlign: "center",
  },
  title: {
    fontSize: 9.5,
    textAlign: "center",
  },
});
