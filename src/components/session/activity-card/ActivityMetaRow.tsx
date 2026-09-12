import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { SessionActivityData } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import { FontSize, FontWeight } from "@/theme/typography";

type ActivityMetaRowProps = {
  activity: SessionActivityData;
  isAttendance: boolean;
  isQuizOrPostTest: boolean;
};

export default function ActivityMetaRow({ activity, isAttendance, isQuizOrPostTest }: ActivityMetaRowProps) {
  const { isCompleted, duration, completedAt } = activity;

  return (
    <View style={styles.metaRow}>
      <View style={styles.durationPill}>
        <AppText variant="overline" weight={FontWeight.bold} color="#374151" style={styles.durationText}>
          {duration}
        </AppText>
      </View>

      {isCompleted && isAttendance && (
        <View style={styles.presenceInfo}>
          <View style={styles.presenceDot} />
          <AppText variant="tiny" weight={FontWeight.semiBold} color={Colors.recordedGreen}>
            {completedAt ? `Present (${completedAt})` : "Present (10:25)"}
          </AppText>
        </View>
      )}

      {isCompleted && isQuizOrPostTest && (
        <View style={styles.completedQuizInfo}>
          <Ionicons name="trophy" size={14} color="#F59E0B" />
          <AppText variant="caption" color={Colors.headerBlue} weight={FontWeight.semiBold}>
            {completedAt ?? "Completed successfully"}
          </AppText>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 8,
  },
  durationPill: {
    backgroundColor: Colors.gray100,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  durationText: {
    fontSize: FontSize.overline,
    textTransform: "lowercase",
  },
  presenceInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  presenceDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.recordedGreen,
  },
  completedQuizInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
});
