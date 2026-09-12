import { SessionActivityData } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import RecordedCard from "../RecordedCard";
import SessionButton from "../SessionButton";
import WaitingCard from "../WaitingCard";
import LockedViolationCard from "./LockedViolationCard";
import LocationVerifyingCard from "./LocationVerifyingCard";
import MissedBanner from "./MissedBanner";

type ActivityCtaProps = {
  activity: SessionActivityData;
  isAttendance: boolean;
  onMarkAttendance: () => void;
  onEnterAction: () => void;
  onCheckInLocation: () => void;
};

export default function ActivityCta({
  activity,
  isAttendance,
  onMarkAttendance,
  onEnterAction,
  onCheckInLocation,
}: ActivityCtaProps) {
  const {
    isCompleted,
    isLive,
    isMissed,
    isLocked,
    lockReason,
    securityCheckInCompleted,
    locationGateEnabled,
    locationGateStatus,
  } = activity;

  if (isCompleted) {
    return (
      <RecordedCard
        title={isAttendance ? "Recorded" : "Completed"}
        subtitle="Good Job !"
        color={Colors.recordedGreen}
        backgroundColor={Colors.recordedGreenBg}
      />
    );
  }

  // Admission gate: the trainer hasn't marked this trainee present, so the
  // module's action (check-in / enter) is blocked even if it's LIVE.
  if (lockReason) {
    return <WaitingCard title="Locked" subtitle={lockReason} />;
  }

  if (isLive && isAttendance) {
    return (
      <SessionButton
        title={securityCheckInCompleted ? "Mark Attendance" : "Secure Check-In"}
        icon={securityCheckInCompleted ? undefined : "camera"}
        onPress={onMarkAttendance}
        backgroundColor={Colors.recordedGreen}
      />
    );
  }

  // Non-attendance module on a geofenced training: the trainee must check
  // in with their live GPS before "Enter Session" appears, so we can track
  // them at every module, not just Attendance.
  if (isLive && locationGateEnabled && locationGateStatus !== "verified") {
    if (locationGateStatus === "checking") {
      return <LocationVerifyingCard />;
    }
    return (
      <SessionButton
        title="Check-In to Enter"
        icon="location"
        onPress={onCheckInLocation}
        backgroundColor={Colors.headerBlue}
      />
    );
  }

  if (isLive) {
    return <SessionButton title="Enter Session" onPress={onEnterAction} backgroundColor={Colors.headerBlue} />;
  }

  if (isMissed) return <MissedBanner />;
  if (isLocked) return <LockedViolationCard />;

  return <WaitingCard title="Please Wait" subtitle="Trainer will unlock soon..." />;
}
