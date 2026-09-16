import type { DetectedEventType } from "./types";

/**
 * Head-pose thresholds, in degrees, from ML Kit's yaw/pitch/roll angles —
 * same values as test_proctoring's HEAD_POSE_CONFIG.
 */
export const HEAD_POSE_CONFIG = {
  yawLeftDeg: 20, // yawAngle > +20 => looking toward device's left
  yawRightDeg: -20,
  pitchUpDeg: 15,
  pitchDownDeg: -15,
  rollTiltDeg: 18,
};

/** Smallest face size (as a ratio of frame width) ML Kit will still report. */
export const MIN_FACE_SIZE = 0.12;

export interface TemporalRule {
  warningMs: number | null;
  violationMs: number | null;
  /** Minimum time a detection must be *absent* before it's considered ended, to avoid a single missed frame fragmenting one occurrence into many. */
  gapToleranceMs: number;
}

/**
 * How long a detection must persist before it escalates to WARNING then
 * VIOLATION. Production-sensible defaults (not test_proctoring's later
 * "instant" tuning, which was for rapid manual testing during development).
 */
export const TEMPORAL_RULES: Record<DetectedEventType, TemporalRule> = {
  // gapToleranceMs is intentionally generous (not near-zero, and not
  // infinite): once a detection starts accumulating, a brief jitter/misread
  // frame no longer throws the progress away, so natural head drift can't
  // keep resetting the timer back to 0. It still eventually treats a
  // genuine, sustained return to normal as "ended" (here: ~2s of clean
  // frames) — a truly infinite tolerance would let one glance days later
  // reuse a years-old start time and look like an instant, already-overdue
  // violation, which is worse than the jitter problem it would "fix".
  // warningMs: null disables the soft (non-strike) popup entirely — every
  // detection now fires the real SECURITY VIOLATION DETECTED strike modal
  // immediately (violationMs: 0) the first frame the camera catches it,
  // rather than waiting for it to persist.
  NO_FACE: { warningMs: null, violationMs: 0, gapToleranceMs: 0 },
  MULTIPLE_FACES: { warningMs: null, violationMs: 0, gapToleranceMs: 0 },
  LOOKING_LEFT: { warningMs: null, violationMs: 0, gapToleranceMs: 0 },
  LOOKING_RIGHT: { warningMs: null, violationMs: 0, gapToleranceMs: 0 },
  HEAD_TILT: { warningMs: null, violationMs: 0, gapToleranceMs: 0 },
};

/** Once a detection ends, how long before a new occurrence of the same type may start. */
export const COOLDOWN_MS = 1000;

/** No violation fires for this long after the panel becomes active, so the candidate has time to get into frame. */
export const GRACE_PERIOD_MS = 2000;
