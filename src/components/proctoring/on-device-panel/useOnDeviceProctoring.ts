import { Ionicons } from "@expo/vector-icons";
import { useEffect, useRef, useState } from "react";
import { useCameraDevice, useCameraPermission } from "react-native-vision-camera";
import { useFaceDetectorOutput } from "react-native-vision-camera-face-detector";

import { ProctoringEngine } from "@/proctoring/onDevice/ProctoringEngine";
import { MIN_FACE_SIZE } from "@/proctoring/onDevice/config";
import type { DetectedEventType, DetectionEvent } from "@/proctoring/onDevice/types";
import { MAX_PROCTORING_WARNINGS, PROCTORING_ENABLED, SECURITY_VIOLATIONS, SecurityViolationType, VIOLATION_FOOTER_LABELS } from "../violations";

const EVENT_TO_VIOLATION: Record<DetectedEventType, SecurityViolationType> = {
  NO_FACE: SECURITY_VIOLATIONS.NO_FACE,
  MULTIPLE_FACES: SECURITY_VIOLATIONS.MULTIPLE_PEOPLE,
  LOOKING_LEFT: SECURITY_VIOLATIONS.SIDE_LOOK,
  LOOKING_RIGHT: SECURITY_VIOLATIONS.SIDE_LOOK,
  HEAD_TILT: SECURITY_VIOLATIONS.HEAD_TILT,
};

type UseOnDeviceProctoringParams = {
  active: boolean;
  paused: boolean;
  warningsCount: number;
  onViolation?: (violationType: SecurityViolationType) => void;
  onWarning?: (violationType: SecurityViolationType) => void;
};

export function useOnDeviceProctoring({ active, paused, warningsCount, onViolation, onWarning }: UseOnDeviceProctoringParams) {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice("front");

  const [engine] = useState(() => new ProctoringEngine());

  const [activeCandidateBadge, setActiveCandidateBadge] = useState<SecurityViolationType | null>(null);
  const [graceActive, setGraceActive] = useState(true);
  const wasPausedRef = useRef(paused);
  const wasActiveRef = useRef(active);

  const maxedOut = warningsCount >= MAX_PROCTORING_WARNINGS;
  // Company-level kill switch (Tenant.live_proctoring_enabled) - when off,
  // the camera/detector never runs and no violation can ever fire,
  // regardless of `active`.
  const proctoringEnabled = PROCTORING_ENABLED;

  useEffect(() => {
    if (!hasPermission) requestPermission();
  }, [hasPermission, requestPermission]);

  // Fresh grace period each time proctoring (re)starts.
  useEffect(() => {
    if (active && !wasActiveRef.current) engine.reset();
    wasActiveRef.current = active;
  }, [active, engine]);

  // Resuming from a pause (the violation modal just closed) — re-check
  // whatever's still ongoing instead of waiting for it to naturally end.
  useEffect(() => {
    if (wasPausedRef.current && !paused) engine.rearmAll();
    wasPausedRef.current = paused;
  }, [paused, engine]);

  useEffect(() => {
    const unsubscribeLive = engine.onLiveState((state) => {
      setGraceActive(state.graceActive);
      if (state.face === "NO_FACE") setActiveCandidateBadge(SECURITY_VIOLATIONS.NO_FACE);
      else if (state.face === "MULTIPLE_FACES") setActiveCandidateBadge(SECURITY_VIOLATIONS.MULTIPLE_PEOPLE);
      else if (state.head === "LEFT" || state.head === "RIGHT") setActiveCandidateBadge(SECURITY_VIOLATIONS.SIDE_LOOK);
      else if (state.head === "TILT") setActiveCandidateBadge(SECURITY_VIOLATIONS.HEAD_TILT);
      else setActiveCandidateBadge(null);
    });
    const unsubscribeEvent = engine.onEvent((event: DetectionEvent) => {
      const violationType = EVENT_TO_VIOLATION[event.eventType];
      if (event.severity === "VIOLATION") onViolation?.(violationType);
      else if (event.severity === "WARNING") onWarning?.(violationType);
    });
    return () => {
      unsubscribeLive();
      unsubscribeEvent();
    };
  }, [engine, onViolation, onWarning]);

  const faceDetectorOutput = useFaceDetectorOutput({
    performanceMode: "fast",
    runLandmarks: false,
    runContours: false,
    runClassifications: false,
    trackingEnabled: false,
    minFaceSize: MIN_FACE_SIZE,
    onFacesDetected(faces) {
      if (!active || paused || maxedOut || !proctoringEnabled) return;

      if (faces.length === 0) {
        engine.ingestFace({ faceCount: 0 }, Date.now());
        return;
      }

      // Largest face by area is treated as the primary candidate (the exam taker).
      let primary = faces[0]!;
      let primaryArea = primary.bounds.width * primary.bounds.height;
      for (let i = 1; i < faces.length; i++) {
        const f = faces[i]!;
        const area = f.bounds.width * f.bounds.height;
        if (area > primaryArea) {
          primary = f;
          primaryArea = area;
        }
      }

      engine.ingestFace(
        {
          faceCount: faces.length,
          primaryFace: { yawDeg: primary.yawAngle, pitchDeg: primary.pitchAngle, rollDeg: primary.rollAngle },
        },
        Date.now(),
      );
    },
    onError(error) {
      console.warn("OnDeviceProctoringPanel: face detector error, skipping frame.", error);
    },
  });

  const isInactive = !active || paused || !hasPermission || maxedOut || !proctoringEnabled;
  const currentBadge = isInactive ? null : activeCandidateBadge;

  const footerLabel = !proctoringEnabled
    ? "Proctoring Off"
    : !hasPermission
      ? "Camera Off"
      : maxedOut
        ? "Submitting…"
        : currentBadge
          ? VIOLATION_FOOTER_LABELS[currentBadge] || "VIOLATION\nDETECTED"
          : graceActive
            ? "Get Ready…"
            : "AI Active";

  const isDangerBadge = !!currentBadge || maxedOut;

  const footerIcon: keyof typeof Ionicons.glyphMap = !hasPermission
    ? "videocam-off-outline"
    : isDangerBadge
      ? "alert-circle"
      : "shield-checkmark-outline";

  return {
    hasPermission,
    requestPermission,
    device,
    faceDetectorOutput,
    footerLabel,
    isDangerBadge,
    footerIcon,
    warningsCount,
  };
}
