import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { QuestionOut } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { QUESTION_TYPE_LABELS } from "./constants";

type QuestionCardProps = {
  question: QuestionOut;
  index: number;
  onDelete: (id: number) => void;
};

export default function QuestionCard({ question: q, index, onDelete }: QuestionCardProps) {
  return (
    <View style={styles.questionCard}>
      <View style={styles.questionHeaderRow}>
        <AppText style={styles.questionIndex} color={Colors.mainColour1} weight={FontWeight.semiBold}>
          Q{index + 1}
        </AppText>
        <AppText style={styles.questionTypeTag} color={Colors.gray600}>
          {QUESTION_TYPE_LABELS[q.questionType] ?? q.questionType}
        </AppText>
        <Pressable onPress={() => onDelete(q.id)} hitSlop={8}>
          <Ionicons name="trash-outline" size={18} color={Colors.danger} />
        </Pressable>
      </View>
      <AppText style={styles.questionText} weight={FontWeight.medium}>
        {q.question}
      </AppText>
      {q.options.map((opt) => (
        <View key={opt.id} style={styles.optionRow}>
          <Ionicons
            name={opt.id === q.correctAnswer ? "checkmark-circle" : "ellipse-outline"}
            size={16}
            color={opt.id === q.correctAnswer ? Colors.success : Colors.gray400}
          />
          <AppText style={styles.optionText}>{opt.text}</AppText>
        </View>
      ))}
      <View style={styles.questionMetaRow}>
        <AppText style={styles.questionMeta} color={Colors.gray600}>
          {q.points} pts
        </AppText>
        {q.timerSeconds != null && (
          <AppText style={styles.questionMeta} color={Colors.gray600}>
            {q.timerSeconds}s
          </AppText>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  questionCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xxl,
    padding: 16,
    gap: 8,
    ...Shadows.card,
  },
  questionHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  questionIndex: { fontSize: Fonts.bodySm },
  questionTypeTag: { fontSize: Fonts.overline },
  questionText: { fontSize: Fonts.body, marginVertical: 4 },
  optionRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 2 },
  optionText: { fontSize: Fonts.bodySm },
  questionMetaRow: { flexDirection: "row", gap: 12, marginTop: 6 },
  questionMeta: { fontSize: Fonts.overline },
});
