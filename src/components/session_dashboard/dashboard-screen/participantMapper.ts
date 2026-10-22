import { TraineeRow } from "@/api/training";
import { ParticipantItem, ParticipantStatus } from "@/components/session_dashboard/sessionDashboardTypes";

function timeOnly(ts: string | null, prefix: string): string {
  if (!ts) return `${prefix}: --`;
  const d = new Date(ts.replace(" ", "T"));
  if (isNaN(d.getTime())) return `${prefix}: --`;
  return `${prefix}: ${d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true })}`;
}

/** Present or Absent once someone decided; anything else - joined but not checked in ("Pending"),
 *  or a test submitted with no attendance row at all ("Attempted") - isn't marked yet, the same
 *  split the server's own Not Marked count uses. */
function toStatus(raw: string): ParticipantStatus {
  const s = raw.toLowerCase();
  if (s === "present") return "PRESENT";
  if (s === "absent") return "ABSENT";
  return "NOT_MARKED";
}

/** ASSIGNED / FRESH as sent; anything else - UNASSIGNED, or an older server's "NOT ALLOCATED" -
 *  is an unassigned participant. */
function toAudience(raw: string): ParticipantItem["attendeeType"] {
  if (raw === "ASSIGNED" || raw === "FRESH") return raw;
  return "UNASSIGNED";
}

/** `data.trainees` (real backend rows) -> the Participant Master List's row shape. */
export function participantsFromTrainees(trainees: TraineeRow[]): ParticipantItem[] {
  return trainees.map((t) => ({
    id: t.traineeUid,
    name: t.name,
    employeeId: t.employeeId || t.traineeUid,
    phone: t.phone != null ? String(t.phone) : "--",
    attendeeType: toAudience(t.audienceType),
    status: toStatus(t.status),
    stage: t.stage ?? "Not Started",
    stageModules: t.stageModules ?? [],
    inTime: timeOnly(t.markedOn, "IN"),
    outTime: timeOnly(t.checkOutTime, "OUT"),
    score: t.score,
    scorePassed: t.score ? (t.scorePassed ?? null) : null,
    // Only carry proctoring data when the trainee is actually locked - the
    // Participant Master List keys the LOCKED pill / unlock control off its
    // presence.
    proctoring: t.isLocked
      ? {
          flags: t.proctoringStrikes,
          maxFlags: t.proctoringMaxStrikes,
          logs: t.proctoringLogs,
          unlocksUsed: t.proctoringUnlocks ?? 0,
          maxUnlocks: t.proctoringMaxUnlocks ?? 2,
        }
      : undefined,
    // Shown beside the Controls buttons whether or not they're locked now (user, 2026-10-22).
    unlocks: { used: t.proctoringUnlocks ?? 0, max: t.proctoringMaxUnlocks ?? 2 },
  }));
}
