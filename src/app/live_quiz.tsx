import { useCallback, useEffect, useState } from "react";
import { StatusBar } from "expo-status-bar";
import { useFocusEffect } from "expo-router";
import { ActivityIndicator, Alert, BackHandler, Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { isModuleLeft, markModuleLeft, submitLiveQuiz } from "@/api/session";
import { QuizLiveHeader, QuizWaiting } from "@/components/quiz";
import { AssessmentMap, QuestionRecapSheet } from "@/components/quiz/assessment-map";
import LiveQuizQuestionView from "@/components/quiz/LiveQuizQuestionView";
import AppText from "@/components/ui/AppText";
import ConfirmModal from "@/components/ui/ConfirmModal";
import { useAuth } from "@/hooks/useAuth";
import { LiveQuizFeedback, useLiveQuiz } from "@/hooks/useLiveQuiz";
import { useLiveQuizSummary } from "@/hooks/useLiveQuizSummary";
import { Colors } from "@/theme/colors";

/** The waiting screen's words once the trainee is done with a question. */
function doneMessage(f: LiveQuizFeedback): string {
  const done = f.kind === "timeout" ? "Time's up for this question." : "Your answer is saved.";
  return `${done}\nThe next question will appear when the trainer sends it.`;
}

export default function LiveQuizScreen() {
  const { trainee } = useAuth();
  const [confirmLeaveOpen, setConfirmLeaveOpen] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const {
    view,
    phase,
    feedback,
    loadError,
    selectedOption,
    secondsLeft,
    timerPaused,
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

  useEffect(() => {
    if (conferenceUid && isModuleLeft(conferenceUid, "LIVE_QUIZ", trainee?.traineeUid)) {
      Alert.alert("Module Left", "You have left this module and cannot rejoin.");
      router.replace("/session_detail");
    }
  }, [conferenceUid, trainee?.traineeUid, router]);

  useFocusEffect(
    useCallback(() => {
      const sub = BackHandler.addEventListener("hardwareBackPress", () => {
        if (phase !== "finished" && phase !== "map") {
          setConfirmLeaveOpen(true);
          return true;
        }
        return false;
      });
      return () => sub.remove();
    }, [phase]),
  );

  const handleConfirmLeave = async () => {
    setConfirmLeaveOpen(false);
    if (leaving) return;
    setLeaving(true);
    if (conferenceUid) {
      markModuleLeft(conferenceUid, "LIVE_QUIZ", trainee?.traineeUid);
      if (token) {
        try {
          await submitLiveQuiz(token, conferenceUid);
        } catch {
          // Best effort server submit
        }
      }
    }
    router.replace("/session_detail");
  };

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <StatusBar style="dark" />
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
            paused={timerPaused}
            onSelect={selectOption}
          />
        ) : phase === "feedback" && feedback ? (
          // Answered or timed out: the waiting screen until the trainer sends the next question
          // (user, 2026-10-22) - right / wrong is on the Assessment Map at the end.
          <QuizWaiting
            onSyncNow={refetch}
            message={doneMessage(feedback)}
            nextQuestionNumber={(feedback.question.order || 0) + 1}
          />
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
        <Pressable style={styles.exit} onPress={() => setConfirmLeaveOpen(true)}>
          <AppText color={Colors.gray600}>Leave</AppText>
        </Pressable>
      )}

      <ConfirmModal
        visible={confirmLeaveOpen}
        title="Leave Live Quiz?"
        message="If you leave now, you won't be able to rejoin this module."
        icon="warning-outline"
        tone="danger"
        cancelText="Cancel"
        confirmText={leaving ? "Leaving..." : "Leave"}
        onCancel={() => setConfirmLeaveOpen(false)}
        onConfirm={handleConfirmLeave}
      />
    </SafeAreaView>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <View style={styles.centered}>{children}</View>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  body: { flex: 1, minHeight: 0 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", gap: 10, paddingHorizontal: 24 },
  retry: { backgroundColor: Colors.headerBlue, paddingHorizontal: 20, paddingVertical: 8, borderRadius: 8 },
  exit: { alignSelf: "center", paddingVertical: 10 },
});
