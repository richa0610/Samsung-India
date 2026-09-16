import React from "react";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { SurveyQuestion } from "./types";
import SurveyRadioOption from "./SurveyRadioOption";
import SurveyTextInput from "./SurveyTextInput";

export type SurveyQuestionCardProps = {
  question: SurveyQuestion;
  index: number;
  total: number;
  value: string;
  onChange: (value: string) => void;
  hasError?: boolean;
};

export default function SurveyQuestionCard({
  question,
  index,
  total,
  value,
  onChange,
  hasError = false,
}: SurveyQuestionCardProps) {
  const isTextType = question.type === "text";

  return (
    <View style={[styles.card, hasError && styles.cardError]}>
      {/* Question Number Badge */}
      <View style={styles.badge}>
        <AppText style={styles.badgeText} weight={FontWeight.medium}>
          Question {index + 1} of {total}
        </AppText>
      </View>

      {/* Question Title */}
      <AppText
        style={styles.questionText}
        color={Colors.black}
        weight={FontWeight.bold}
      >
        {question.question}
      </AppText>

      {/* Answer Content */}
      {isTextType ? (
        <SurveyTextInput
          value={value}
          onChangeText={onChange}
          hasError={hasError}
        />
      ) : (
        <View style={styles.optionsList}>
          {question.options?.map((option) => (
            <SurveyRadioOption
              key={option.id}
              id={option.id}
              text={option.text}
              selected={value === option.id || value === option.text}
              onSelect={() => onChange(option.id)}
            />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: "#80BAFF",
    padding: 16,
    marginBottom: 14,
    ...createShadow({ x: 0, y: 2, blur: 6, opacity: 0.04, elevation: 2 }),
  },
  cardError: {
    borderColor: Colors.danger,
  },
  badge: {
    backgroundColor: "#DDEEFF",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: "flex-start",
  },
  badgeText: {
    fontSize: 10.5,
    color: "#006AFF",
  },
  questionText: {
    fontSize: 14.5,
    lineHeight: 21,
    marginTop: 10,
    marginBottom: 14,
  },
  optionsList: {
    gap: 8,
  },
});
