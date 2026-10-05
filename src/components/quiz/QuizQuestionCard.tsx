import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import QuizExplanation from "./QuizExplanation";
import QuizOption from "./QuizOption";
import QuizProgress from "./QuizProgress";

export type QuizQuestionData = {
  id: string | number;
  question: string;
  options: { id: string; text: string }[];
  currentQuestion: number;
  totalQuestions: number;
  correctAnswer?: string | null;
  explanation?: string | null;
};

export type QuizQuestionCardProps = {
  question: QuizQuestionData;
  selectedOptionId?: string | null;
  onSelectOption: (optionId: string) => void;
  disabled?: boolean;
  isResultMode?: boolean;
  correctOptionId?: string | null;
  explanation?: string | null;
};

export default function QuizQuestionCard({
  question,
  selectedOptionId,
  onSelectOption,
  disabled = false,
  isResultMode = false,
  correctOptionId,
  explanation,
}: QuizQuestionCardProps) {
  const correctId = correctOptionId ?? question.correctAnswer;
  const expl = explanation ?? question.explanation;

  return (
    <View style={styles.card}>
      {/* Question Number Badge */}
      <QuizProgress
        currentQuestion={question.currentQuestion}
        totalQuestions={question.totalQuestions}
      />

      {/* Question Text */}
      <AppText
        style={styles.questionText}
        color={Colors.black}
        weight={FontWeight.bold}
      >
        {question.question}
      </AppText>

      {/* Options List */}
      <View style={styles.optionsList}>
        {question.options.map((option, index) => {
          // Letters A, B, C, D...
          const letter = String.fromCharCode(65 + index);
          const isSelected = selectedOptionId === option.id;
          const isCorrect = isResultMode && correctId === option.id;
          const isYourAnswer =
            isResultMode && isSelected && correctId !== option.id;

          const badge = isCorrect
            ? "correct"
            : isYourAnswer
              ? "yourAnswer"
              : null;

          return (
            <QuizOption
              key={option.id}
              letter={letter}
              text={option.text}
              isSelected={isSelected}
              disabled={disabled || isResultMode}
              onSelect={() => onSelectOption(option.id)}
              isResultMode={isResultMode}
              badge={badge}
            />
          );
        })}
      </View>

      {/* Explanation Box (when in Result Mode) */}
      {isResultMode && expl ? <QuizExplanation explanation={expl} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "100%",
    maxWidth: "100%",
    backgroundColor: Colors.white,
    borderRadius: 18,
    padding: 16,
    ...createShadow({ x: 0, y: 2, blur: 8, opacity: 0.06, elevation: 2 }),
  },
  badgeContainer: {
    alignSelf: "flex-start",
    backgroundColor: "#DDEEFF",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 12,
    letterSpacing: 0.2,
  },
  questionText: {
    fontSize: 16,
    lineHeight: 23,
    marginTop: 12,
    marginBottom: 4,
  },
  optionsList: {
    width: "100%",
    maxWidth: "100%",
    marginTop: 6,
  },
});
