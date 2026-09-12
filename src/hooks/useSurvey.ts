/**
 * useSurvey Hook
 * Encapsulates survey data loading, question formatting, answer state,
 * validation, submission, and timer duration tracking.
 */

import {
  ApiError,
  AssessmentQuestion,
  getAssessmentQuestions,
  submitAssessment,
} from "@/api/assessment";
import { SurveyAnswers, SurveyQuestion } from "@/components/survey";
import { useAuth } from "@/hooks/useAuth";
import { useCallback, useEffect, useMemo, useState } from "react";

const FREE_TEXT_TYPES = new Set(["short_answer", "paragraph", "text"]);

export function useSurvey(suiteUid?: string, conferenceUid?: string) {
  const { token } = useAuth();

  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [surveyTitle, setSurveyTitle] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submittedAt, setSubmittedAt] = useState<Date | null>(null);
  const [startedAt] = useState(() => new Date());

  const [answers, setAnswers] = useState<SurveyAnswers>({});
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!token || !suiteUid) return;
      setLoading(true);
      setError(null);
      try {
        const data = await getAssessmentQuestions(token, suiteUid);
        if (!ignore) {
          setQuestions(data.questions);
          setSurveyTitle(data.title);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof ApiError ? err.message : "Couldn't load the survey.",
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, [token, suiteUid, reloadKey]);

  const handleAnswerChange = useCallback(
    (questionId: string | number, value: string) => {
      setAnswers((current) => ({ ...current, [questionId]: value }));
    },
    [],
  );

  const handleSubmit = useCallback(async () => {
    if (!token || !suiteUid || !conferenceUid || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitAssessment(
        token,
        suiteUid,
        conferenceUid,
        questions.map((question) => ({
          questionId: question.id,
          selectedOption: answers[question.id] ?? null,
        })),
      );
      setSubmittedAt(new Date());
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Couldn't submit the survey.",
      );
    } finally {
      setSubmitting(false);
    }
  }, [token, suiteUid, conferenceUid, submitting, questions, answers]);

  const surveyQuestions: SurveyQuestion[] = useMemo(() => {
    return questions.map((q) => ({
      id: q.id,
      question: q.question,
      type: FREE_TEXT_TYPES.has(q.question_type) ? "text" : "single-select",
      options: q.options?.map((opt) => ({ id: opt.id, text: opt.text })) ?? [],
      required: true,
    }));
  }, [questions]);

  const { headerTitle, headerSubtitle } = useMemo(() => {
    if (!surveyTitle) {
      return {
        headerTitle: "SECs Feedback | June",
        headerSubtitle: "Classroom Training Sessions",
      };
    }
    if (surveyTitle.includes("\n")) {
      const [t, sub] = surveyTitle.split("\n");
      return { headerTitle: t, headerSubtitle: sub };
    }
    return {
      headerTitle: surveyTitle,
      headerSubtitle: "Classroom Training Sessions",
    };
  }, [surveyTitle]);

  const retry = useCallback(() => {
    setReloadKey((k) => k + 1);
  }, []);

  return {
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
  };
}
