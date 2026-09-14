import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { LiveStudioQuestion } from "./sessionDashboardTypes";

type Props = {
  question: LiveStudioQuestion;
  /** Seconds left on this question's timer - only passed for the active one. */
  secondsLeft?: number;
  onBroadcast: (questionId: number) => void;
};

export default function LiveStudioQuestionRow({ question: q, secondsLeft, onBroadcast }: Props) {
  return (
    <View style={[styles.row, q.isActive && styles.rowActive]}>
      <View style={styles.badgesCol}>
        <View style={styles.numPill}>
          <AppText style={styles.numText}>{q.qNumber}</AppText>
        </View>
        <View style={styles.timerPill}>
          <Ionicons name="alarm-outline" size={10} color={Colors.headerBlue} />
          <AppText style={styles.timerText}>
            {q.isActive && secondsLeft !== undefined ? `${secondsLeft}s` : `${q.timerSecs}s`}
          </AppText>
        </View>
      </View>

      <View style={styles.textCol}>
        <AppText style={styles.qText} numberOfLines={2}>{q.questionText}</AppText>
        <AppText style={styles.metaText}>{q.points} pts · {q.responseCount} responses</AppText>
      </View>

      <Pressable
        style={[styles.broadcastBtn, q.isActive && styles.broadcastBtnActive]}
        onPress={() => onBroadcast(q.id)}
      >
        <Ionicons name={q.isActive ? "radio" : "play"} size={10} color={Colors.white} />
        <AppText style={styles.broadcastBtnText}>{q.isActive ? "Live" : "Broadcast"}</AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.gray50,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    padding: 7,
    gap: 6,
  },
  rowActive: { borderColor: "#10B981", backgroundColor: "#F0FDF4" },
  badgesCol: { gap: 2, alignItems: "flex-start" },
  numPill: { backgroundColor: "#1F2937", paddingHorizontal: 4, paddingVertical: 1.5, borderRadius: 4 },
  numText: { fontSize: 8, fontWeight: "800", color: Colors.white },
  timerPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    backgroundColor: Colors.waitingBlueBg,
    borderWidth: 1,
    borderColor: Colors.notificationIconBg,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 8,
  },
  timerText: { fontSize: 8, fontWeight: "700", color: Colors.headerBlue },
  textCol: { flex: 1, gap: 2 },
  qText: { fontSize: 9, color: "#1F2937", fontWeight: "500", lineHeight: 12.5 },
  metaText: { fontSize: 7.5, color: "#6B7280", fontWeight: "600" },
  broadcastBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    backgroundColor: "#0066FF",
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 6,
  },
  broadcastBtnActive: { backgroundColor: "#10B981" },
  broadcastBtnText: { fontSize: 8.5, fontWeight: "700", color: Colors.white },
});
