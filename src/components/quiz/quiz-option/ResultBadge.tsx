import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";

type ResultBadgeProps = {
  isCorrect: boolean;
  isYourAnswer: boolean;
};

export default function ResultBadge({ isCorrect, isYourAnswer }: ResultBadgeProps) {
  if (isCorrect) {
    return (
      <View style={styles.correctBadge}>
        <AppText style={styles.correctBadgeText} weight={FontWeight.bold}>
          Correct Answer
        </AppText>
      </View>
    );
  }

  if (isYourAnswer) {
    return (
      <View style={styles.yourAnswerBadge}>
        <AppText style={styles.yourAnswerBadgeText} weight={FontWeight.bold}>
          Your Answer
        </AppText>
      </View>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  correctBadge: {
    backgroundColor: "#D4F4E4",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    flexShrink: 0,
  },
  correctBadgeText: {
    fontSize: 10,
    color: "#047857",
    letterSpacing: 0.1,
  },
  yourAnswerBadge: {
    backgroundColor: "#FEE2E2",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    flexShrink: 0,
  },
  yourAnswerBadgeText: {
    fontSize: 10,
    color: "#DC2626",
    letterSpacing: 0.1,
  },
});
