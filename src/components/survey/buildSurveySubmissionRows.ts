import { AssessmentQuestion } from "@/api/assessment";
import { SubmissionSummaryRow } from "@/components/assessment/TestSubmittedView";
import { Colors } from "@/theme/colors";
import { SurveyAnswers } from "./types";

type BuildSurveySubmissionRowsParams = {
  headerTitle: string;
  questions: AssessmentQuestion[];
  answers: SurveyAnswers;
  startedAt: Date;
  submittedAt: Date;
};

export function buildSurveySubmissionRows({
  headerTitle,
  questions,
  answers,
  startedAt,
  submittedAt,
}: BuildSurveySubmissionRowsParams): SubmissionSummaryRow[] {
  const attempted = Object.keys(answers).filter((key) => answers[key]?.trim()).length;
  const elapsedSeconds = Math.max(Math.round((submittedAt.getTime() - startedAt.getTime()) / 1000), 0);
  const hh = String(Math.floor(elapsedSeconds / 3600)).padStart(2, "0");
  const mm = String(Math.floor((elapsedSeconds % 3600) / 60)).padStart(2, "0");
  const ss = String(elapsedSeconds % 60).padStart(2, "0");

  return [
    {
      label: "Survey Title",
      value: headerTitle,
      icon: "document-text",
      iconColor: Colors.success,
      iconBg: "#D8F8EB",
    },
    {
      label: "Date & Time",
      value: `${submittedAt.toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" })}, ${submittedAt.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}`,
      icon: "calendar",
      iconColor: Colors.mainColour1,
      iconBg: Colors.notificationBg,
    },
    {
      label: "Duration",
      value: `${hh}:${mm}:${ss}`,
      icon: "time",
      iconColor: "#8B5CF6",
      iconBg: "#EDE4FF",
    },
    {
      label: "Total Questions",
      value: String(questions.length),
      icon: "help-circle",
      iconColor: "#F59E0B",
      iconBg: "#FFF3D6",
    },
    {
      label: "Attempted",
      value: String(attempted),
      icon: "checkmark-done",
      iconColor: Colors.success,
      iconBg: "#D8F8EB",
    },
  ];
}
