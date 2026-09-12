/**
 * useAttendance Hook
 * Runs the final attendance write once the trainee reaches the "Mark Attendance"
 * step, then exposes its lifecycle (checking-in / done / error) to the screen.
 *
 * The Secure Check-In screen stashes the verified location + photo
 * (`getPendingCheckIn`) for every session now, so this normally submits them
 * to `/attendance/check-in/secure` - which attaches the proof to the row the
 * trainer already marked "Present" (and, for a geofenced session, re-checks
 * the venue radius). The plain `/attendance/check-in` is only a fallback for
 * when no coordinates were captured at all.
 */

import { useCallback, useEffect, useState } from "react";
import { Alert } from "react-native";
import { useAuth } from "@/hooks/useAuth";
import { AttendanceRecord, ApiError, checkIn, secureCheckIn } from "@/api/attendance";
import { clearPendingCheckIn, getPendingCheckIn, setSessionFlowState } from "@/api/session";

export type AttendanceStatus = "checking-in" | "done" | "error";

async function submitCheckIn(token: string, conferenceUid: string): Promise<AttendanceRecord> {
  const pending = getPendingCheckIn();
  const result = pending
    ? await secureCheckIn(token, {
        conferenceUid,
        latitude: pending.latitude,
        longitude: pending.longitude,
        photo: { uri: pending.photoUri, name: "checkin.jpg", type: "image/jpeg" },
      })
    : await checkIn(token, conferenceUid);
  clearPendingCheckIn();
  return result;
}

export function useAttendance(conferenceUid?: string) {
  const { token } = useAuth();
  const [status, setStatus] = useState<AttendanceStatus>("checking-in");
  const [markedOn, setMarkedOn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const errorText = (err: unknown) =>
    err instanceof ApiError ? err.message : "Couldn't mark your attendance.";

  // A geofenced session rejects a check-in from outside the venue radius
  // ("...Move within N m to check in."). GPS can drift between the Secure
  // Check-In pre-check and this final write, so surface it as a popup here too.
  const alertIfOutsideGeofence = (err: unknown) => {
    if (err instanceof ApiError && /move within/i.test(err.message)) {
      Alert.alert("You're too far from the venue", err.message);
    }
  };

  useEffect(() => {
    if (!token || !conferenceUid) return;
    let ignore = false;
    submitCheckIn(token, conferenceUid)
      .then((result) => {
        if (ignore) return;
        setMarkedOn(result.markedOn);
        setStatus("done");
      })
      .catch((err) => {
        if (ignore) return;
        alertIfOutsideGeofence(err);
        setError(errorText(err));
        setStatus("error");
      });
    return () => {
      ignore = true;
    };
  }, [token, conferenceUid]);

  const retry = useCallback(async () => {
    if (!token || !conferenceUid) return;
    setStatus("checking-in");
    setError(null);
    try {
      const result = await submitCheckIn(token, conferenceUid);
      setMarkedOn(result.markedOn);
      setStatus("done");
    } catch (err) {
      alertIfOutsideGeofence(err);
      setError(errorText(err));
      setStatus("error");
    }
  }, [token, conferenceUid]);

  const confirmAttendanceRecorded = useCallback(() => {
    setSessionFlowState("ATTENDANCE_RECORDED");
  }, []);

  return {
    status,
    markedOn,
    error,
    retry,
    confirmAttendanceRecorded,
  };
}
