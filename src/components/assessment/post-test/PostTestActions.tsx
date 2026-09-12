import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontSize, FontWeight } from "@/theme/typography";

type PostTestActionsProps = {
  questionIndex: number;
  isLastQuestion: boolean;
  isActive: boolean;
  isSubmitting: boolean;
  onPrevious: () => void;
  onNext: () => void;
};

export default function PostTestActions({
  questionIndex,
  isLastQuestion,
  isActive,
  isSubmitting,
  onPrevious,
  onNext,
}: PostTestActionsProps) {
  const previousDisabled = questionIndex === 0 || !isActive;
  const nextDisabled = isSubmitting || !isActive;

  return (
    <View style={styles.actions}>
      <Pressable
        disabled={previousDisabled}
        onPress={onPrevious}
        style={[styles.previousButton, previousDisabled && styles.disabledButton]}
      >
        <AppText style={styles.previousText} weight={FontWeight.semiBold}>
          Previous Question
        </AppText>
      </Pressable>

      <Pressable disabled={nextDisabled} onPress={onNext} style={[styles.nextButton, nextDisabled && styles.disabledButton]}>
        {isSubmitting ? (
          <ActivityIndicator color={Colors.white} />
        ) : (
          <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.nextText}>
            {isLastQuestion ? "Submit Test" : "Next Question"}
          </AppText>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  actions: {
    flexDirection: "row",
    gap: 12,
    padding: 14,
    backgroundColor: Colors.white,
  },
  previousButton: {
    flex: 1,
    height: 46,
    borderRadius: 12,
    borderWidth: 1.8,
    borderColor: "#006AFF",
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  previousText: {
    fontSize: FontSize.label,
    color: "#006AFF",
  },
  nextButton: {
    flex: 1,
    height: 46,
    borderRadius: 12,
    backgroundColor: "#006AFF",
    alignItems: "center",
    justifyContent: "center",
  },
  nextText: {
    fontSize: FontSize.label,
    color: Colors.white,
  },
  disabledButton: { opacity: 0.5 },
});
