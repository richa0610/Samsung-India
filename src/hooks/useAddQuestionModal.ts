import { useState } from "react";

import {
  ApiError,
  AssessmentSuiteDetail,
  QuestionOption,
  addAssessmentQuestion,
} from "@/api/training";
import { cleanText, digitsOnly, firstError, intInRange, required } from "@/utils/validation";

const DEFAULT_OPTIONS: QuestionOption[] = [
  { id: "1", text: "" },
  { id: "2", text: "" },
];

type UseAddQuestionModalParams = {
  adminToken: string | null;
  suiteUid: string;
  onAdded: (updated: AssessmentSuiteDetail) => void;
};

export function useAddQuestionModal({ adminToken, suiteUid, onAdded }: UseAddQuestionModalParams) {
  const [question, setQuestion] = useState("");
  const [questionType, setQuestionType] = useState("multiple_choice");
  const [points, setPoints] = useState("1");
  const [timerSeconds, setTimerSeconds] = useState("30");
  const [options, setOptions] = useState<QuestionOption[]>(DEFAULT_OPTIONS);
  const [correctAnswer, setCorrectAnswer] = useState<string>("1");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setQuestion("");
    setQuestionType("multiple_choice");
    setPoints("1");
    setTimerSeconds("30");
    setOptions(DEFAULT_OPTIONS);
    setCorrectAnswer("1");
    setError(null);
  };

  const handleAddOption = () => {
    const nextId = String(options.length + 1);
    setOptions((prev) => [...prev, { id: nextId, text: "" }]);
  };

  const handleUpdateOption = (id: string, text: string) => {
    setOptions((prev) => prev.map((opt) => (opt.id === id ? { ...opt, text } : opt)));
  };

  const handleRemoveOption = (id: string) => {
    if (options.length <= 2) return;
    setOptions((prev) => prev.filter((opt) => opt.id !== id));
    if (correctAnswer === id) {
      setCorrectAnswer(options.find((o) => o.id !== id)?.id ?? "1");
    }
  };

  const handleSave = async () => {
    const validationError = firstError(
      required(question, "Question text"),
      intInRange(points, 1, 100, "Points", true),
      intInRange(timerSeconds, 5, 600, "Timer (seconds)", true),
    );
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!adminToken) return;
    const cleanOptions = options
      .map((opt) => ({ ...opt, text: cleanText(opt.text, 300) }))
      .filter((opt) => opt.text);
    if (cleanOptions.length < 2) {
      setError("Please provide at least 2 options.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const updated = await addAssessmentQuestion(adminToken, suiteUid, {
        question: cleanText(question, 500),
        questionType,
        points: Number(digitsOnly(points)) || 1,
        timerSeconds: Number(digitsOnly(timerSeconds)) || 30,
        options: cleanOptions,
        correctAnswer,
      });
      reset();
      onAdded(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't add that question.");
    } finally {
      setSaving(false);
    }
  };

  return {
    question,
    setQuestion,
    questionType,
    setQuestionType,
    points,
    setPoints,
    timerSeconds,
    setTimerSeconds,
    options,
    correctAnswer,
    setCorrectAnswer,
    saving,
    error,
    reset,
    handleAddOption,
    handleUpdateOption,
    handleRemoveOption,
    handleSave,
  };
}
