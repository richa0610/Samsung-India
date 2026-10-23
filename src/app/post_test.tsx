import { useLocalSearchParams } from "expo-router";

import TestSubmittedView from "@/components/assessment/TestSubmittedView";
import {
  buildSubmissionRows,
  PostTestActiveView,
  PostTestErrorView,
  PostTestLoadingView,
} from "@/components/assessment/post-test";
import ProctoringScreen from "@/components/proctoring/ProctoringScreen";
import { usePostTest } from "@/hooks/usePostTest";

export default function PostTestScreen() {
  const { conferenceUid, suiteUid, proctored, retest } = useLocalSearchParams<{
    conferenceUid: string;
    suiteUid: string;
    proctored?: string;
    retest?: string;
  }>();

  const isRetest = retest === "true";
  const postTest = usePostTest(conferenceUid, suiteUid, proctored, isRetest);
  const {
    readyToStart,
    setReadyToStart,
    loading,
    error,
    questions,
    testStatus,
    submittedAt,
    retry,
    current,
    suiteTitle,
    answers,
    totalSeconds,
    remainingSeconds,
    handleGoToDashboard,
  } = postTest;

  if (!readyToStart) {
    return <ProctoringScreen onStartTest={() => setReadyToStart(true)} />;
  }

  if (loading) {
    return <PostTestLoadingView />;
  }

  if (error && questions.length === 0) {
    return <PostTestErrorView error={error} onRetry={retry} />;
  }

  if (testStatus === "completed" && submittedAt) {
    return (
      <TestSubmittedView
        rows={buildSubmissionRows({ suiteTitle, questions, answers, totalSeconds, remainingSeconds, submittedAt })}
        onGoToDashboard={handleGoToDashboard}
      />
    );
  }

  if (!current) return null;

  return <PostTestActiveView postTest={postTest} />;
}
