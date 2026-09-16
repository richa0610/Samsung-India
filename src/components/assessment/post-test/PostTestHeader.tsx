import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontSize } from "@/theme/typography";

type PostTestHeaderProps = {
  remainingMinutes: number;
  remainingSecondsPart: number;
  questionIndex: number;
  questionsLength: number;
};

export default function PostTestHeader({
  remainingMinutes,
  remainingSecondsPart,
  questionIndex,
  questionsLength,
}: PostTestHeaderProps) {
  const percent = Math.round(((questionIndex + 1) / questionsLength) * 100);

  return (
    <View style={styles.header}>
      <View style={styles.headerRow}>
        <View style={styles.timer}>
          <Ionicons name="time-outline" size={14} color={Colors.primary} />
          <AppText style={styles.timerText}>
            {String(remainingMinutes).padStart(2, "0")}:{String(remainingSecondsPart).padStart(2, "0")}
          </AppText>
        </View>
        <View style={styles.progress}>
          <AppText style={styles.progressText}>Overall Progress</AppText>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${percent}%` }]} />
          </View>
          <AppText style={styles.progressPercent}>{percent}%</AppText>
        </View>
        <View style={styles.headerIcon}>
          <Ionicons name="cloud-outline" size={17} color={Colors.primary} />
        </View>
        <View style={styles.wifi}>
          <Ionicons name="wifi" size={15} color={Colors.white} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: { backgroundColor: Colors.mainColour1, padding: 9 },
  headerRow: {
    height: 30,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  timer: {
    height: 22,
    paddingHorizontal: 6,
    borderRadius: 4,
    backgroundColor: Colors.white,
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  timerText: { color: Colors.primary, fontSize: FontSize.overline },
  progress: {
    flex: 1,
    height: 22,
    backgroundColor: Colors.white,
    borderRadius: 4,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 5,
    gap: 5,
  },
  progressText: { fontSize: FontSize.tiny, color: Colors.black },
  progressTrack: {
    flex: 1,
    height: 6,
    backgroundColor: Colors.gray100,
    borderRadius: 3,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: Colors.primary,
    borderRadius: 3,
  },
  progressPercent: {
    fontSize: FontSize.tiny,
    color: Colors.black,
    minWidth: 26,
    textAlign: "right",
  },
  headerIcon: {
    width: 22,
    height: 22,
    borderRadius: 3,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  wifi: {
    width: 22,
    height: 22,
    borderRadius: 3,
    backgroundColor: "#16A34A",
    alignItems: "center",
    justifyContent: "center",
  },
});
