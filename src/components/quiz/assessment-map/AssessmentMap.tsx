import { ScrollView, StyleSheet, View } from "react-native";

import { LiveQuizSummary } from "@/api/session";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import AssessmentMapHeader from "./AssessmentMapHeader";
import MapActions from "./MapActions";
import QuestionStatusGrid from "./QuestionStatusGrid";
import StatsRow from "./StatsRow";
import StatusLegend from "./StatusLegend";

type AssessmentMapProps = {
  summary: LiveQuizSummary;
  connected?: boolean;
  submitting?: boolean;
  onSelectQuestion: (index: number) => void;
  onReviewQuestions: () => void;
  onFinalSubmit: () => void;
};

function formatMs(totalMs: number): string | null {
  if (totalMs <= 0) return null;
  const totalSeconds = Math.round(totalMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export default function AssessmentMap({
  summary,
  connected = true,
  submitting = false,
  onSelectQuestion,
  onReviewQuestions,
  onFinalSubmit,
}: AssessmentMapProps) {
  const answered = summary.attemptedCount + summary.timedOutCount;
  const timeTaken = formatMs(
    summary.questions.reduce((sum, q) => sum + (q.responseMs ?? 0), 0),
  );

  return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <AssessmentMapHeader
        answeredCount={answered}
        totalQuestions={summary.totalQuestions}
        timeTakenLabel={timeTaken}
        connected={connected}
      />

      <View style={styles.card}>
        <View style={styles.hero}>
          <AppText style={styles.heroTitle} color={Colors.white} weight={FontWeight.bold}>
            Assessment Map
          </AppText>
          <AppText style={styles.heroSubtitle} color={Colors.white}>
            Review your attempts before final submission
          </AppText>
        </View>

        <View style={styles.body}>
          <StatsRow
            attemptedCount={summary.attemptedCount}
            skippedCount={summary.skippedCount}
            expiredCount={summary.timedOutCount}
          />
          <StatusLegend />
          <QuestionStatusGrid questions={summary.questions} onSelectQuestion={onSelectQuestion} />
          <View style={styles.divider} />
          <MapActions
            onReviewQuestions={onReviewQuestions}
            onSubmit={onFinalSubmit}
            submitting={submitting}
          />
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1, paddingBottom: 28 },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 20,
    marginHorizontal: 16,
    marginTop: 14,
    overflow: "hidden",
    ...createShadow({ x: 0, y: 4, blur: 10, opacity: 0.08, elevation: 3 }),
  },
  hero: { backgroundColor: Colors.headerBlue, paddingVertical: 18, alignItems: "center" },
  heroTitle: { fontSize: 22 },
  heroSubtitle: { fontSize: 12, marginTop: 3, opacity: 0.9 },
  body: { padding: 16 },
  divider: { height: 1, backgroundColor: "#E5E7EB", marginTop: 18, marginBottom: 16 },
});
