/**
 * usePostTest Hook
 * Encapsulates the entire post-test lifecycle: question fetching, timer countdown,
 * question navigation, option selection, submission handling, result tracking,
 * and strict proctoring/violation state machines.
 */

import {
  ApiError,
  AssessmentQuestion,
  AssessmentResult,
  getAssessmentQuestions,
  submitAssessment,
  terminateAssessmentWithViolation,
} from "@/api/assessment";
import {
  getLastViolation,
  getSessionViolationCount,
  isSessionLocked,
  lockSession,
  MAX_PROCTORING_WARNINGS,
  recordSessionViolation,
  SECURITY_VIOLATIONS,
  SecurityViolationType,
} from "@/components/proctoring/violations";
import { reportProctoringLock } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { AppState, Platform } from "react-native";

const DEFAULT_TEST_MINUTES = 30;

export type PostTestStatus =
  | "active"
  | "submitting"
  | "completed"
  | "security-locked";

export function usePostTest(
  conferenceUid?: string,
  suiteUid?: string,
  proctored?: string,
) {
  const router = useRouter();
  const { token } = useAuth();

  const [readyToStart, setReadyToStart] = useState(proctored === "true");

  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [suiteTitle, setSuiteTitle] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Session key for persistent violation tracking
  const sessionKey = conferenceUid || suiteUid || "default-post-test";

  // Unified post-test status
  const [testStatus, setTestStatus] = useState<PostTestStatus>(() =>
    isSessionLocked(sessionKey) ? "security-locked" : "active",
  );
  const [assessmentResult, setAssessmentResult] =
    useState<AssessmentResult | null>(null);
  const [submittedAt, setSubmittedAt] = useState<Date | null>(null);

  // Violation-specific state
  const [violationCount, setViolationCount] = useState(() =>
    getSessionViolationCount(sessionKey),
  );
  const [currentViolation, setCurrentViolation] =
    useState<SecurityViolationType | null>(() => getLastViolation(sessionKey));
  const [violationModalVisible, setViolationModalVisible] = useState(false);
  const [lockedViolationType, setLockedViolationType] =
    useState<SecurityViolationType | null>(() => getLastViolation(sessionKey));

  // Guards: deduplicate multiple simultaneous violation triggers and double termination
  const terminatingRef = useRef(isSessionLocked(sessionKey));
  const lastViolationTimeRef = useRef(0);

  // Soft (non-strike) warning shown at the earlier WARNING severity tier —
  // separate from currentViolation/violationModalVisible, which track real strikes.
  const [softWarningType, setSoftWarningType] =
    useState<SecurityViolationType | null>(null);
  const softWarningTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string | null>>({});

  const [totalSeconds, setTotalSeconds] = useState(DEFAULT_TEST_MINUTES * 60);
  const [remainingSeconds, setRemainingSeconds] = useState(
    DEFAULT_TEST_MINUTES * 60,
  );

  const [reloadKey, setReloadKey] = useState(0);

  // Load questions
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
          setSuiteTitle(data.title ?? null);
          if (data.testTime) {
            const mins = parseInt(data.testTime, 10);
            if (!isNaN(mins) && mins > 0) {
              setTotalSeconds(mins * 60);
              setRemainingSeconds(mins * 60);
            }
          }
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Couldn't load test questions.",
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

  const current = questions[questionIndex];
  const selectedOption = answers[questionIndex] ?? null;
  const isLastQuestion = questionIndex === questions.length - 1;
  const isActive = testStatus === "active";

  // Normal submit
  const handleSubmit = useCallback(async () => {
    if (!token || !suiteUid || !conferenceUid) return;
    if (terminatingRef.current) return;
    terminatingRef.current = true;
    setTestStatus("submitting");
    setError(null);
    try {
      const res = await submitAssessment(
        token,
        suiteUid,
        conferenceUid,
        questions.map((question, index) => ({
          questionId: question.id,
          selectedOption: answers[index] ?? null,
        })),
      );
      setAssessmentResult(res);
      setSubmittedAt(new Date());
      setTestStatus("completed");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Couldn't submit the test.",
      );
      terminatingRef.current = false;
      setTestStatus("active");
    }
  }, [token, suiteUid, conferenceUid, questions, answers]);

  // Security violation termination
  const handleViolationTermination = useCallback(
    async (violationType: SecurityViolationType) => {
      terminatingRef.current = true;
      setTestStatus("security-locked");
      setLockedViolationType(violationType);
      lockSession(sessionKey, violationType);

      const answersPayload = questions.map((question, index) => ({
        questionId: question.id,
        selectedOption: answers[index] ?? null,
      }));

      try {
        await terminateAssessmentWithViolation(
          token ?? "",
          suiteUid ?? "",
          conferenceUid ?? "",
          violationType,
          answersPayload,
        );
      } catch {
        // Even if API call fails, lock the test permanently for this session
      }

      // Persist the lock onto the trainee's attendance row so the trainer's
      // Participant Master List shows it and can unlock (with a reason).
      if (token && conferenceUid) {
        try {
          await reportProctoringLock(token, conferenceUid, violationType, MAX_PROCTORING_WARNINGS);
        } catch {
          // Non-fatal - the local lock still holds for this session.
        }
      }

      router.replace({
        pathname: "/session_detail",
        params: {
          flow: "ATTENDANCE_RECORDED",
          postTest: "security_locked",
          violation: "locked",
          violationType,
        },
      });
    },
    [token, suiteUid, conferenceUid, sessionKey, questions, answers, router],
  );

  // Central Violation Trigger
  const triggerViolation = useCallback(
    (violationType: SecurityViolationType) => {
      if (
        testStatus !== "active" ||
        terminatingRef.current ||
        violationModalVisible
      )
        return;

      const now = Date.now();
      if (now - lastViolationTimeRef.current < 1500) return;
      lastViolationTimeRef.current = now;

      // A real strike supersedes any soft warning already on screen for the
      // same escalating occurrence — don't let both stack visually.
      if (softWarningTimeoutRef.current) clearTimeout(softWarningTimeoutRef.current);
      setSoftWarningType(null);

      const newCount = recordSessionViolation(sessionKey, violationType);
      setViolationCount(newCount);
      setCurrentViolation(violationType);

      if (newCount < MAX_PROCTORING_WARNINGS) {
        setViolationModalVisible(true);
      } else {
        setViolationModalVisible(false);
        handleViolationTermination(violationType);
      }
    },
    [testStatus, violationModalVisible, sessionKey, handleViolationTermination],
  );

  const handleCloseViolationModal = () => {
    setViolationModalVisible(false);
    setCurrentViolation(null);
    // Note: lastViolationTimeRef is intentionally left as-is (not reset to
    // Date.now()) so the camera resumes noticing side-look movement right
    // away instead of sitting through another debounce window after close.
  };

  // Soft warning: no strike counted, just an early nudge that clears itself.
  const triggerSoftWarning = useCallback(
    (violationType: SecurityViolationType) => {
      if (testStatus !== "active" || terminatingRef.current) return;
      if (softWarningTimeoutRef.current) clearTimeout(softWarningTimeoutRef.current);
      setSoftWarningType(violationType);
      softWarningTimeoutRef.current = setTimeout(() => {
        setSoftWarningType(null);
      }, 1800);
    },
    [testStatus],
  );

  useEffect(() => {
    return () => {
      if (softWarningTimeoutRef.current) clearTimeout(softWarningTimeoutRef.current);
    };
  }, []);

  // Tab-switch detection (Web)
  useEffect(() => {
    if (Platform.OS !== "web" || !readyToStart) return;

    const handleVisibilityChange = () => {
      if (
        document.hidden &&
        testStatus === "active" &&
        !terminatingRef.current
      ) {
        triggerViolation(SECURITY_VIOLATIONS.TAB_SWITCH);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [readyToStart, testStatus, triggerViolation]);

  // App-switch detection (Native — the equivalent of a tab switch on web)
  useEffect(() => {
    if (Platform.OS === "web" || !readyToStart) return;

    const subscription = AppState.addEventListener("change", (nextState) => {
      if (
        nextState === "background" &&
        testStatus === "active" &&
        !terminatingRef.current
      ) {
        triggerViolation(SECURITY_VIOLATIONS.TAB_SWITCH);
      }
    });

    return () => subscription.remove();
  }, [readyToStart, testStatus, triggerViolation]);

  // Timer countdown
  useEffect(() => {
    if (!readyToStart || questions.length === 0 || testStatus !== "active")
      return;
    const timer = setInterval(() => {
      setRemainingSeconds((seconds) => {
        if (seconds <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return seconds - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [readyToStart, questions.length, testStatus, handleSubmit]);

  const remainingMinutes = Math.floor(remainingSeconds / 60);
  const remainingSecondsPart = remainingSeconds % 60;
  const totalMinutes = Math.max(Math.ceil(totalSeconds / 60), 1);

  const selectOption = (optionId: string) => {
    if (!isActive) return;
    setAnswers((items) => ({ ...items, [questionIndex]: optionId }));
  };

  const move = (direction: number) => {
    if (!isActive) return;
    setQuestionIndex((index) =>
      Math.min(Math.max(index + direction, 0), questions.length - 1),
    );
  };

  const retry = () => {
    setReloadKey((k) => k + 1);
  };

  const handleGoToDashboard = () => {
    const attempted = Object.keys(answers).length;
    const elapsedSeconds = Math.max(totalSeconds - remainingSeconds, 0);
    const hh = String(Math.floor(elapsedSeconds / 3600)).padStart(2, "0");
    const mm = String(Math.floor((elapsedSeconds % 3600) / 60)).padStart(
      2,
      "0",
    );

    const scoreStr = assessmentResult
      ? `${assessmentResult.correctCount}/${assessmentResult.totalQuestions}`
      : `${attempted}/${questions.length || 15}`;
    const durationStr = `Ran : ${hh !== "00" ? `${parseInt(hh)}h ` : ""}${parseInt(mm) || 1}m`;
    router.replace({
      pathname: "/session_detail",
      params: {
        postTest: "completed",
        score: scoreStr,
        duration: durationStr,
      },
    });
  };

  const handleSecurityLockedClose = () => {
    router.replace({
      pathname: "/session_detail",
      params: { postTest: "security_locked" },
    });
  };

  return {
    token,
    readyToStart,
    setReadyToStart,
    questions,
    current,
    questionIndex,
    selectedOption,
    isLastQuestion,
    suiteTitle,
    loading,
    error,
    testStatus,
    isActive,
    isSubmitting: testStatus === "submitting",
    assessmentResult,
    submittedAt,
    violationCount,
    currentViolation,
    violationModalVisible,
    lockedViolationType,
    softWarningType,
    totalSeconds,
    remainingSeconds,
    remainingMinutes,
    remainingSecondsPart,
    totalMinutes,
    answers,
    selectOption,
    move,
    handleSubmit,
    triggerViolation,
    triggerSoftWarning,
    handleCloseViolationModal,
    retry,
    handleGoToDashboard,
    handleSecurityLockedClose,
  };
}
