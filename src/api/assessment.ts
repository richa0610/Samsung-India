import { USE_MOCK_DATA } from "@/config/dataSource";
import { apiRequest } from "./client";
import * as mock from "./mockService";

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

export function getAssessmentQuestions(token: string, suiteUid: string) {
  if (USE_MOCK_DATA) return mock.getAssessmentQuestions(token, suiteUid);
  return apiRequest<AssessmentQuestionsResponse>(`/assessments/${suiteUid}/questions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function submitAssessment(
  token: string,
  suiteUid: string,
  conferenceUid: string,
  answers: AssessmentAnswer[]
) {
  if (USE_MOCK_DATA) return mock.submitAssessment(token, suiteUid, conferenceUid, answers);
  return apiRequest<AssessmentResult>(`/assessments/${suiteUid}/submit`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid, answers }),
  });
}

// No real backend endpoint yet - callers already treat failures as
// non-fatal (see usePostTest.ts's handleViolationTermination).
export { terminateAssessmentWithViolation } from "@/api/mockService";
export { ApiError } from "@/api/client";


