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
 * How long a detection must hold before it counts as a strike. The camera panel turns red with
 * the reason (e.g. "SIDE-LOOK DETECTED") the moment it sees the problem; the SECURITY VIOLATION
 * DETECTED strike only fires if the candidate is still in that position this much later.
 */
export const STRIKE_AFTER_MS = 2000;

/**
 * Per-detection timing. warningMs: null - there is no separate soft (non-strike) popup; the red
 * camera panel is the warning. gapToleranceMs: 0 - returning to a normal position ends the
 * occurrence, so the 2 seconds start again from zero the next time.
 */
export const TEMPORAL_RULES: Record<DetectedEventType, TemporalRule> = {
  NO_FACE: { warningMs: null, violationMs: STRIKE_AFTER_MS, gapToleranceMs: 0 },
  MULTIPLE_FACES: { warningMs: null, violationMs: STRIKE_AFTER_MS, gapToleranceMs: 0 },
  LOOKING_LEFT: { warningMs: null, violationMs: STRIKE_AFTER_MS, gapToleranceMs: 0 },
  LOOKING_RIGHT: { warningMs: null, violationMs: STRIKE_AFTER_MS, gapToleranceMs: 0 },
  HEAD_TILT: { warningMs: null, violationMs: STRIKE_AFTER_MS, gapToleranceMs: 0 },
};

/** Once a detection that caused a strike ends, how long before a new occurrence of the same type may start. */
export const COOLDOWN_MS = 1000;

/** No violation fires for this long after the panel becomes active, so the candidate has time to get into frame. */
export const GRACE_PERIOD_MS = 2000;
