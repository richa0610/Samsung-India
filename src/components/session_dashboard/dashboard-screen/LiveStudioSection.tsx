import { Fragment } from "react";

import { LiveStudio } from "@/api/training";
import LiveStudioCard from "@/components/session_dashboard/LiveStudioCard";
import ParticipantAttendanceCard from "@/components/session_dashboard/ParticipantAttendanceCard";
import { LiveQuizControls, ParticipantItem } from "@/components/session_dashboard/sessionDashboardTypes";

type LiveStudioSectionProps = {
  participants: ParticipantItem[];
  liveStudio: LiveStudio | null;
  liveQuizControls: LiveQuizControls;
  onRefresh: () => void;
  canEditAttendance: boolean;
  onMarkAttendance: (traineeUid: string, status: "Present" | "Absent", reason: string) => void;
  onUnlockExam: (traineeUid: string, reason: string) => void;
};

export default function LiveStudioSection({
  participants,
  liveStudio,
  liveQuizControls,
  onRefresh,
  canEditAttendance,
  onMarkAttendance,
  onUnlockExam,
}: LiveStudioSectionProps) {
  return (
    <Fragment>
      {liveStudio && <LiveStudioCard liveStudio={liveStudio} controls={liveQuizControls} />}

      <ParticipantAttendanceCard
        participants={participants}
        onRefresh={onRefresh}
        canEdit={canEditAttendance}
        onMark={onMarkAttendance}
        onUnlock={onUnlockExam}
      />
    </Fragment>
  );
}
