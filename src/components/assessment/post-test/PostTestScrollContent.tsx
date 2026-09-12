import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { usePostTest } from "@/hooks/usePostTest";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontSize, FontWeight, LineHeight } from "@/theme/typography";
import PostTestQuestionCard from "./PostTestQuestionCard";
import TestProgressRow from "./TestProgressRow";

type PostTestScrollContentProps = {
  postTest: ReturnType<typeof usePostTest>;
};

export default function PostTestScrollContent({ postTest }: PostTestScrollContentProps) {
  const {
    totalMinutes,
    remainingMinutes,
    remainingSecondsPart,
    token,
    isActive,
    violationModalVisible,
    testStatus,
    violationCount,
    currentViolation,
    triggerViolation,
    triggerSoftWarning,
    suiteTitle,
    current,
    questionIndex,
    questions,
    selectedOption,
    isLastQuestion,
    isSubmitting,
    error,
    selectOption,
    move,
    handleSubmit,
  } = postTest;

  if (!current) return null;

  return (
    <>
      <TestProgressRow
        totalMinutes={totalMinutes}
        remainingMinutes={remainingMinutes}
        remainingSecondsPart={remainingSecondsPart}
        token={token}
        isActive={isActive}
        paused={violationModalVisible || testStatus !== "active"}
        violationCount={violationCount}
        currentViolation={currentViolation}
        onViolation={triggerViolation}
        onWarning={triggerSoftWarning}
      />

      <View style={styles.testTitle}>
        <AppText style={styles.title} weight={FontWeight.semiBold}>
          {suiteTitle ?? "MX Training Offline\nPost Test ( July 2026 )"}
        </AppText>
      </View>

      <PostTestQuestionCard
        current={current}
        questionIndex={questionIndex}
        questionsLength={questions.length}
        selectedOption={selectedOption}
        isActive={isActive}
        isLastQuestion={isLastQuestion}
        isSubmitting={isSubmitting}
        error={error}
        onSelectOption={selectOption}
        onPrevious={() => move(-1)}
        onNext={() => (isLastQuestion ? handleSubmit() : move(1))}
      />
    </>
  );
}

const styles = StyleSheet.create({
  testTitle: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 16,
    backgroundColor: Colors.white,
    ...createShadow({ x: 0, y: 2, blur: 8, opacity: 0.06, elevation: 2, color: "#000000" }),
  },
  title: {
    fontSize: FontSize.body,
    lineHeight: LineHeight.h2,
    textAlign: "center",
    color: "#111827",
  },
});
