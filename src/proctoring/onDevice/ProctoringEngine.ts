import { COOLDOWN_MS, GRACE_PERIOD_MS, TEMPORAL_RULES } from "./config";
import { classifyHeadPose, faceStatusFromCount, headEventType } from "./ProctoringRules";
import type { DetectedEventType, DetectionEvent, FaceFrameResult, HeadStatus, LiveDetectionState, Severity } from "./types";

const SEVERITY_RANK: Record<Severity, number> = { INFO: 0, WARNING: 1, VIOLATION: 2 };

const ALL_EVENT_TYPES: DetectedEventType[] = ["NO_FACE", "MULTIPLE_FACES", "LOOKING_LEFT", "LOOKING_RIGHT", "HEAD_TILT"];

interface ActiveDetectionState {
  startedAt: number;
  lastDetectedAt: number;
  emittedSeverity: Severity | null;
  eventId: string | null;
}

let idCounter = 0;
function generateId(): string {
  idCounter += 1;
  return `ondevice-${Date.now()}-${idCounter}`;
}

export type DetectionEventListener = (event: DetectionEvent) => void;
export type LiveStateListener = (state: LiveDetectionState) => void;

/**
 * Minimal on-device face/head-pose detection state machine, trimmed from
 * test_proctoring's src/proctoring/ProctoringEngine.ts down to exactly the
 * event types this app's SecurityViolationModal/violations.ts support. Same
 * START -> CONTINUE -> END temporal state machine as the prototype: a
 * detection must persist past TEMPORAL_RULES[type].violationMs before it
 * counts, and won't re-fire for the same continuous occurrence once it has
 * (see `rearm`/`rearmAll` for why the panel needs to override that).
 *
 * Has no dependency on the camera or React — it's fed plain per-frame
 * FaceFrameResult objects and emits plain DetectionEvent objects.
 */
export class ProctoringEngine {
  private active = new Map<DetectedEventType, ActiveDetectionState>();
  private cooldownUntil = new Map<DetectedEventType, number>();
  private listeners = new Set<DetectionEventListener>();
  private liveListeners = new Set<LiveStateListener>();
  private graceUntilMs = 0;

  private live: LiveDetectionState = { face: "NORMAL", head: "NORMAL", graceActive: false };

  onEvent(listener: DetectionEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onLiveState(listener: LiveStateListener): () => void {
    this.liveListeners.add(listener);
    return () => this.liveListeners.delete(listener);
  }

  getLiveState(): LiveDetectionState {
    return this.live;
  }

  /** Ingests one frame's face-detection result. */
  ingestFace(result: FaceFrameResult, nowMs: number) {
    const faceStatus = faceStatusFromCount(result.faceCount);
    let headStatus: HeadStatus = "NORMAL";

    const present = new Set<DetectedEventType>();
    if (faceStatus !== "NORMAL") present.add(faceStatus);

    if (result.primaryFace) {
      headStatus = classifyHeadPose(result.primaryFace.yawDeg, result.primaryFace.pitchDeg, result.primaryFace.rollDeg);
      const headEvt = headEventType(headStatus);
      if (headEvt) present.add(headEvt);
    }

    const graceActive = nowMs < this.graceUntilMs;
    if (!graceActive) {
      this.reconcile(present, nowMs);
    }

    this.live = { face: faceStatus, head: headStatus, graceActive };
    this.publishLive();
  }

  private reconcile(present: Set<DetectedEventType>, nowMs: number) {
    for (const eventType of ALL_EVENT_TYPES) {
      const rule = TEMPORAL_RULES[eventType];
      const isPresent = present.has(eventType);
      const existing = this.active.get(eventType);

      if (isPresent) {
        if (!existing) {
          const cooldownUntil = this.cooldownUntil.get(eventType) ?? 0;
          if (nowMs < cooldownUntil) continue; // still cooling down from the last occurrence
          this.active.set(eventType, { startedAt: nowMs, lastDetectedAt: nowMs, emittedSeverity: null, eventId: null });
        } else {
          existing.lastDetectedAt = nowMs;
        }
      }

      const state = this.active.get(eventType);
      if (!state) continue;

      const gapMs = nowMs - state.lastDetectedAt;
      const hasEnded = !isPresent && gapMs > rule.gapToleranceMs;

      if (!hasEnded) {
        const duration = state.lastDetectedAt - state.startedAt;
        let target: Severity | null = null;
        if (rule.violationMs != null && duration >= rule.violationMs) target = "VIOLATION";
        else if (rule.warningMs != null && duration >= rule.warningMs) target = "WARNING";

        if (target && (state.emittedSeverity == null || SEVERITY_RANK[target] > SEVERITY_RANK[state.emittedSeverity])) {
          state.emittedSeverity = target;
          const id = state.eventId ?? generateId();
          state.eventId = id;
          this.publishEvent({ id, eventType, severity: target });
        }
      } else {
        this.active.delete(eventType);
        this.cooldownUntil.set(eventType, nowMs + COOLDOWN_MS);
      }
    }
  }

  private publishEvent(event: DetectionEvent) {
    for (const l of this.listeners) l(event);
  }

  private publishLive() {
    for (const l of this.liveListeners) l(this.live);
  }

  reset(nowMs: number = Date.now()) {
    this.active.clear();
    this.cooldownUntil.clear();
    this.graceUntilMs = nowMs + GRACE_PERIOD_MS;
    this.live = { ...this.live, graceActive: true };
    this.publishLive();
  }

  /**
   * Re-checks one still-ongoing detection immediately instead of waiting for
   * it to naturally end and restart. A detection only fires once per
   * continuous occurrence — if the underlying condition (e.g. a second
   * person) never actually left frame, the engine would otherwise stay
   * silent about it. Also clears any leftover cooldown, in case the
   * detection *did* independently end (a brief real-world flicker) while the
   * caller wasn't watching — see test_proctoring's ProctoringEngine.rearm
   * for the full incident this was written to fix.
   */
  rearm(eventType: DetectedEventType, nowMs: number = Date.now()) {
    this.cooldownUntil.delete(eventType);
    const state = this.active.get(eventType);
    if (!state) return;
    state.emittedSeverity = null;
    state.eventId = null;
    state.startedAt = nowMs;
    state.lastDetectedAt = nowMs;
  }

  /** Re-arms every currently-active detection type — used when resuming from a pause, since the caller doesn't know which type (if any) caused it. */
  rearmAll(nowMs: number = Date.now()) {
    for (const eventType of this.active.keys()) this.rearm(eventType, nowMs);
  }
}
