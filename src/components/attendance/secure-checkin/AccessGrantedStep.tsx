import { useRouter } from "expo-router";

import { VerifyLocationResult } from "@/api/attendance";
import { setAttendanceState, setSessionFlowState } from "@/api/session";
import AccessGrantedView from "@/components/attendance/AccessGrantedView";
import { formatDisplayDate } from "@/utils/formatDisplayDate";

type AccessGrantedStepParams = {
  title?: string;
  time?: string;
  endTime?: string;
  date?: string;
  location?: string;
};

type AccessGrantedStepProps = {
  params: AccessGrantedStepParams;
  locationResult: VerifyLocationResult | null;
  router: ReturnType<typeof useRouter>;
};

export default function AccessGrantedStep({ params, locationResult, router }: AccessGrantedStepProps) {
  return (
    <AccessGrantedView
      details={[
        { label: "Session", value: params.title || "Training Session", icon: "calendar-outline" },
        {
          label: "Time",
          value: [params.time, params.endTime].filter(Boolean).join(" - ") || params.time || "--",
          icon: "time-outline",
        },
        { label: "Date", value: formatDisplayDate(params.date ?? null), icon: "calendar-outline" },
        {
          label: "Location",
          value: params.location || locationResult?.venueLabel || "--",
          icon: "location-outline",
        },
      ]}
      onContinue={() => {
        setAttendanceState("ATTENDANCE_RECORDED");
        router.replace({ pathname: "/session_detail", params: { attendance: "completed", checkIn: "verified" } });
      }}
      onHome={() => {
        setSessionFlowState("CAMERA_VERIFIED");
        router.replace({ pathname: "/session_detail", params: { flow: "CAMERA_VERIFIED", checkIn: "verified" } });
      }}
    />
  );
}
