import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { getOptionBorder, ResultBadge } from "./quiz-option";

export type OptionLetter = "A" | "B" | "C" | "D" | string;

export type QuizOptionItem = {
  id: string;
  text: string;
};

export const OPTION_THEMES: Record<string, { color: string; bg: string; border: string }> = {
  A: { color: "#00A859", bg: "#E8F8EF", border: "#00A859" },
  B: { color: "#006AFF", bg: "#EAF2FF", border: "#006AFF" },
  C: { color: "#EAB308", bg: "#FEF9C3", border: "#FACC15" },
  D: { color: "#EF4444", bg: "#FEE2E2", border: "#EF4444" },
};

export type QuizOptionProps = {
  letter: OptionLetter;
  text: string;
  isSelected?: boolean;
  disabled?: boolean;
  onSelect: () => void;
  isResultMode?: boolean;
  badge?: "correct" | "yourAnswer" | null;
};

export default function QuizOption({
  letter,
  text,
  isSelected = false,
  disabled = false,
  onSelect,
  isResultMode = false,
  badge = null,
}: QuizOptionProps) {
  const theme = OPTION_THEMES[letter.toUpperCase()] ?? { color: Colors.headerBlue, bg: "#EAF2FF", border: Colors.headerBlue };

  const isCorrect = badge === "correct";
  const isYourAnswer = badge === "yourAnswer";
  const { borderColor, borderWidth, borderBottomWidth } = getOptionBorder({ isResultMode, isCorrect, isYourAnswer, theme });

  return (
    <Pressable
      onPress={onSelect}
      disabled={disabled}
      style={({ pressed }) => [
        styles.container,
        {
          borderColor,
          borderWidth,
          borderBottomWidth,
          ...createShadow({ x: 0, y: 3, blur: 3, color: borderColor, opacity: 0.25, elevation: 3 }),
        },
        !isResultMode && isSelected && { backgroundColor: theme.bg },
        pressed && !disabled && styles.pressed,
        disabled && styles.disabled,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`Option ${letter}: ${text}`}
      accessibilityState={{ selected: isSelected, disabled }}
    >
      <View style={[styles.letterBadge, { backgroundColor: theme.color }]}>
        <AppText style={styles.letterText} color={Colors.white} weight={FontWeight.bold}>
          {letter}
        </AppText>
      </View>

      <AppText style={styles.optionText} color={Colors.black} weight={FontWeight.medium}>
        {text}
      </AppText>

      <ResultBadge isCorrect={isCorrect} isYourAnswer={isYourAnswer} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    maxWidth: "100%",
    minHeight: 74,
    borderRadius: 18,
    backgroundColor: Colors.white,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    marginTop: 12,
  },
  pressed: {
    opacity: 0.9,
    transform: [{ translateY: 1.5 }],
  },
  disabled: {
    opacity: 0.95,
  },
  letterBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  letterText: {
    fontSize: 20,
  },
  optionText: {
    flex: 1,
    flexShrink: 1,
    fontSize: 13,
    lineHeight: 19,
  },
});
