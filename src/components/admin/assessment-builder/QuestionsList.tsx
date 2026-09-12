import { Ionicons } from "@expo/vector-icons";
import { Fragment } from "react";
import { StyleSheet, View } from "react-native";

import { QuestionOut } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import QuestionCard from "./QuestionCard";

type QuestionsListProps = {
  questions: QuestionOut[];
  onDeleteQuestion: (id: number) => void;
};

export default function QuestionsList({ questions, onDeleteQuestion }: QuestionsListProps) {
  if (questions.length === 0) {
    return (
      <View style={styles.emptyState}>
        <Ionicons name="help-circle-outline" size={32} color={Colors.gray400} />
        <AppText style={styles.emptyText} color={Colors.gray600}>
          No questions yet. Tap + to add one.
        </AppText>
      </View>
    );
  }

  return (
    <Fragment>
      {questions.map((q, index) => (
        <QuestionCard key={q.id} question={q} index={index} onDelete={onDeleteQuestion} />
      ))}
    </Fragment>
  );
}

const styles = StyleSheet.create({
  emptyState: { alignItems: "center", gap: 6, paddingVertical: 40 },
  emptyText: { fontSize: Fonts.bodySm },
});
