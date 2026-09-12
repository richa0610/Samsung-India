import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { SessionActivityData } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import SessionActivityCard from "./SessionActivityCard";

export type SessionTimelineItemProps = {
  activity: SessionActivityData;
  isLast?: boolean;
  onMarkAttendance: () => void;
  onEnterQuiz: () => void;
  onEnterPostTest: () => void;
  onEnterSurvey: () => void;
  onCheckInLocation: (moduleKey: SessionActivityData["key"]) => void;
};

export default function SessionTimelineItem({
  activity,
  isLast = false,
  onMarkAttendance,
  onEnterQuiz,
  onEnterPostTest,
  onEnterSurvey,
  onCheckInLocation,
}: SessionTimelineItemProps) {
  const dotColor = activity.isCompleted
    ? Colors.recordedGreen
    : activity.isMissed
      ? Colors.danger
      : Colors.headerBlue;

  return (
    <View style={styles.timelineRow}>
      {/* Left Time Column */}
      <View style={styles.timeColumn}>
        <AppText style={styles.startTime} weight={FontWeight.bold}>
          {activity.startTime}
        </AppText>
        <AppText style={styles.endTime} weight={FontWeight.medium}>
          {activity.endTime}
        </AppText>
      </View>

      {/* Vertical Rail with Indicator Dot and Connecting Line */}
      <View style={styles.rail}>
        <View style={[styles.dot, { backgroundColor: dotColor }]} />
        {!isLast && <View style={styles.railLine} />}
      </View>

      {/* Configurable Activity Card */}
      <SessionActivityCard
        activity={activity}
        onMarkAttendance={onMarkAttendance}
        onEnterQuiz={onEnterQuiz}
        onEnterPostTest={onEnterPostTest}
        onEnterSurvey={onEnterSurvey}
        onCheckInLocation={onCheckInLocation}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  timelineRow: {
    flexDirection: "row",
    minHeight: 104,
  },
  timeColumn: {
    width: 48,
    alignItems: "flex-end",
    paddingTop: 2,
  },
  startTime: {
    fontSize: 12,
    color: Colors.black,
  },
  endTime: {
    fontSize: 10,
    color: Colors.gray600,
    marginTop: 2,
  },

  rail: {
    width: 28,
    alignItems: "center",
    paddingTop: 6,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    zIndex: 2,
  },
  railLine: {
    position: "absolute",
    top: 14,
    bottom: -16,
    width: 1.5,
    backgroundColor: Colors.timelineRail,
  },
});
