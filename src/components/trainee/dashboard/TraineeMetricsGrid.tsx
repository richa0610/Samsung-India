import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";

import { TraineeMetricCard } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

/** A metric card: Total Trainings or one of the cards each training counts toward. */
export type TraineeMetricCardKey = "total" | TraineeMetricCard;

/** Each card's title - also how Training History names the card it was opened from. */
export const TRAINEE_METRIC_LABELS: Record<TraineeMetricCardKey, string> = {
  total: "Total Trainings",
  present: "Present",
  absent: "Absent",
  scheduled: "Scheduled",
  ongoing: "Ongoing",
  notStarted: "Not Started",
};

export type TraineeMetricsProps = {
  totalTrainings?: number;
  presentCount?: number;
  absentCount?: number;
  scheduledCount?: number;
  notStartedCount?: number;
  ongoingCount?: number;
  /** Tapping a card opens the trainings it counted (as the trainer's Home stat cards do). */
  onPressCard?: (card: TraineeMetricCardKey) => void;
};

export default function TraineeMetricsGrid({
  totalTrainings = 0,
  presentCount = 0,
  absentCount = 0,
  scheduledCount = 0,
  notStartedCount = 0,
  ongoingCount = 0,
  onPressCard,
}: TraineeMetricsProps) {
  const cards: {
    key: TraineeMetricCardKey;
    value: number;
    valueColor: string;
    iconName: keyof typeof Ionicons.glyphMap;
    iconColor: string;
    iconBg: string;
  }[] = [
    {
      key: "total",
      value: totalTrainings,
      valueColor: Colors.blueAccent,
      iconName: "school",
      iconColor: Colors.blueAccent,
      iconBg: Colors.blue50,
    },
    {
      key: "present",
      value: presentCount,
      valueColor: Colors.success,
      iconName: "calendar-outline",
      iconColor: Colors.success,
      iconBg: Colors.successBgSoft,
    },
    {
      key: "absent",
      value: absentCount,
      valueColor: Colors.danger,
      iconName: "person-remove-outline",
      iconColor: Colors.danger,
      iconBg: Colors.dangerBgSoft,
    },
    {
      key: "scheduled",
      value: scheduledCount,
      valueColor: "#EA580C",
      iconName: "calendar-number-outline",
      iconColor: "#EA580C",
      iconBg: "#FFF7ED",
    },
    {
      key: "ongoing",
      value: ongoingCount,
      valueColor: "#0EA5E9",
      iconName: "radio-outline",
      iconColor: "#0EA5E9",
      iconBg: "#F0F9FF",
    },
    {
      key: "notStarted",
      value: notStartedCount,
      valueColor: "#7C3AED",
      iconName: "alert-circle-outline",
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
        <Pressable
          key={card.key}
          onPress={onPressCard ? () => onPressCard(card.key) : undefined}
          disabled={!onPressCard}
          style={({ pressed }) => [styles.card, pressed && styles.pressedCard]}
          accessibilityRole={onPressCard ? "button" : undefined}
          accessibilityLabel={`${TRAINEE_METRIC_LABELS[card.key]}: ${card.value}`}
        >
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
            {TRAINEE_METRIC_LABELS[card.key]}
          </AppText>
        </Pressable>
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
  pressedCard: {
    opacity: 0.75,
    transform: [{ scale: 0.96 }],
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
