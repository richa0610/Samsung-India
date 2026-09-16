import { TraineeRow } from "@/api/training";
import { ParticipantItem, ParticipantStatus } from "@/components/session_dashboard/sessionDashboardTypes";

function timeOnly(ts: string | null, prefix: string): string {
  if (!ts) return `${prefix}: --`;
  const d = new Date(ts.replace(" ", "T"));
  if (isNaN(d.getTime())) return `${prefix}: --`;
  return `${prefix}: ${d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true })}`;
}

function toStatus(raw: string): ParticipantStatus {
  const s = raw.toLowerCase();
  if (s === "present") return "PRESENT";
  if (s === "pending") return "PENDING";
  return "ABSENT";
}

/** `data.trainees` (real backend rows) -> the Participant Master List's row shape. */
export function participantsFromTrainees(trainees: TraineeRow[]): ParticipantItem[] {
  return trainees.map((t) => ({
    id: t.traineeUid,
    name: t.name,
    employeeId: t.employeeId || t.traineeUid,
    phone: t.phone != null ? String(t.phone) : "--",
    attendeeType: t.audienceType === "ASSIGNED" ? "ASSIGNED" : "NOT ALLOCATED",
    status: toStatus(t.status),
    inTime: timeOnly(t.markedOn, "IN"),
    outTime: timeOnly(t.checkOutTime, "OUT"),
    // Only carry proctoring data when the trainee is actually locked - the
    // Participant Master List keys the LOCKED pill / unlock control off its
    // presence.
    proctoring: t.isLocked
      ? { flags: t.proctoringStrikes, maxFlags: t.proctoringMaxStrikes, logs: t.proctoringLogs }
      : undefined,
  }));
}
