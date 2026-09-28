import { Colors } from "@/theme/colors";
type OptionTheme = { color: string; bg: string; border: string };

type OptionBorderParams = {
  isResultMode: boolean;
  isCorrect: boolean;
  isYourAnswer: boolean;
  theme: OptionTheme;
};

export function getOptionBorder({ isResultMode, isCorrect, isYourAnswer, theme }: OptionBorderParams) {
  const borderColor = isResultMode ? (isCorrect ? Colors.recordedGreen : isYourAnswer ? Colors.red : Colors.gray200) : theme.border;

  const borderWidth = isResultMode ? (isCorrect || isYourAnswer ? 1.5 : 1) : 1.5;

  const borderBottomWidth = isResultMode ? (isCorrect || isYourAnswer ? 3.5 : 1) : 3.5;

  return { borderColor, borderWidth, borderBottomWidth };
}
