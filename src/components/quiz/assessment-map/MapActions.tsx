import { ActivityIndicator, Pressable, StyleSheet } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type MapActionsProps = {
  onReviewQuestions: () => void;
  onSubmit: () => void;
  submitting: boolean;
};

export default function MapActions({ onReviewQuestions, onSubmit, submitting }: MapActionsProps) {
  return (
    <>
      <Pressable style={styles.reviewButton} onPress={onReviewQuestions} accessibilityRole="button" accessibilityLabel="Review Questions">
        <AppText color={Colors.white} weight={FontWeight.bold}>
          Review Questions
        </AppText>
      </Pressable>

      <Pressable
        style={[styles.submitButton, submitting && styles.buttonDisabled]}
        disabled={submitting}
        onPress={onSubmit}
        accessibilityRole="button"
        accessibilityLabel="Final Submit"
      >
        {submitting ? (
          <ActivityIndicator color={Colors.white} />
        ) : (
          <AppText color={Colors.white} weight={FontWeight.bold}>
            Final Submit
          </AppText>
        )}
      </Pressable>
    </>
  );
}

const styles = StyleSheet.create({
  reviewButton: {
    height: 48,
    borderRadius: 12,
    backgroundColor: Colors.headerBlue,
    alignItems: "center",
    justifyContent: "center",
  },
  submitButton: {
    height: 48,
    borderRadius: 12,
    backgroundColor: "#008744",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 10,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
});
