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
      valueColor: Colors.blueAccent,
      iconName: "school" as const,
      iconColor: Colors.blueAccent,
      iconBg: Colors.blue50,
    },
    {
      title: "Present",
      value: presentCount,
      valueColor: Colors.success,
      iconName: "calendar-outline" as const,
      iconColor: Colors.success,
      iconBg: Colors.successBgSoft,
    },
    {
      title: "Absent",
      value: absentCount,
      valueColor: Colors.danger,
      iconName: "person-remove-outline" as const,
      iconColor: Colors.danger,
      iconBg: Colors.dangerBgSoft,
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
            color={Colors.gray600}
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
    borderColor: Colors.gray200,
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
