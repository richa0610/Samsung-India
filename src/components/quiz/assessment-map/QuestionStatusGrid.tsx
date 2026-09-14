import { Pressable, StyleSheet, View } from "react-native";

import { LiveQuizSummaryQuestion } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";

type QuestionStatusGridProps = {
  questions: LiveQuizSummaryQuestion[];
  onSelectQuestion: (index: number) => void;
};

export default function QuestionStatusGrid({ questions, onSelectQuestion }: QuestionStatusGridProps) {
  return (
    <View style={styles.grid}>
      {questions.map((question, index) => {
        const tone =
          question.status === "attempted"
            ? styles.attempted
            : question.status === "timed_out"
              ? styles.expired
              : styles.skipped;
        const textTone =
          question.status === "attempted"
            ? styles.attemptedText
            : question.status === "timed_out"
              ? styles.expiredText
              : styles.skippedText;

        return (
          <Pressable
            key={question.id}
            onPress={() => onSelectQuestion(index)}
            style={({ pressed }) => [styles.tile, tone, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel={`Question ${question.order}: ${question.status.replace("_", " ")}`}
          >
            <AppText style={[styles.tileText, textTone]} weight={FontWeight.bold}>
              {question.order}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "flex-start",
    gap: 12,
    marginTop: 14,
  },
  tile: {
    width: 52,
    height: 52,
    borderRadius: 10,
    borderWidth: 1.2,
    alignItems: "center",
    justifyContent: "center",
  },
  pressed: { opacity: 0.75, transform: [{ scale: 0.96 }] },
  attempted: { backgroundColor: "#E8F8EF", borderColor: "#81D1AD" },
  skipped: { backgroundColor: "#FEF9C3", borderColor: "#FDE047" },
  expired: { backgroundColor: "#FEE2E2", borderColor: "#FCA5A5" },
  tileText: { fontSize: 18 },
  attemptedText: { color: "#00A859" },
  skippedText: { color: "#D97706" },
  expiredText: { color: "#EF4444" },
});
