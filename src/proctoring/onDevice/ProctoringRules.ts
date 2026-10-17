import { HEAD_POSE_CONFIG } from "./config";
import type { DetectedEventType, FaceStatus, HeadStatus } from "./types";

/**
 * Pure classification helpers, adapted from test_proctoring's
 * src/proctoring/ProctoringRules.ts and src/ai/face/FaceAnalyzer.ts.
 */

export function faceStatusFromCount(faceCount: number): FaceStatus {
  if (faceCount === 0) return "NO_FACE";
  if (faceCount >= 2) return "MULTIPLE_FACES";
  return "NORMAL";
}

export function classifyHeadPose(yawDeg: number, pitchDeg: number, rollDeg: number): HeadStatus {
  // yawDeg: positive = face turned toward the camera's left (subject's right).
  if (yawDeg > HEAD_POSE_CONFIG.yawLeftDeg) return "LEFT";
  if (yawDeg < HEAD_POSE_CONFIG.yawRightDeg) return "RIGHT";
  if (pitchDeg > HEAD_POSE_CONFIG.pitchUpDeg) return "UP";
  if (pitchDeg < HEAD_POSE_CONFIG.pitchDownDeg) return "DOWN";
  if (Math.abs(rollDeg) > HEAD_POSE_CONFIG.rollTiltDeg) return "TILT";
  return "NORMAL";
}

/** UP/DOWN intentionally map to null — no matching SecurityViolationType exists in this app's violation set. */
export function headEventType(status: HeadStatus): DetectedEventType | null {
  switch (status) {
    case "LEFT":
      return "LOOKING_LEFT";
    case "RIGHT":
      return "LOOKING_RIGHT";
    case "TILT":
      return "HEAD_TILT";
    default:
      return null;
  }
}
