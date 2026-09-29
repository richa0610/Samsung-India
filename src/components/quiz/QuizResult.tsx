import { ScrollView, StyleSheet } from "react-native";

import QuizQuestionCard, { QuizQuestionData } from "./QuizQuestionCard";
import QuizResultHero, { QuizResultType } from "./QuizResultHero";

export type QuizResultProps = {
  type: QuizResultType;
  question: QuizQuestionData;
  selectedOptionId?: string | null;
  correctOptionId?: string | null;
  explanation?: string | null;
  heroTitle?: string;
  heroSubtitle?: string;
};

export default function QuizResult({
  type,
  question,
  selectedOptionId,
  correctOptionId,
  explanation,
  heroTitle,
  heroSubtitle,
}: QuizResultProps) {
  const correctId = correctOptionId ?? question.correctAnswer ?? "A";
  const expl = explanation ?? question.explanation;

  return (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      {/* Result Hero Header (Correct / Incorrect / Time's Up) */}
      <QuizResultHero type={type} title={heroTitle} subtitle={heroSubtitle} />

      {/* Question Card in Result State */}
      <QuizQuestionCard
        question={question}
        selectedOptionId={selectedOptionId}
        onSelectOption={() => {}}
        disabled={true}
        isResultMode={true}
        correctOptionId={correctId}
        explanation={expl}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    width: "100%",
    maxWidth: "100%",
    paddingHorizontal: 16,
    paddingTop: 4,
    paddingBottom: 8,
    justifyContent: "space-between",
  },
});
