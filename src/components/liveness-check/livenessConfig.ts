/** Tunable thresholds for useFaceLivenessGate. Degrees/ratios, not shared with src/proctoring/onDevice's own (differently-tuned) constants. */
export const LIVENESS_CONFIG = {
  /** Face bounding-box width must be within this fraction of the frame width - too small = too far away, too big = too close. */
  minFaceSizeRatio: 0.28,
  maxFaceSizeRatio: 0.85,
  /** Face center must fall within this fraction of the frame's half-width/height from the true center. */
  maxCenterOffsetRatioX: 0.22,
  maxCenterOffsetRatioY: 0.28,

  /** "Look at the camera" - max head-pose deviation still considered straight-on. */
  maxYawDeg: 12,
  maxPitchDeg: 12,
  maxRollDeg: 14,

  /** "Move your head slightly" - yaw must drift at least this far from the straight-on baseline. */
  moveYawDeltaDeg: 8,
  /** Eye-open probability (runClassifications) below this counts as "closed", above this as "open" - a close-then-open cycle counts as a blink. */
  eyeClosedThreshold: 0.4,
  eyeOpenThreshold: 0.6,

  /** How long a qualifying read must hold continuously before the step advances - filters single-frame flicker. */
  holdMs: 350,
  /** Absent detections must persist this long before they end a step (a single dropped frame shouldn't reset progress). */
  gapToleranceMs: 250,

  /** Give up and show a retry prompt if verification hasn't completed within this long. */
  timeoutMs: 30_000,

  minFaceSize: 0.15,
} as const;
