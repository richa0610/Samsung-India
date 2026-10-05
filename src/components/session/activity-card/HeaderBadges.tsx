import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { SessionActivityData } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";
import SessionStatusBadge from "../SessionStatusBadge";
import { getStatusLabel } from "./getStatusLabel";

type HeaderBadgesProps = {
  activity: SessionActivityData;
};

export default function HeaderBadges({ activity }: HeaderBadgesProps) {
  const { key, isLive, isCompleted, isMissed, isLocked } = activity;
  const isAttendance = key === "ATTENDANCE";
  const isQuiz = key === "LIVE_QUIZ";
  const isPostTest = key === "STANDARD_TEST";

  return (
    <View style={styles.headerBadges}>
      {activity.ranDuration ? (
        <View style={styles.runtimePill}>
          <AppText variant="tiny" color={Colors.gray600} weight={FontWeight.medium}>
            {activity.ranDuration}
          </AppText>
        </View>
      ) : null}

      <SessionStatusBadge
        label={getStatusLabel(activity)}
        live={isLive && !isLocked}
        liveColor={isAttendance ? Colors.recordedGreen : Colors.headerBlue}
        completed={isCompleted && isAttendance}
        scoreBadge={isCompleted && (isQuiz || isPostTest) && !!activity.score}
        missed={isMissed}
        locked={isLocked}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  headerBadges: {
    flexDirection: "column",
    alignItems: "center",
    gap: 6,
  },
  runtimePill: {
    backgroundColor: Colors.gray100,
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 4,
  },
});
