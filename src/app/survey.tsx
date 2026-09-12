import { useLocalSearchParams, useRouter } from "expo-router";

import TestSubmittedView from "@/components/assessment/TestSubmittedView";
import { SurveyErrorView, SurveyLoadingView, SurveyModule, buildSurveySubmissionRows } from "@/components/survey";
import { useSurvey } from "@/hooks/useSurvey";

export default function SurveyScreen() {
  const router = useRouter();
  const { conferenceUid, suiteUid } = useLocalSearchParams<{
    conferenceUid: string;
    suiteUid: string;
  }>();

  const {
    questions,
    surveyQuestions,
    headerTitle,
    headerSubtitle,
    answers,
    loading,
    error,
    submitting,
    submittedAt,
    startedAt,
    handleAnswerChange,
    handleSubmit,
    retry,
  } = useSurvey(suiteUid, conferenceUid);

  if (loading) {
    return <SurveyLoadingView />;
  }

  if (error && questions.length === 0) {
    return <SurveyErrorView error={error} onRetry={retry} />;
  }

  if (submittedAt) {
    return (
      <TestSubmittedView
        title="Survey Submitted Successfully!"
        thankYouText="Your feedback has been submitted successfully."
        rows={buildSurveySubmissionRows({ headerTitle, questions, answers, startedAt, submittedAt })}
        onGoToDashboard={() => {
          router.replace({ pathname: "/session_detail", params: { survey: "completed" } });
        }}
      />
    );
  }

  return (
    <SurveyModule
      questions={surveyQuestions}
      title={headerTitle}
      subtitle={headerSubtitle}
      instruction="Please review and complete the form below"
      answers={answers}
      onAnswerChange={handleAnswerChange}
      onSubmit={handleSubmit}
      submitting={submitting}
      error={error}
    />
  );
}
