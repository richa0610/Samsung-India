import { LIVENESS_CONFIG as C } from "./livenessConfig";
import type { LivenessErrorListener, LivenessFaceReading, LivenessGateState, LivenessStateListener, LivenessStep } from "./types";

const INSTRUCTIONS: Record<LivenessStep, string> = {
  NO_FACE: "Place your face inside the frame",
  MULTIPLE_FACES: "Only one face allowed in the frame",
  POSITIONING: "Place your face inside the frame",
  LOOK_STRAIGHT: "Look at the camera",
  MOVE_HEAD: "Move your head slightly",
  VERIFIED: "Human verification successful",
  TIMED_OUT: "Taking too long — reposition your face and try again",
};

const NEGATIVE_STEPS = new Set<LivenessStep>(["NO_FACE", "MULTIPLE_FACES"]);

/** Which step a single frame's reading satisfies on its own, ignoring hold-time/history. */
function classifyFrame(faceCount: number, face: LivenessFaceReading | null): LivenessStep {
  if (faceCount === 0 || !face) return "NO_FACE";
  if (faceCount > 1) return "MULTIPLE_FACES";

  const wellSized = face.sizeRatio >= C.minFaceSizeRatio && face.sizeRatio <= C.maxFaceSizeRatio;
  const centered = face.centerOffsetXRatio <= C.maxCenterOffsetRatioX && face.centerOffsetYRatio <= C.maxCenterOffsetRatioY;
  if (!wellSized || !centered) return "POSITIONING";

  const straight = Math.abs(face.yawDeg) <= C.maxYawDeg && Math.abs(face.pitchDeg) <= C.maxPitchDeg && Math.abs(face.rollDeg) <= C.maxRollDeg;
  if (!straight) return "LOOK_STRAIGHT";

  return "MOVE_HEAD";
}

/**
 * Minimal one-shot liveness/humanness state machine: place face in frame ->
 * look straight -> move head slightly (or blink) -> verified. Has no
 * dependency on React or the camera - fed plain per-frame readings, and
 * emits plain state objects to subscribers. Mirrors the
 * src/proctoring/onDevice/ProctoringEngine split (engine vs. the React hook
 * that wires it to a camera), but runs once per activation instead of
 * continuously monitoring.
 *
 * `verified` is deliberately NOT sticky forever once reached: it reflects
 * whether a single real face is in frame *right now*. Once the one-time
 * ceremony (straight -> move/blink) has been done once this activation
 * (`provenHuman`), losing and regaining the face just re-checks presence -
 * it doesn't force the whole ceremony again. This matters because the
 * capture button is gated on `verified`, not on "was ever verified" - a
 * trainer who passes the check and then points the camera elsewhere before
 * tapping Capture must have the button disable again, not stay unlocked
 * from a stale pass.
 */
export class LivenessGateEngine {
  private step: LivenessStep = "NO_FACE";
  private pendingStep: LivenessStep | null = null;
  private pendingSince = 0;
  private badSince: number | null = null;
  private baselineYaw: number | null = null;
  private eyesWereClosed = false;
  private verified = false;
  private provenHuman = false;
  private hasDetected = false;

  private listeners = new Set<LivenessStateListener>();
  private errorListeners = new Set<LivenessErrorListener>();

  onChange(listener: LivenessStateListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onError(listener: LivenessErrorListener): () => void {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  getState(): LivenessGateState {
    return { step: this.step, instruction: INSTRUCTIONS[this.step], verified: this.verified, hasDetected: this.hasDetected };
  }

  reportError(message: string) {
    for (const l of this.errorListeners) l(message);
  }

  reset() {
    this.step = "NO_FACE";
    this.pendingStep = null;
    this.pendingSince = 0;
    this.badSince = null;
    this.baselineYaw = null;
    this.eyesWereClosed = false;
    this.verified = false;
    this.provenHuman = false;
    this.hasDetected = false;
    for (const l of this.errorListeners) l(null);
    this.publish();
  }

  /** Called once per detector timeout window - a no-op once already proven human (a momentary lost-presence blip shouldn't force the whole ceremony to restart). */
  checkTimeout() {
    if (this.verified || this.provenHuman) return;
    this.commit("TIMED_OUT");
  }

  /** Ingests one frame's face-detection result. */
  ingestFace(faceCount: number, face: LivenessFaceReading | null, nowMs: number) {
    if (this.provenHuman) {
      this.ingestPostProof(faceCount, face, nowMs);
      return;
    }
    if (this.verified) return;
    const raw = classifyFrame(faceCount, face);

    if (NEGATIVE_STEPS.has(raw)) {
      this.pendingStep = null;
      if (this.badSince === null) this.badSince = nowMs;
      // A single dropped/blurry frame shouldn't instantly discard progress -
      // only commit the regression once it's persisted a little.
      if (this.step !== raw && nowMs - this.badSince >= C.gapToleranceMs) {
        this.baselineYaw = null;
        this.eyesWereClosed = false;
        this.commit(raw);
      }
      return;
    }
    this.badSince = null;

    if (raw === "MOVE_HEAD" && this.step === "MOVE_HEAD") {
      if (face) {
        if (this.baselineYaw === null) this.baselineYaw = face.yawDeg;
        const turned = Math.abs(face.yawDeg - this.baselineYaw) >= C.moveYawDeltaDeg;

        let blinked = false;
        if (typeof face.leftEyeOpen === "number" && typeof face.rightEyeOpen === "number") {
          const avgOpen = (face.leftEyeOpen + face.rightEyeOpen) / 2;
          if (avgOpen <= C.eyeClosedThreshold) this.eyesWereClosed = true;
          else if (avgOpen >= C.eyeOpenThreshold && this.eyesWereClosed) blinked = true;
        }

        if (turned || blinked) this.commit("VERIFIED");
      }
      return;
    }

    if (raw === this.step) return; // already-committed step, nothing to do

    // Moving to a new (non-negative) step: debounce briefly so a single
    // lucky/unlucky frame can't flip the instruction back and forth.
    if (this.pendingStep !== raw) {
      this.pendingStep = raw;
      this.pendingSince = nowMs;
      return;
    }
    if (nowMs - this.pendingSince >= C.holdMs) {
      if (raw === "MOVE_HEAD" && face) this.baselineYaw = face.yawDeg;
      this.commit(raw);
    }
  }

  /**
   * Lightweight continuous presence check once the one-time ceremony has
   * already been proven this activation: no face / multiple faces flips
   * `verified` back off (debounced the same way as the initial ceremony, so
   * a single dropped frame doesn't flicker it), and a single face - in any
   * pose, no need to look-straight/move again - flips it back on.
   */
  private ingestPostProof(faceCount: number, face: LivenessFaceReading | null, nowMs: number) {
    const raw = classifyFrame(faceCount, face);

    if (NEGATIVE_STEPS.has(raw)) {
      if (this.badSince === null) this.badSince = nowMs;
      if (this.verified && nowMs - this.badSince >= C.gapToleranceMs) this.setLive(raw, false);
      return;
    }
    this.badSince = null;
    if (!this.verified) this.setLive("VERIFIED", true);
  }

  private setLive(step: LivenessStep, verified: boolean) {
    if (this.step === step && this.verified === verified) return;
    this.step = step;
    this.verified = verified;
    this.hasDetected = true;
    this.publish();
  }

  private commit(step: LivenessStep) {
    if (this.verified) return; // frozen once verified, until reset()
    if (step === "VERIFIED") {
      this.verified = true;
      this.provenHuman = true;
    }
    this.step = step;
    this.pendingStep = null;
    this.hasDetected = true;
    this.publish();
  }

  private publish() {
    const state = this.getState();
    for (const l of this.listeners) l(state);
  }
}
