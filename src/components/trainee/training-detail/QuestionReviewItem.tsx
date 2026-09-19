import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import { TrainingQuestionAttempt } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

type QuestionReviewItemProps = {
  index: number;
  attempt: TrainingQuestionAttempt;
};

// Surveys carry no correct answer (correctOptionId is null) - options then
// just show the trainee's pick with a neutral highlight, no right/wrong
// styling, since there's nothing to grade.
export default function QuestionReviewItem({ index, attempt }: QuestionReviewItemProps) {
  const hasAnswerKey = !!attempt.correctOptionId;

  return (
    <View style={styles.container}>
      <View style={styles.questionHeader}>
        <AppText variant="caption" weight={FontWeight.bold} color="#111827" style={styles.questionText}>
          {index}. {attempt.question}
        </AppText>
        {hasAnswerKey &&
          (attempt.answered ? (
            <Ionicons
              name={attempt.isCorrect ? "checkmark-circle" : "close-circle"}
              size={18}
              color={attempt.isCorrect ? "#059669" : "#DC2626"}
            />
          ) : (
            <Ionicons name="remove-circle-outline" size={18} color="#9CA3AF" />
          ))}
      </View>

      <View style={styles.optionList}>
        {attempt.options.map((option) => {
          const isSelected = option.id === attempt.selectedOptionId;
          const isCorrectOption = hasAnswerKey && option.id === attempt.correctOptionId;

          let style = styles.optionNeutral;
          let textColor = "#374151";
          if (hasAnswerKey) {
            if (isSelected && isCorrectOption) {
              style = styles.optionCorrect;
              textColor = "#059669";
            } else if (isSelected && !isCorrectOption) {
              style = styles.optionWrong;
              textColor = "#DC2626";
            } else if (isCorrectOption) {
              style = styles.optionCorrect;
              textColor = "#059669";
            }
          } else if (isSelected) {
            style = styles.optionSelected;
            textColor = "#1D4ED8";
          }

          return (
            <View key={option.id} style={[styles.optionRow, style]}>
              <AppText variant="caption" color={textColor} style={styles.optionText}>
                {option.text}
              </AppText>
              {isSelected && <AppText variant="tiny" color={textColor}>Your answer</AppText>}
              {hasAnswerKey && isCorrectOption && !isSelected && (
                <AppText variant="tiny" color="#059669">
                  Correct answer
                </AppText>
              )}
            </View>
          );
        })}
        {!attempt.answered && (
          <AppText variant="tiny" color="#9CA3AF" style={styles.notAnswered}>
            Not answered
          </AppText>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
  },
  questionHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 8,
  },
  questionText: { flex: 1, lineHeight: 18 },
  optionList: { marginTop: 8, gap: 6 },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: Radius.lg,
    borderWidth: 1,
  },
  optionText: { flex: 1 },
  optionNeutral: { backgroundColor: "#F9FAFB", borderColor: "#E5E7EB" },
  optionSelected: { backgroundColor: "#EFF6FF", borderColor: "#BFDBFE" },
  optionCorrect: { backgroundColor: "#ECFDF5", borderColor: "#A7F3D0" },
  optionWrong: { backgroundColor: "#FEF2F2", borderColor: "#FECACA" },
  notAnswered: { marginTop: 2 },
});
