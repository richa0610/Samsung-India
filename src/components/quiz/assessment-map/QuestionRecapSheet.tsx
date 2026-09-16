import { Ionicons } from "@expo/vector-icons";
import { Modal, Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { LiveQuizSummaryQuestion } from "@/api/session";
import QuizResult from "@/components/quiz/QuizResult";
import { QuizResultType } from "@/components/quiz/QuizResultHero";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type QuestionRecapSheetProps = {
  visible: boolean;
  questions: LiveQuizSummaryQuestion[];
  index: number;
  onClose: () => void;
  onStep: (delta: number) => void;
};

function recapType(q: LiveQuizSummaryQuestion): QuizResultType {
  if (q.status === "attempted") {
    return q.yourOptionId && q.yourOptionId === q.correctOptionId ? "correct" : "incorrect";
  }
  return "timeout";
}

export default function QuestionRecapSheet({
  visible,
  questions,
  index,
  onClose,
  onStep,
}: QuestionRecapSheetProps) {
  const question = questions[index];
  if (!question) return null;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose} transparent={false}>
      <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
        <View style={styles.header}>
          <Pressable onPress={onClose} hitSlop={8} accessibilityRole="button" accessibilityLabel="Close recap">
            <Ionicons name="close" size={24} color={Colors.gray600} />
          </Pressable>
          <AppText weight={FontWeight.bold} style={styles.headerTitle}>
            Question {question.order} of {questions.length}
          </AppText>
          <View style={styles.stepRow}>
            <Pressable
              onPress={() => onStep(-1)}
              disabled={index === 0}
              hitSlop={8}
              style={index === 0 && styles.stepDisabled}
              accessibilityRole="button"
              accessibilityLabel="Previous question"
            >
              <Ionicons name="chevron-back" size={22} color={Colors.headerBlue} />
            </Pressable>
            <Pressable
              onPress={() => onStep(1)}
              disabled={index === questions.length - 1}
              hitSlop={8}
              style={index === questions.length - 1 && styles.stepDisabled}
              accessibilityRole="button"
              accessibilityLabel="Next question"
            >
              <Ionicons name="chevron-forward" size={22} color={Colors.headerBlue} />
            </Pressable>
          </View>
        </View>

        <QuizResult
          type={recapType(question)}
          heroTitle={question.status === "skipped" ? "Not answered" : undefined}
          heroSubtitle={
            question.status === "skipped" ? "This question didn't reach you during the quiz" : undefined
          }
          question={{
            id: question.id,
            question: question.text,
            options: question.options,
            currentQuestion: question.order,
            totalQuestions: questions.length,
            correctAnswer: question.correctOptionId,
            explanation: question.explanation,
          }}
          selectedOptionId={question.yourOptionId}
          correctOptionId={question.correctOptionId}
          explanation={question.explanation}
        />
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  headerTitle: { fontSize: 15 },
  stepRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  stepDisabled: { opacity: 0.3 },
});
