import React, { ReactElement, ReactNode } from "react";
import { RefreshControlProps, ScrollView, StyleSheet, View } from "react-native";

import SessionTimelineItem from "./SessionTimelineItem";
import { SessionItem } from "./TimelineItem";
import { SessionActivityData } from "@/hooks/useTraineeHome";

type Props = {
  activities?: SessionActivityData[];
  sessions?: SessionItem[];
  /** Render greyed-out and non-interactive (trainer hasn't started the session). */
  dimmed?: boolean;
  onMarkAttendance: () => void;
  onEnterQuiz: () => void;
  onEnterPostTest: () => void;
  onEnterSurvey: () => void;
  onCheckInLocation: (moduleKey: SessionActivityData["key"]) => void;
  footerComponent?: ReactNode;
  refreshControl?: ReactElement<RefreshControlProps>;
};

export default function SessionTimeline({
  activities,
  sessions,
  dimmed = false,
  onMarkAttendance,
  onEnterQuiz,
  onEnterPostTest,
  onEnterSurvey,
  onCheckInLocation,
  footerComponent,
  refreshControl,
}: Props) {
  // Normalize activities from either activities or sessions prop
  const items: SessionActivityData[] =
    activities ??
    (sessions ?? []).map((session) => ({  
      id: session.key,
      key: session.key,
      startTime: session.time || "09:00",
      endTime: session.endTime || "10:00",
      duration: session.duration || "1h",
      type: session.type,
      title: "Session Activity",
      isLive: session.isLive,
      isCompleted: session.isCompleted,
      isMissed: session.isMissed,
      completedAt: session.completedAt,
      score: session.score,
      geoFencing: session.geoFencing,
    }));

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
      refreshControl={refreshControl}
    >
      <View
        style={[styles.itemList, dimmed && styles.dimmed]}
        pointerEvents={dimmed ? "none" : "auto"}
      >
        {items.map((activity, index) => (
          <SessionTimelineItem
            key={activity.id ?? activity.key}
            activity={activity}
            isLast={index === items.length - 1}
            onMarkAttendance={onMarkAttendance}
            onEnterQuiz={onEnterQuiz}
            onEnterPostTest={onEnterPostTest}
            onEnterSurvey={onEnterSurvey}
            onCheckInLocation={onCheckInLocation}
          />
        ))}
      </View>

      {footerComponent && (
        <View style={styles.footerWrap}>{footerComponent}</View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    paddingTop: 16,
    paddingHorizontal: 16,
    paddingBottom: 28,
    flexGrow: 1,
  },
  itemList: {
    gap: 14,
  },
  dimmed: {
    opacity: 0.5,
  },
  footerWrap: {
    marginTop: 14,
  },
});
