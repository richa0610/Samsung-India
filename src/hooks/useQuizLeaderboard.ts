/**
 * useQuizLeaderboard Hook
 * Powers the trainee Rank page. It only ever shows real data: once a Live Quiz
 * has been ended by the trainer it renders the true per-session ranking (score
 * DESC, then total response time ASC). Before that it reports the live state
 * ("in_progress" / "submitted"), and with no Live Quiz at all ("none") the
 * screen shows an empty state - there is no sample/mock fallback.
 */

import { LeaderboardFilterValues } from "@/components/quiz/LeaderboardFilter";
import { LeaderboardUser } from "@/components/quiz/LeaderboardRow";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { LiveQuizResults, getCurrentSession, getLiveQuizResults } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { useLiveQuizChannel } from "@/hooks/useLiveQuizChannel";

function formatMs(ms: number): string {
  const s = Math.round(ms / 1000);
  return s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`;
}

const pct = (n: number) => `${Number.isInteger(n) ? n : n.toFixed(1)}%`;

export type RankLiveState = "none" | "in_progress" | "submitted" | "live" | "ranked";

// Re-poll the board this often while the quiz is still running.
const LIVE_POLL_MS = 5000;

export function useQuizLeaderboard() {
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = useWindowDimensions();
  const router = useRouter();
  const params = useLocalSearchParams<{ conferenceUid?: string }>();
  const { token } = useAuth();

  const [conferenceUid, setConferenceUid] = useState<string | null>(params.conferenceUid ?? null);
  const [results, setResults] = useState<LiveQuizResults | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      let uid = params.conferenceUid ?? conferenceUid;
      if (!uid) {
        uid = (await getCurrentSession(token)).conferenceUid;
        setConferenceUid(uid);
      }
      if (uid) setResults(await getLiveQuizResults(token, uid));
    } catch {
      setResults(null);
    }
  }, [token, params.conferenceUid, conferenceUid]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );
  useLiveQuizChannel(conferenceUid, token, load);

  const liveState: RankLiveState = (results?.state as RankLiveState) ?? "none";
  // The full results view (score card + performance summary + leaderboard) is
  // shown as soon as the trainee has submitted - "live" while the quiz runs and
  // the board keeps re-polling, "ranked" once the trainer ends it (final).
  const showResults = liveState === "live" || liveState === "ranked";
  const you = results?.you ?? null;

  // While the quiz is still running, refetch the board every few seconds so new
  // submissions and re-ranks show without a manual pull. Stops once `finished`.
  const quizFinished = results?.finished ?? false;
  const hasResults = results != null;
  useEffect(() => {
    if (!conferenceUid || !hasResults || quizFinished || liveState === "none") return;
    const id = setInterval(load, LIVE_POLL_MS);
    return () => clearInterval(id);
  }, [conferenceUid, hasResults, quizFinished, liveState, load]);

  const total = showResults ? results!.totalQuestions : 0;
  const correct = showResults ? results!.correctCount : 0;
  const incorrect = Math.max(0, total - correct);
  const accuracy = showResults ? Math.round(you?.percentage ?? 0) : 0;
  const timeTakenFormatted = showResults
    ? formatMs(you?.totalResponseMs ?? (results!.durationSeconds ?? 0) * 1000)
    : "—";

  const [filterOpen, setFilterOpen] = useState(false);
  const [filterValues, setFilterValues] = useState<LeaderboardFilterValues>({
    trainingType: "",
    state: "",
    district: "",
    zone: "",
  });

  const leaderboardUsers = useMemo<LeaderboardUser[]>(() => {
    if (!showResults || !results) return [];
    return results.leaderboard.map((r) => ({
      name: r.isYou ? "You" : r.name,
      score: `${r.score}/${r.maxScore}`,
      accuracy: pct(r.percentage),
      isYou: r.isYou,
    }));
  }, [showResults, results]);

  const handleApplyFilter = () => setFilterOpen(false);
  const handleContinue = () => router.replace("/session_detail");

  return {
    insets,
    screenWidth,
    liveState,
    showResults,
    isLive: liveState === "live",
    quizEnded: quizFinished,
    yourRank: you?.rank ?? null,
    total,
    correct,
    accuracy,
    incorrect,
    timeTakenFormatted,
    filterOpen,
    setFilterOpen,
    filterValues,
    setFilterValues,
    leaderboardUsers,
    handleApplyFilter,
    handleContinue,
  };
}
