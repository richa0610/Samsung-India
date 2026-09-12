import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import { AssessmentQuestion } from "@/api/assessment";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontSize, FontWeight, LineHeight } from "@/theme/typography";
import PostTestActions from "./PostTestActions";
import QuestionOptionsList from "./QuestionOptionsList";

type PostTestQuestionCardProps = {
  current: AssessmentQuestion;
  questionIndex: number;
  questionsLength: number;
  selectedOption: string | null;
  isActive: boolean;
  isLastQuestion: boolean;
  isSubmitting: boolean;
  error: string | null;
  onSelectOption: (optionId: string) => void;
  onPrevious: () => void;
  onNext: () => void;
};

export default function PostTestQuestionCard({
  current,
  questionIndex,
  questionsLength,
  selectedOption,
  isActive,
  isLastQuestion,
  isSubmitting,
  error,
  onSelectOption,
  onPrevious,
  onNext,
}: PostTestQuestionCardProps) {
  return (
    <View style={styles.questionCard}>
      <View style={styles.questionBody}>
        <View style={styles.tags}>
          <View style={styles.questionTagWrapper}>
            <AppText style={styles.questionTag} weight={FontWeight.medium}>
              Question {questionIndex + 1} of {questionsLength}
            </AppText>
          </View>
          <View style={styles.multiTagWrapper}>
            <AppText style={styles.multiTag} weight={FontWeight.medium}>
              {current.question_type === "multi" ? "Multi – Select" : "Single Select"}
            </AppText>
          </View>
          <View style={styles.unlimitedTag}>
            <Ionicons name="infinite" size={13} color="#00A859" />
            <AppText style={styles.unlimitedText} weight={FontWeight.medium}>
              Unlimited
            </AppText>
          </View>
        </View>

        <AppText style={styles.question} weight={FontWeight.bold}>
          {current.question}
        </AppText>

        <QuestionOptionsList
          options={current.options}
          selectedOption={selectedOption}
          isActive={isActive}
          onSelect={onSelectOption}
        />

        {error && <AppText style={styles.inlineError}>{error}</AppText>}
      </View>

      <PostTestActions
        questionIndex={questionIndex}
        isLastQuestion={isLastQuestion}
        isActive={isActive}
        isSubmitting={isSubmitting}
        onPrevious={onPrevious}
        onNext={onNext}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  questionCard: {
    flex: 1,
    justifyContent: "space-between",
    borderRadius: 20,
    borderWidth: 2,
    borderColor: "#006AFF",
    overflow: "hidden",
    backgroundColor: Colors.white,
    ...createShadow({ x: 0, y: 4, blur: 12, opacity: 0.08, elevation: 4, color: "#000000" }),
  },
  questionBody: { padding: 14 },
  tags: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  questionTagWrapper: {
    backgroundColor: "#D1E5FF",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  questionTag: {
    fontSize: FontSize.tiny,
    lineHeight: LineHeight.overline,
    color: "#0066FF",
  },
  multiTagWrapper: {
    backgroundColor: "#F1F3F5",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  multiTag: {
    fontSize: FontSize.tiny,
    lineHeight: LineHeight.overline,
    color: "#4B5563",
  },
  unlimitedTag: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    backgroundColor: "#D1F2DE",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  unlimitedText: {
    fontSize: FontSize.tiny,
    lineHeight: LineHeight.overline,
    color: "#00A859",
  },
  question: {
    fontSize: 18,
    lineHeight: LineHeight.body,
    color: "#000000",
    marginVertical: 10,
  },
  inlineError: {
    color: Colors.danger,
    fontSize: FontSize.caption,
    marginTop: 8,
    textAlign: "center",
  },
});
