import React from "react";
import type { ComponentType } from "react";
import type { SvgProps } from "react-native-svg";
import { Ionicons } from "@expo/vector-icons";

import type { SessionModuleKey } from "@/api/session";
import { SessionActivityData } from "@/hooks/useTraineeHome";
import SessionTimelineItem from "./SessionTimelineItem";

export type SessionItem = {
  key: SessionModuleKey;
  time: string;
  endTime: string;
  duration: string;
  type: string;
  isLive: boolean;
  isCompleted: boolean;
  isMissed: boolean;
  completedAt: string | null;
  score: string | null;
  icon?: keyof typeof Ionicons.glyphMap | ComponentType<SvgProps>;
  iconColor?: string;
  geoFencing?: boolean;
};

type Props = {
  session: SessionItem;
  isLast?: boolean;
  onMarkAttendance: () => void;
  onEnterQuiz: () => void;
  onEnterPostTest: () => void;
  onEnterSurvey: () => void;
};

export default function TimelineItem({
  session,
  isLast = false,
  onMarkAttendance,
  onEnterQuiz,
  onEnterPostTest,
  onEnterSurvey,
}: Props) {
  const activityData: SessionActivityData = {
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
  };

  return (
    <SessionTimelineItem
      activity={activityData}
      isLast={isLast}
      onMarkAttendance={onMarkAttendance}
      onEnterQuiz={onEnterQuiz}
      onEnterPostTest={onEnterPostTest}
      onEnterSurvey={onEnterSurvey}
      // This wrapper's `SessionItem` never sets `locationGateEnabled`, so the
      // gate is always off here - no handler ever fires.
      onCheckInLocation={() => {}}
    />
  );
}

