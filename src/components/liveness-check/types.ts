/**
 * One-shot, client-side "is this a real person looking at the camera right
 * now" gate — distinct from src/proctoring/onDevice, which continuously
 * monitors an already-verified session for violations. This instead walks a
 * single linear sequence once (frame -> straight -> move/blink -> verified)
 * before a capture button unlocks, then stops.
 */
export type LivenessStep =
  | "NO_FACE"
  | "MULTIPLE_FACES"
  | "POSITIONING"
  | "LOOK_STRAIGHT"
  | "MOVE_HEAD"
  | "VERIFIED"
  | "TIMED_OUT";

export interface LivenessGateState {
  step: LivenessStep;
  instruction: string;
  verified: boolean;
  /** True once a detector frame has arrived at least once (distinguishes "still starting up" from a genuine NO_FACE read). */
  hasDetected: boolean;
}

/** A single frame's face reading, already reduced to what the gate needs. */
export interface LivenessFaceReading {
  yawDeg: number;
  pitchDeg: number;
  rollDeg: number;
  sizeRatio: number;
  centerOffsetXRatio: number;
  centerOffsetYRatio: number;
  leftEyeOpen?: number;
  rightEyeOpen?: number;
}

export type LivenessStateListener = (state: LivenessGateState) => void;
export type LivenessErrorListener = (message: string | null) => void;
