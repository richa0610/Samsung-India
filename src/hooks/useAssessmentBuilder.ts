/**
 * useAssessmentBuilder Hook
 * Encapsulates assessment suite loading, suite creation, question adding/deleting,
 * validation, and modal states.
 */

import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import {
  ApiError,
  AssessmentSuiteDetail,
  createAssessmentSuite,
  deleteAssessmentQuestion,
  fetchAssessmentSuiteDetail,
} from "@/api/training";
import { cleanText, digitsOnly, firstError, intInRange, required } from "@/utils/validation";

export function useAssessmentBuilder(suiteUidParam?: string) {
  const { adminToken } = useAuth();

  const [suiteUid, setSuiteUid] = useState<string | null>(
    suiteUidParam ?? null,
  );
  const [suite, setSuite] = useState<AssessmentSuiteDetail | null>(null);
  const [loading, setLoading] = useState(!!suiteUidParam);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [testTime, setTestTime] = useState("30");
  const [type, setType] = useState("Quiz");
  const [creating, setCreating] = useState(false);

  const [addVisible, setAddVisible] = useState(false);

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!adminToken || !suiteUid) return;
      try {
        const detail = await fetchAssessmentSuiteDetail(adminToken, suiteUid);
        if (!ignore) {
          setSuite(detail);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Couldn't load this assessment.",
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
  }, [adminToken, suiteUid]);

  const handleCreateSuite = async () => {
    const validationError = firstError(
      required(title, "Title"),
      required(category, "Category"),
      intInRange(testTime, 1, 180, "Time (min)", true),
    );
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!adminToken) return;
    setCreating(true);
    setError(null);
    try {
      const created = await createAssessmentSuite(adminToken, {
        title: cleanText(title, 150),
        description: cleanText(description, 500) || undefined,
        category,
        testTime: digitsOnly(testTime),
        type,
      });
      setSuiteUid(created.assessmentSuiteUid);
      setSuite(created);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Couldn't create this assessment.",
      );
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    if (!adminToken || !suiteUid) return;
    try {
      const updated = await deleteAssessmentQuestion(
        adminToken,
        suiteUid,
        questionId,
      );
      setSuite(updated);
    } catch {
      setError("Couldn't remove that question.");
    }
  };

  const handleQuestionAdded = (updated: AssessmentSuiteDetail) => {
    setSuite(updated);
    setAddVisible(false);
  };

  return {
    adminToken,
    suiteUid,
    suite,
    loading,
    error,
    title,
    setTitle,
    description,
    setDescription,
    category,
    setCategory,
    testTime,
    setTestTime,
    type,
    setType,
    creating,
    addVisible,
    setAddVisible,
    handleCreateSuite,
    handleDeleteQuestion,
    handleQuestionAdded,
  };
}
