import { ScrollView, StyleSheet, View } from "react-native";

import { LiveQuizQuestion } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import QuizOption from "./QuizOption";
import QuizTimer from "./QuizTimer";

type Props = {
  question: LiveQuizQuestion;
  secondsLeft: number;
  selectedOption: string | null;
  locked: boolean;
  /** The trainer stopped the timer: the clock is frozen and answering waits for Play. */
  paused?: boolean;
  onSelect: (optionId: string) => void;
};

export default function LiveQuizQuestionView({
  question,
  secondsLeft,
  selectedOption,
  locked,
  paused = false,
  onSelect,
}: Props) {
  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <QuizTimer remainingSeconds={secondsLeft} size={116} borderColor={paused ? Colors.gray500 : undefined} />

      {paused && (
        <View style={styles.pausedBanner} accessibilityRole="alert">
          <AppText color={Colors.white} weight={FontWeight.bold} style={styles.pausedText}>
            Paused by trainer - answers open again when the timer restarts
          </AppText>
        </View>
      )}

      <View style={styles.card}>
        <AppText style={styles.questionText} color={Colors.black} weight={FontWeight.bold}>
          {question.text}
        </AppText>

        <View style={styles.options}>
          {question.options.map((option, index) => (
            <QuizOption
              key={option.id}
              letter={String.fromCharCode(65 + index)}
              text={option.text}
              isSelected={selectedOption === option.id}
              disabled={locked || paused}
              onSelect={() => onSelect(option.id)}
            />
          ))}
        </View>
      </View>

      {locked && (
        <AppText style={styles.lockedNote} color={Colors.gray600} align="center">
          {selectedOption ? "Answer locked in. Look at the main screen." : "Time's up - look at the main screen."}
        </AppText>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, gap: 16, alignItems: "center" },
  card: { width: "100%", backgroundColor: Colors.white, borderRadius: 18, padding: 16, gap: 14 },
  questionText: { fontSize: 15, lineHeight: 21 },
  options: { gap: 10 },
  lockedNote: { fontSize: 12, marginTop: 4 },
  pausedBanner: { backgroundColor: Colors.gray600, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 8 },
  pausedText: { fontSize: 12, textAlign: "center" },
});
