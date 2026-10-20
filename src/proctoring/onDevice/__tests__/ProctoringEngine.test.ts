import { expect, test } from "@jest/globals";

import { ProctoringEngine } from "../ProctoringEngine";
import type { DetectedEventType, DetectionEvent, FaceFrameResult } from "../types";

const STRAIGHT: FaceFrameResult = { faceCount: 1, primaryFace: { yawDeg: 0, pitchDeg: 0, rollDeg: 0 } };
const SIDE_LOOK: FaceFrameResult = { faceCount: 1, primaryFace: { yawDeg: 30, pitchDeg: 0, rollDeg: 0 } };
const FRAME_MS = 100;

function setup() {
  const engine = new ProctoringEngine();
  const strikes: DetectionEvent[] = [];
  engine.onEvent((event) => strikes.push(event));
  /** Feeds the same camera frame every FRAME_MS from `fromMs` to `toMs` inclusive. */
  const hold = (frame: FaceFrameResult, fromMs: number, toMs: number) => {
    for (let t = fromMs; t <= toMs; t += FRAME_MS) engine.ingestFace(frame, t);
  };
  return { engine, strikes, hold };
}

test("the camera panel turns red at once, but the strike only fires if the side-look lasts 2 seconds", () => {
  const { engine, strikes, hold } = setup();

  engine.ingestFace(SIDE_LOOK, 0);
  expect(engine.getLiveState().head).toBe("LEFT"); // red panel: "SIDE-LOOK DETECTED"
  expect(strikes).toEqual([]);

  hold(SIDE_LOOK, 100, 1900);
  expect(strikes).toEqual([]);

  engine.ingestFace(SIDE_LOOK, 2000);
  expect(strikes).toEqual([expect.objectContaining({ eventType: "LOOKING_LEFT", severity: "VIOLATION" })]);
});

test("looking back in time cancels it, and turning away again starts a fresh 2 seconds", () => {
  const { engine, strikes, hold } = setup();

  hold(SIDE_LOOK, 0, 1500);
  engine.ingestFace(STRAIGHT, 1600);
  expect(engine.getLiveState().head).toBe("NORMAL"); // panel back to normal
  hold(SIDE_LOOK, 1700, 3600);
  expect(strikes).toEqual([]); // 1.9 s into the second look

  engine.ingestFace(SIDE_LOOK, 3700);
  expect(strikes).toHaveLength(1);
});

test.each<[string, FaceFrameResult, DetectedEventType]>([
  ["no face", { faceCount: 0 }, "NO_FACE"],
  ["a second person", { faceCount: 2, primaryFace: STRAIGHT.primaryFace }, "MULTIPLE_FACES"],
  ["looking right", { faceCount: 1, primaryFace: { yawDeg: -30, pitchDeg: 0, rollDeg: 0 } }, "LOOKING_RIGHT"],
  ["head tilted", { faceCount: 1, primaryFace: { yawDeg: 0, pitchDeg: 0, rollDeg: 25 } }, "HEAD_TILT"],
])("%s follows the same 2-second rule", (_label, frame, eventType) => {
  const { strikes, hold } = setup();

  hold(frame, 0, 1900);
  expect(strikes).toEqual([]);

  hold(frame, 2000, 2000);
  expect(strikes).toEqual([expect.objectContaining({ eventType, severity: "VIOLATION" })]);
});

test("one strike per occurrence; after the popup closes, still looking away needs another full 2 seconds", () => {
  const { engine, strikes, hold } = setup();

  hold(SIDE_LOOK, 0, 3000);
  expect(strikes).toHaveLength(1); // no repeat strikes while the same look continues

  engine.rearmAll(3000); // the strike popup was closed and the camera resumed
  hold(SIDE_LOOK, 3100, 4900);
  expect(strikes).toHaveLength(1);

  engine.ingestFace(SIDE_LOOK, 5000);
  expect(strikes).toHaveLength(2);
});
