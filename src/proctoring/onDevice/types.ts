/**
 * Trimmed types for the on-device detection engine — scoped to exactly the
 * 4 camera-based violation types SecurityViolationModal/violations.ts
 * already support (NO_FACE, MULTIPLE_FACES, side-look, HEAD_TILT). Adapted
 * from test_proctoring's fuller src/types/proctoring.ts, which also covers
 * object/distance detection this app's UI has no slot for.
 */

export type HeadStatus = "NORMAL" | "LEFT" | "RIGHT" | "UP" | "DOWN" | "TILT";
export type FaceStatus = "NORMAL" | "NO_FACE" | "MULTIPLE_FACES";

export type DetectedEventType = "NO_FACE" | "MULTIPLE_FACES" | "LOOKING_LEFT" | "LOOKING_RIGHT" | "HEAD_TILT";

export type Severity = "INFO" | "WARNING" | "VIOLATION";

export interface FaceFrameResult {
  faceCount: number;
  /** Euler angles (degrees) of the largest detected face, if any. */
  primaryFace?: {
    yawDeg: number;
    pitchDeg: number;
    rollDeg: number;
  };
}

export interface DetectionEvent {
  id: string;
  eventType: DetectedEventType;
  severity: Severity;
}

export interface LiveDetectionState {
  face: FaceStatus;
  head: HeadStatus;
  /** True during the settle-in window after the panel becomes active — see GRACE_PERIOD_MS. */
  graceActive: boolean;
}
