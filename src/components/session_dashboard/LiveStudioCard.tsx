import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { LiveStudio } from "@/api/training";
import { useCountdown } from "@/hooks/useCountdown";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import LiveStudioActions from "./LiveStudioActions";
import LiveStudioQuestionRow from "./LiveStudioQuestionRow";
import { LiveQuizControls } from "./sessionDashboardTypes";

const STATE_LABELS: Record<string, string> = {
  IDLE: "LOBBY",
  WAITING: "LOBBY",
  QUESTION_LIVE: "LIVE",
  LEADERBOARD: "LEADERBOARD",
  FINISHED: "FINISHED",
};

export default function LiveStudioCard({
  liveStudio,
  controls,
}: {
  liveStudio: LiveStudio;
  controls: LiveQuizControls;
}) {
  const { state, activeQuestionId, timerEndsAt, timerRemainingMs, serverNowMs, totalResponses, participants, questions } =
    liveStudio;
  const isPaused = timerRemainingMs != null;
  // While paused, timerEndsAt is stale (frozen at whatever it was when Stop
  // Timer was pressed) - show the frozen remaining value instead of letting
  // the countdown keep ticking against it.
  const runningSecondsLeft = useCountdown(state === "QUESTION_LIVE" && !isPaused ? timerEndsAt : null, serverNowMs);
  const secondsLeft = isPaused ? Math.ceil(timerRemainingMs / 1000) : runningSecondsLeft;
  const activeOrder = questions.find((q) => q.id === activeQuestionId)?.order ?? null;

  return (
    <View style={styles.card}>
      <View style={styles.headerBanner}>
        <View style={styles.headerTitleRow}>
          <Ionicons name="radio" size={15} color={Colors.white} />
          <AppText style={styles.headerTitle}>LIVE STUDIO</AppText>
        </View>
        <AppText style={styles.headerSuite} numberOfLines={1}>{liveStudio.suiteTitle}</AppText>
      </View>

      <View style={styles.summaryRow}>
        <Summary label="STATE" value={isPaused ? "PAUSED" : (STATE_LABELS[state] ?? state)} color="#2563EB" />
        <Summary label="ACTIVE Q" value={activeOrder ? `Q${activeOrder}` : "—"} />
        <Summary
          label="TIME LEFT"
          value={state === "QUESTION_LIVE" ? `${secondsLeft}s` : "—"}
          color={state === "QUESTION_LIVE" && secondsLeft <= 5 ? "#DC2626" : "#EA580C"}
        />
        <Summary
          label="RESPONSES"
          value={`${totalResponses}/${participants}`}
          color="#10B981"
          highlighted
        />
      </View>

      <View style={styles.questionsList}>
        {questions.map((q) => (
          <LiveStudioQuestionRow
            key={q.id}
            question={{
              id: q.id,
              qNumber: `Q${q.order}`,
              timerSecs: q.timerSeconds,
              questionText: q.text,
              points: q.points,
              responseCount: q.responseCount,
              isActive: q.isActive,
            }}
            secondsLeft={q.isActive ? secondsLeft : undefined}
            onBroadcast={controls.onBroadcast}
          />
        ))}
        {questions.length === 0 && (
          <AppText style={styles.empty}>No questions configured for this Live Quiz.</AppText>
        )}
      </View>

      <LiveStudioActions
        state={state}
        isPaused={isPaused}
        questions={questions}
        activeQuestionId={activeQuestionId}
        controls={controls}
      />
    </View>
  );
}

function Summary({
  label,
  value,
  color,
  highlighted,
}: {
  label: string;
  value: string;
  color?: string;
  highlighted?: boolean;
}) {
  return (
    <View style={[styles.summaryBox, highlighted && styles.summaryBoxHighlighted]}>
      <AppText style={styles.summaryLabel}>{label}</AppText>
      <AppText style={[styles.summaryValue, color ? { color } : null]}>{value}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    overflow: "hidden",
    marginHorizontal: 14,
    marginTop: 10,
    ...Shadows.card,
  },
  headerBanner: {
    backgroundColor: "#0066FF",
    paddingVertical: 9,
    paddingHorizontal: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  headerTitleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  headerTitle: { fontSize: 11.5, fontWeight: "800", color: Colors.white, letterSpacing: 0.3 },
  headerSuite: { flex: 1, textAlign: "right", fontSize: 8.5, fontWeight: "700", color: "rgba(255,255,255,0.85)" },
  summaryRow: { flexDirection: "row", gap: 6, padding: 10 },
  summaryBox: {
    flex: 1,
    backgroundColor: Colors.gray50,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    paddingVertical: 6,
    alignItems: "center",
  },
  summaryBoxHighlighted: { backgroundColor: "#FFFFFF", borderColor: "#10B981", borderWidth: 1.5 },
  summaryLabel: { fontSize: 7.5, fontWeight: "700", color: "#6B7280" },
  summaryValue: { fontSize: 12.5, fontWeight: "800", color: "#111827", marginTop: 1 },
  questionsList: { paddingHorizontal: 10, gap: 5, marginBottom: 10 },
  empty: { fontSize: 9, color: "#6B7280", textAlign: "center", paddingVertical: 16 },
});
