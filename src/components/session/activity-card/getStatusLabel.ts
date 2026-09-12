import { SessionActivityData } from "@/hooks/useTraineeHome";

export function getStatusLabel(activity: SessionActivityData): string {
  const { isLive, isCompleted, isMissed, isLocked, key } = activity;
  const isAttendance = key === "ATTENDANCE";
  const isQuiz = key === "LIVE_QUIZ";
  const isPostTest = key === "STANDARD_TEST";

  if (isLocked) return "Locked";

  if (isCompleted) {
    if (isAttendance) return "Recorded";
    if ((isQuiz || isPostTest) && activity.score) return `Score : ${activity.score}`;
    return "Completed";
  }

  if (isMissed) return "Missed";
  if (isLive) return "LIVE NOW";
  return "Upcoming";
}
