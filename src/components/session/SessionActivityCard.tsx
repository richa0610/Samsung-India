import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { SessionActivityData } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { ActivityCta, ActivityMetaRow, HeaderBadges, TypeIcon } from "./activity-card";

export type SessionActivityCardProps = {
  activity: SessionActivityData;
  onMarkAttendance: () => void;
  onEnterQuiz: () => void;
  onEnterPostTest: () => void;
  onEnterSurvey: () => void;
  onCheckInLocation: (moduleKey: SessionActivityData["key"]) => void;
};

export default function SessionActivityCard({
  activity,
  onMarkAttendance,
  onEnterQuiz,
  onEnterPostTest,
  onEnterSurvey,
  onCheckInLocation,
}: SessionActivityCardProps) {
  const { key } = activity;
  const isAttendance = key === "ATTENDANCE";
  const isQuiz = key === "LIVE_QUIZ";
  const isPostTest = key === "STANDARD_TEST";

  const handleEnterAction = () => {
    if (key === "LIVE_QUIZ") {
      onEnterQuiz();
    } else if (key === "SURVEY") {
      onEnterSurvey();
    } else if (key === "STANDARD_TEST") {
      onEnterPostTest();
    } else if (isAttendance) {
      onMarkAttendance();
    }
  };

  return (
    <View style={styles.cardContainer}>
      <View style={styles.cardHeader}>
        <View style={styles.typeSection}>
          <TypeIcon isAttendance={isAttendance} isQuiz={isQuiz} />
          <AppText variant="overline" color={isAttendance ? Colors.recordedGreen : Colors.headerBlue} weight={FontWeight.bold}>
            {activity.type}
          </AppText>
        </View>

        <HeaderBadges activity={activity} />
      </View>

      <AppText variant="body" weight={FontWeight.bold} style={styles.activityTitle}>
        {activity.title}
      </AppText>

      <ActivityMetaRow activity={activity} isAttendance={isAttendance} isQuizOrPostTest={isQuiz || isPostTest} />

      <ActivityCta
        activity={activity}
        isAttendance={isAttendance}
        onMarkAttendance={onMarkAttendance}
        onEnterAction={handleEnterAction}
        onCheckInLocation={() => onCheckInLocation(activity.key)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    flex: 1,
    backgroundColor: Colors.white,
    padding: 14,
    borderRadius: Radius.card,
    ...Shadows.timelineCard,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  typeSection: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  activityTitle: {
    marginTop: 8,
    color: Colors.black,
  },
});
