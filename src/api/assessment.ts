import { apiRequest } from "./client";

export type AssessmentQuestion = {
  id: number;
  question: string;
  question_type: string;
  sort_order: number;
  options: { id: string; text: string }[];
  correctAnswer?: string | null;
  explanation?: string | null;
};


export type AssessmentAnswer = {
  questionId: number;
  selectedOption: string | null;
};

export type AssessmentResult = {
  totalScore: number;
  maxScore: number;
  percentage: number;
  correctCount: number;
  totalQuestions: number;
};

export type AssessmentQuestionsResponse = {
  title: string | null;
  testTime: string | null;
  questions: AssessmentQuestion[];
};

/** The questions of a test the trainee is taking now - the server checks the session is theirs,
 *  they're marked Present and this test's module is open. */
export function getAssessmentQuestions(token: string, suiteUid: string, conferenceUid: string, retest?: boolean) {
  const query = `conferenceUid=${encodeURIComponent(conferenceUid)}${retest ? "&retest=true" : ""}`;
  return apiRequest<AssessmentQuestionsResponse>(`/assessments/${encodeURIComponent(suiteUid)}/questions?${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function submitAssessment(
  token: string,
  suiteUid: string,
  conferenceUid: string,
  answers: AssessmentAnswer[],
  retest?: boolean,
) {
  return apiRequest<AssessmentResult>(`/assessments/${suiteUid}/submit`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid, answers, retest: !!retest }),
  });
}

export { ApiError } from "@/api/client";


