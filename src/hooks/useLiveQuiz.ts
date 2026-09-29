import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  ApiError,
  LiveQuizQuestion,
  LiveQuizView,
  getLiveQuizView,
  reportLiveQuizTimeout,
  revealLiveQuestion,
  submitLiveAnswer,
  submitLiveQuiz,
} from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { useCountdown } from "@/hooks/useCountdown";
import { useLiveQuizChannel } from "@/hooks/useLiveQuizChannel";

// Fallback poll - the /ws/live nudge is the primary trigger.
const POLL_MS = 5000;

export type LiveQuizPhase = "waiting" | "question" | "feedback" | "map" | "finished";

/** The question the trainee just resolved was the last one in the quiz. */
function isLastQuestion(q: { order?: number; total?: number }): boolean {
  return (q.total ?? 0) > 0 && (q.order ?? 0) >= (q.total ?? 0);
}

export type LiveQuizFeedback = {
  kind: "correct" | "incorrect" | "timeout";
  question: LiveQuizQuestion;
  selectedOptionId: string | null;
  correctOptionId: string | null;
  explanation: string | null;
};

export function useLiveQuiz() {
  const router = useRouter();
  const { token } = useAuth();
  const { conferenceUid } = useLocalSearchParams<{ conferenceUid: string }>();

  const [view, setView] = useState<LiveQuizView | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<LiveQuizFeedback | null>(null);
  const [resolvedQuestionId, setResolvedQuestionId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const lastQidRef = useRef<number | null>(null);
  const revealingRef = useRef(false);
  // Guards against out-of-order responses: refetch() is triggered from three
  // places at once (mount, the poll interval, every WS nudge), so nothing
  // stops an older in-flight request from resolving after a newer one and
  // clobbering fresh state with stale data - most likely right at cold
  // mount, when a pre-broadcast "WAITING" request can still be in flight
  // when the trainer broadcasts question 1 moments later.
  const requestSeqRef = useRef(0);

  const revealAsTimeout = useCallback(
    async (question: LiveQuizQuestion, selected: string | null) => {
      if (!token || !conferenceUid || revealingRef.current) return;
      revealingRef.current = true;
      // No setState before the first await - keeps this safe to call straight
      // from an effect without a synchronous render cascade.
      let reveal: { correctOptionId: string | null; explanation: string | null; yourOptionId: string | null } | null =
        null;
      try {
        reveal = await revealLiveQuestion(token, conferenceUid, question.id);
      } catch {
        reveal = null;
      }
      setResolvedQuestionId(question.id);
      setFeedback({
        kind: "timeout",
        question,
        selectedOptionId: selected ?? reveal?.yourOptionId ?? null,
        correctOptionId: reveal?.correctOptionId ?? null,
        explanation: reveal?.explanation ?? null,
      });
      // Record the miss so the Assessment Map can tell "timed out" from
      // "skipped" (idempotent server-side - no-op if a row already exists).
      void reportLiveQuizTimeout(token, conferenceUid, question.id).catch(() => {});
      revealingRef.current = false;
    },
    [token, conferenceUid],
  );

  const refetch = useCallback(async () => {
    if (!token || !conferenceUid) return;
    const seq = ++requestSeqRef.current;
    let next: LiveQuizView;
    try {
      next = await getLiveQuizView(token, conferenceUid);
    } catch (err) {
      // A newer refetch has started since this one was sent - let its
      // resolution (success or failure) be the one that updates state.
      if (seq !== requestSeqRef.current) return;
      setLoadError(err instanceof ApiError ? err.message : "Couldn't load the quiz.");
      return;
    }
    // Same guard on the success path - this response is stale if another
    // refetch() call was made after this one was sent.
    if (seq !== requestSeqRef.current) return;
    setLoadError(null);
    setView(next);

    // A different question is live (trainer broadcast the next one, possibly
    // before this one's timer ran out). Drop everything tied to the previous
    // question so the new one shows immediately with its own fresh countdown -
    // no dwell on the old question.
    const qid = next.question?.id ?? null;
    if (next.state === "QUESTION_LIVE" && qid != null && qid !== lastQidRef.current) {
      lastQidRef.current = qid;
      setFeedback(null);
      setSelectedOption(null);
      setResolvedQuestionId(null);
    }
  }, [token, conferenceUid]);

  useFocusEffect(
    useCallback(() => {
      refetch();
      const id = setInterval(refetch, POLL_MS);
      return () => clearInterval(id);
    }, [refetch]),
  );

  const { connected } = useLiveQuizChannel(conferenceUid, token, refetch);

  const liveQuestion = view?.state === "QUESTION_LIVE" ? (view.question ?? null) : null;
  const onLiveQuestion = !!liveQuestion && resolvedQuestionId !== liveQuestion.id && !feedback;
  const secondsLeft = useCountdown(onLiveQuestion ? view?.timerEndsAt : null, view?.serverNowMs);

  // Timer expired and we never answered - `revealAsTimeout` sets `feedback`,
  // which flips `onLiveQuestion` false so this won't re-fire.
  useEffect(() => {
    if (!onLiveQuestion || !liveQuestion || !view?.timerEndsAt || secondsLeft > 0 || selectedOption) return;
    revealAsTimeout(liveQuestion, null);
  }, [onLiveQuestion, liveQuestion, view?.timerEndsAt, secondsLeft, selectedOption, revealAsTimeout]);

  // Trainer ended the quiz - straight to the rank page.
  useEffect(() => {
    if (view?.state !== "FINISHED") return;
    router.replace({ pathname: "/quiz_leaderboard", params: { conferenceUid: conferenceUid ?? "" } });
  }, [view?.state, conferenceUid, router]);

  const selectOption = useCallback(
    async (optionId: string) => {
      if (!onLiveQuestion || !liveQuestion || !token || !conferenceUid || selectedOption) return;
      setSelectedOption(optionId);
      try {
        const res = await submitLiveAnswer(token, conferenceUid, liveQuestion.id, optionId);
        if (res.accepted) {
          setFeedback({
            kind: res.correct ? "correct" : "incorrect",
            question: liveQuestion,
            selectedOptionId: optionId,
            correctOptionId: res.correctOptionId ?? null,
            explanation: res.explanation ?? null,
          });
        } else {
          revealAsTimeout(liveQuestion, optionId);
        }
      } catch {
        // keep the local selection; a later refetch reconciles
      }
    },
    [onLiveQuestion, liveQuestion, token, conferenceUid, selectedOption, revealAsTimeout],
  );

  const onFinalSubmit = useCallback(async () => {
    if (!token || !conferenceUid || submitting) return;
    setSubmitting(true);
    try {
      await submitLiveQuiz(token, conferenceUid);
      router.replace({ pathname: "/quiz_leaderboard", params: { conferenceUid } });
    } catch {
      setSubmitting(false);
    }
  }, [token, conferenceUid, submitting, router]);

  // Answering / timing out on the LAST question flips straight to the read-only
  // Assessment Map (no feedback card). Derived from `feedback` - which both
  // selectOption and revealAsTimeout set only after an await - so there's no
  // state to keep in sync and `refetch` clearing `feedback` resets it too.
  const reachedMap = !!feedback && isLastQuestion(feedback.question);

  const phase: LiveQuizPhase =
    view?.state === "FINISHED"
      ? "finished"
      : reachedMap
        ? "map"
        : feedback
          ? "feedback"
          : onLiveQuestion
            ? "question"
            : "waiting";

  return {
    view,
    phase,
    feedback,
    loadError,
    selectedOption,
    secondsLeft,
    submitting,
    connected,
    conferenceUid,
    token,
    selectOption,
    onFinalSubmit,
    refetch,
    router,
  };
}
