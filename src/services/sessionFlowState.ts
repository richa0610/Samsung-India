/**
 * Where the trainee is in a session's check-in flow (joined -> secure check-in -> attendance
 * recorded), which modules they have left, and the check-in photo + location waiting to be
 * submitted. Client-side navigation state only: held in memory for this app run, never sent
 * anywhere by itself. Keyed by conference (and trainee) when given, otherwise one app-wide value.
 */
import type { AttendanceState, SessionFlowState } from "@/api/session";

let _flowState: SessionFlowState = "JOINED";
let _attendanceRecorded = false;
const _flowStateByKey: Record<string, SessionFlowState> = {};
const _attendanceRecordedByKey: Record<string, boolean> = {};

const _scopedKey = (conferenceUid?: string, traineeUid?: string): string | null => {
  if (!conferenceUid) return null;
  return traineeUid ? `${conferenceUid}:${traineeUid}` : conferenceUid;
};

export function getSessionFlowState(conferenceUid?: string, traineeUid?: string): SessionFlowState {
  const key = _scopedKey(conferenceUid, traineeUid);
  if (key) {
    if (_attendanceRecordedByKey[key]) {
      return "ATTENDANCE_RECORDED";
    }
    return _flowStateByKey[key] ?? "JOINED";
  }
  if (_attendanceRecorded) {
    return "ATTENDANCE_RECORDED";
  }
  return _flowState;
}

export function setSessionFlowState(
  state: SessionFlowState,
  conferenceUid?: string,
  traineeUid?: string,
) {
  const key = _scopedKey(conferenceUid, traineeUid);
  if (key) {
    _flowStateByKey[key] = state;
    if (state === "ATTENDANCE_RECORDED") {
      _attendanceRecordedByKey[key] = true;
    } else if (state === "JOINED" || state === "SECURE_CHECKIN") {
      _attendanceRecordedByKey[key] = false;
    }
    return;
  }

  _flowState = state;
  if (state === "ATTENDANCE_RECORDED") {
    _attendanceRecorded = true;
  } else if (state === "JOINED" || state === "SECURE_CHECKIN") {
    _attendanceRecorded = false;
  }
}

export function setAttendanceState(
  state: AttendanceState,
  conferenceUid?: string,
  traineeUid?: string,
) {
  setSessionFlowState(state, conferenceUid, traineeUid);
}

const _leftModulesByKey: Record<string, boolean> = {};

export function markModuleLeft(conferenceUid: string, moduleKey: string, traineeUid?: string) {
  const key = `${conferenceUid}:${traineeUid || "default"}:${moduleKey}`;
  _leftModulesByKey[key] = true;
}

export function isModuleLeft(conferenceUid: string, moduleKey: string, traineeUid?: string): boolean {
  const key = `${conferenceUid}:${traineeUid || "default"}:${moduleKey}`;
  return Boolean(_leftModulesByKey[key]);
}

// Location + face photo captured on the Secure Check-In screen, held here
// until the "Mark Attendance" step submits them to /attendance/check-in/secure
// (a geofenced session needs the coordinates at submit time; the plain
// /attendance/check-in has none and is refused by the backend).
export type PendingCheckIn = { latitude: number; longitude: number; photoUri: string };
let _pendingCheckIn: PendingCheckIn | null = null;

export function setPendingCheckIn(pending: PendingCheckIn) {
  _pendingCheckIn = pending;
}
export function getPendingCheckIn(): PendingCheckIn | null {
  return _pendingCheckIn;
}
export function clearPendingCheckIn() {
  _pendingCheckIn = null;
}
