import { useLocalSearchParams, useRouter } from "expo-router";

import AccessGrantedView from "@/components/attendance/AccessGrantedView";
import AttendanceCheckingInView from "@/components/attendance/AttendanceCheckingInView";
import AttendanceErrorView from "@/components/attendance/AttendanceErrorView";
import { setSessionFlowState } from "@/api/session";
import { useAttendance } from "@/hooks/useAttendance";

export default function AttendanceScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    conferenceUid: string;
    title?: string;
    location?: string;
    time?: string;
    endTime?: string;
  }>();

  const { status, markedOn, error, retry, confirmAttendanceRecorded } = useAttendance(params.conferenceUid);

  const handleNavigateToSession = () => {
    confirmAttendanceRecorded();
    router.replace({
      pathname: "/session_detail",
      params: { flow: "ATTENDANCE_RECORDED", attendance: "completed" },
    });
  };

  if (status === "checking-in") {
    return <AttendanceCheckingInView onBack={() => router.back()} />;
  }

  if (status === "error") {
    return <AttendanceErrorView error={error} onRetry={retry} onBack={() => router.back()} />;
  }

  return (
    <AccessGrantedView
      details={[
        {
          label: "Session",
          value: params.title || "Training Session",
          icon: "calendar-outline",
        },
        {
          label: "Time",
          value: [params.time, params.endTime].filter(Boolean).join(" - ") || "--",
          icon: "time-outline",
        },
        {
          label: "Checked In",
          value: markedOn ? (markedOn.split(" ")[1]?.slice(0, 5) ?? markedOn) : "--",
          icon: "calendar-outline",
        },
        {
          label: "Location",
          value: params.location || "--",
          icon: "location-outline",
        },
      ]}
      onContinue={handleNavigateToSession}
      onHome={() => {
        setSessionFlowState("CAMERA_VERIFIED");
        router.replace({
          pathname: "/session_detail",
          params: { flow: "CAMERA_VERIFIED", checkIn: "verified" },
        });
      }}
    />
  );
}
