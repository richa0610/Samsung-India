import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { QuizLiveHeader, QuizWaiting } from "@/components/quiz";
import { AssessmentMap, QuestionRecapSheet } from "@/components/quiz/assessment-map";
import LiveQuizQuestionView from "@/components/quiz/LiveQuizQuestionView";
import QuizResult from "@/components/quiz/QuizResult";
import { QuizQuestionData } from "@/components/quiz/QuizQuestionCard";
import AppText from "@/components/ui/AppText";
import { LiveQuizFeedback, useLiveQuiz } from "@/hooks/useLiveQuiz";
import { useLiveQuizSummary } from "@/hooks/useLiveQuizSummary";
import { Colors } from "@/theme/colors";

function toQuestionData(f: LiveQuizFeedback): QuizQuestionData {
  return {
    id: f.question.id,
    question: f.question.text,
    options: f.question.options,
    currentQuestion: f.question.order || 1,
    totalQuestions: f.question.total || f.question.order || 1,
    correctAnswer: f.correctOptionId,
    explanation: f.explanation,
  };
}

export default function LiveQuizScreen() {
  const {
    view,
    phase,
    feedback,
    loadError,
    selectedOption,
    secondsLeft,
    submitting,
    connected,
    conferenceUid,
    token,
    selectOption,
    onFinalSubmit,
    refetch,
    router,
  } = useLiveQuiz();

  const { summary, recapIndex, openRecap, openReview, closeRecap, stepRecap } =
    useLiveQuizSummary(conferenceUid, token, phase === "map");

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <StatusBar style="light" />
      <QuizLiveHeader onRefresh={refetch} isConnected={connected} showConnectionLabel={phase !== "question"} />

      <View style={styles.body}>
        {loadError && !view ? (
          <Centered>
            <AppText color={Colors.gray600} align="center">{loadError}</AppText>
            <Pressable style={styles.retry} onPress={refetch}>
              <AppText color={Colors.white}>Retry</AppText>
            </Pressable>
          </Centered>
        ) : phase === "map" ? (
          summary ? (
            <>
              <AssessmentMap
                summary={summary}
                connected={connected}
                submitting={submitting}
                onSelectQuestion={openRecap}
                onReviewQuestions={openReview}
                onFinalSubmit={onFinalSubmit}
              />
              <QuestionRecapSheet
                visible={recapIndex !== null}
                questions={summary.questions}
                index={recapIndex ?? 0}
                onClose={closeRecap}
                onStep={stepRecap}
              />
            </>
          ) : (
            <Centered>
              <ActivityIndicator color={Colors.headerBlue} />
              <AppText color={Colors.gray600} align="center">Building your assessment map…</AppText>
              <Pressable style={styles.retry} onPress={onFinalSubmit} disabled={submitting}>
                <AppText color={Colors.white}>{submitting ? "Submitting…" : "Skip & Final Submit"}</AppText>
              </Pressable>
            </Centered>
          )
        ) : phase === "question" && view?.question ? (
          <LiveQuizQuestionView
            question={view.question}
            secondsLeft={secondsLeft}
            selectedOption={selectedOption}
            locked={selectedOption != null}
            onSelect={selectOption}
          />
        ) : phase === "feedback" && feedback ? (
          <View style={styles.feedbackWrap}>
            <QuizResult
              type={feedback.kind}
              question={toQuestionData(feedback)}
              selectedOptionId={feedback.selectedOptionId}
              correctOptionId={feedback.correctOptionId}
              explanation={feedback.explanation}
            />
            <AppText style={styles.waitHint} color={Colors.gray600} align="center">
              Waiting for the trainer to move to the next question…
            </AppText>
          </View>
        ) : phase === "finished" ? (
          <Centered>
            <ActivityIndicator color={Colors.headerBlue} />
            <AppText color={Colors.gray600} align="center">Quiz complete — loading your rank…</AppText>
          </Centered>
        ) : (
          <QuizWaiting onSyncNow={refetch} />
        )}
      </View>

      {phase !== "finished" && phase !== "map" && (
        <Pressable style={styles.exit} onPress={() => router.replace("/session_detail")}>
          <AppText color={Colors.gray600}>Leave</AppText>
        </Pressable>
      )}
    </SafeAreaView>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <View style={styles.centered}>{children}</View>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  body: { flex: 1, minHeight: 0 },
  feedbackWrap: { flex: 1, minHeight: 0 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", gap: 10, paddingHorizontal: 24 },
  retry: { backgroundColor: Colors.headerBlue, paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  waitHint: { fontSize: 12, paddingHorizontal: 24, paddingBottom: 12 },
  exit: { alignSelf: "center", paddingVertical: 10 },
});
