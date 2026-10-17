import React from "react";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type QuizProgressProps = {
  currentQuestion: number;
  totalQuestions: number;
};

export default function QuizProgress({
  currentQuestion,
  totalQuestions,
}: QuizProgressProps) {
  return (
    <View style={styles.badgeContainer}>
      <AppText
        style={styles.badgeText}
        color={Colors.headerBlue}
        weight={FontWeight.bold}
      >
        Question {currentQuestion} of {totalQuestions}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badgeContainer: {
    alignSelf: "flex-start",
    backgroundColor: "#DDEEFF",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 10.5,
    letterSpacing: 0.2,
  },
});

