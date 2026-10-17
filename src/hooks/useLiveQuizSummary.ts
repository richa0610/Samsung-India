import { useCallback, useEffect, useState } from "react";

import { getLiveQuizSummary, LiveQuizSummary } from "@/api/session";

/**
 * Fetches the trainee's per-question outcome map for the Live Quiz once they
 * reach the end-of-quiz Assessment Map (`active`), and owns the read-only
 * recap sheet's open/index state. Kept separate so useLiveQuiz stays lean.
 */
export function useLiveQuizSummary(
  conferenceUid: string | undefined,
  token: string | null | undefined,
  active: boolean,
) {
  const [summary, setSummary] = useState<LiveQuizSummary | null>(null);
  const [loading, setLoading] = useState(false);
  // null = recap sheet closed; a number = the question index being reviewed.
  const [recapIndex, setRecapIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!active || !conferenceUid || !token || summary) return;
    let ignore = false;
    async function load(activeToken: string, uid: string) {
      setLoading(true);
      try {
        const next = await getLiveQuizSummary(activeToken, uid);
        if (!ignore) setSummary(next);
      } catch {
        // Non-fatal - the map just won't render; Final Submit still works.
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load(token, conferenceUid);
    return () => {
      ignore = true;
    };
  }, [active, conferenceUid, token, summary]);

  const openRecap = useCallback((index: number) => setRecapIndex(index), []);
  const openReview = useCallback(() => setRecapIndex(0), []);
  const closeRecap = useCallback(() => setRecapIndex(null), []);
  const stepRecap = useCallback(
    (delta: number) =>
      setRecapIndex((current) => {
        if (current === null || !summary) return current;
        return Math.min(Math.max(current + delta, 0), summary.questions.length - 1);
      }),
    [summary],
  );

  return { summary, loading, recapIndex, openRecap, openReview, closeRecap, stepRecap };
}
