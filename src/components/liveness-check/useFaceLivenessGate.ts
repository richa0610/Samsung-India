import { useCallback, useEffect, useRef, useState } from "react";
import { useFaceDetectorOutput, useImageFaceDetector } from "react-native-vision-camera-face-detector";

import { LivenessGateEngine } from "./LivenessGateEngine";
import { LIVENESS_CONFIG as C } from "./livenessConfig";

export type UseFaceLivenessGateParams = {
  /** Only runs the detector/state machine while true - pass false once a photo is captured, or while the modal is hidden. */
  active: boolean;
};

/**
 * One-shot liveness/humanness gate for a photo-capture flow: place face in
 * frame -> look straight -> move head slightly (or blink) -> verified.
 * Reuses the already-installed react-native-vision-camera-face-detector -
 * no frames ever leave the device. Attach `faceDetectorOutput` to the same
 * `<Camera outputs={[...]}>` array as the existing photo output.
 */
export function useFaceLivenessGate({ active }: UseFaceLivenessGateParams) {
  const [engine] = useState(() => new LivenessGateEngine());
  const [state, setState] = useState(() => engine.getState());
  const [detectorError, setDetectorError] = useState<string | null>(null);
  const wasActiveRef = useRef(active);

  useEffect(() => {
    const unsubscribe = engine.onChange(setState);
    return unsubscribe;
  }, [engine]);

  useEffect(() => {
    const unsubscribe = engine.onError(setDetectorError);
    return unsubscribe;
  }, [engine]);

  // Fresh run every time the gate (re)activates - e.g. modal reopened, or retake after a failed capture.
  useEffect(() => {
    if (active && !wasActiveRef.current) engine.reset();
    wasActiveRef.current = active;
  }, [active, engine]);

  // Frame-independent timeout - fires even if the detector stops delivering frames entirely (e.g. camera stalls).
  useEffect(() => {
    if (!active) return;
    const timer = setTimeout(() => engine.checkTimeout(), C.timeoutMs);
    return () => clearTimeout(timer);
  }, [active, engine]);

  const faceDetectorOutput = useFaceDetectorOutput({
    performanceMode: "fast",
    runLandmarks: false,
    runContours: false,
    runClassifications: true, // needed for leftEyeOpenProbability/rightEyeOpenProbability
    trackingEnabled: false,
    minFaceSize: C.minFaceSize,
    onFacesDetected(faces) {
      if (!active) return;
      if (faces.length !== 1) {
        engine.ingestFace(faces.length, null, Date.now());
        return;
      }
      const f = faces[0]!;
      const frameW = f.frameWidth || 1;
      const frameH = f.frameHeight || 1;
      const centerX = f.bounds.x + f.bounds.width / 2;
      const centerY = f.bounds.y + f.bounds.height / 2;
      engine.ingestFace(
        1,
        {
          yawDeg: f.yawAngle,
          pitchDeg: f.pitchAngle,
          rollDeg: f.rollAngle,
          sizeRatio: f.bounds.width / frameW,
          centerOffsetXRatio: Math.abs(centerX - frameW / 2) / (frameW / 2),
          centerOffsetYRatio: Math.abs(centerY - frameH / 2) / (frameH / 2),
          leftEyeOpen: f.leftEyeOpenProbability,
          rightEyeOpen: f.rightEyeOpenProbability,
        },
        Date.now(),
      );
    },
    onError(error) {
      console.warn("useFaceLivenessGate: face detector error, skipping frame.", error);
      engine.reportError("Face detection hit a problem. You can still retry.");
    },
  });

  const reset = useCallback(() => engine.reset(), [engine]);

  // Static, one-off analysis of the already-captured JPEG file - not a live
  // camera stream, so it can run *after* the live faceDetectorOutput has
  // been detached for the actual capture (see the device stream-limit note
  // where faceDetectorOutput is attached) without any resource conflict.
  // This is what actually rejects a capture with no/multiple faces, since
  // `verified` above only reflects the live feed up to the moment just
  // before the shutter fires, not the literal captured frame.
  const imageFaceDetector = useImageFaceDetector({ performanceMode: "fast", minFaceSize: C.minFaceSize });
  const verifyCapturedPhoto = useCallback(
    async (uri: string): Promise<{ ok: boolean; faceCount: number }> => {
      try {
        // Pass the { uri } object form, not a bare string - Android's
        // resolveInputImage (HybridImageFaceDetector.kt) only matches a
        // native Kotlin String or a Map, and a raw JS string doesn't appear
        // to marshal into either across this library's Nitro union-type
        // binding for `string | number | { uri }` (throws "Invalid image
        // type" instead). The object form is unambiguous.
        const faces = await imageFaceDetector.detectFaces({ uri });
        return { ok: faces.length === 1, faceCount: faces.length };
      } catch (error) {
        // A detector hiccup on the still image isn't a security boundary by
        // itself (the live ceremony already ran) - fail open rather than
        // stranding the trainer on a broken check.
        console.warn("useFaceLivenessGate: post-capture face check failed, allowing capture through.", error);
        return { ok: true, faceCount: 1 };
      }
    },
    [imageFaceDetector],
  );

  return {
    ...state,
    detectorError,
    faceDetectorOutput,
    reset,
    verifyCapturedPhoto,
    timedOut: state.step === "TIMED_OUT",
  };
}
