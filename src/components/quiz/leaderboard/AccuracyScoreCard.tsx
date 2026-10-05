import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

type AccuracyScoreCardProps = {
  accuracy: number;
  correct: number;
  total: number;
  timeTakenFormatted: string;
};

export default function AccuracyScoreCard({ accuracy, correct, total, timeTakenFormatted }: AccuracyScoreCardProps) {
  return (
    <View style={styles.scoreCard}>
      <AppText style={styles.scoreLabel} color={Colors.white} weight={FontWeight.semiBold}>
        Your Live Accuracy
      </AppText>
      <AppText style={styles.scoreValue} color={Colors.white} weight={FontWeight.bold}>
        {accuracy}%
      </AppText>
      <View style={styles.pillsRow}>
        <View style={styles.pillItem}>
          <Ionicons name="disc-outline" size={14} color={Colors.white} />
          <AppText style={styles.pillText} color={Colors.white} weight={FontWeight.semiBold}>
            {correct} / {total} Correct
          </AppText>
        </View>
        <View style={styles.pillItem}>
          <Ionicons name="time-outline" size={14} color={Colors.white} />
          <AppText style={styles.pillText} color={Colors.white} weight={FontWeight.semiBold}>
            {timeTakenFormatted} taken
          </AppText>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  scoreCard: {
    backgroundColor: Colors.headerBlue,
    borderRadius: 16,
    paddingVertical: 18,
    paddingHorizontal: 16,
    alignItems: "center",
    ...createShadow({ x: 0, y: 4, blur: 12, opacity: 0.1, elevation: 3 }),
  },
  scoreLabel: {
    fontSize: 11,
    letterSpacing: 0.5,
    opacity: 0.9,
  },
  scoreValue: {
    fontSize: 42,
    lineHeight: 48,
    marginVertical: 4,
  },
  pillsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 8,
  },
  pillItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "rgba(255, 255, 255, 0.2)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  pillText: {
    fontSize: 11.5,
  },
});
