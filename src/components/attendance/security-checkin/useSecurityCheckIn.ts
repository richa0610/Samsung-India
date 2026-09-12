import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, Image, ImageSourcePropType, Platform } from "react-native";
import {
  CameraRef,
  CommonResolutions,
  useCameraDevice,
  useCameraPermission,
  usePhotoOutput,
} from "react-native-vision-camera";
import { useFaceDetectorOutput } from "react-native-vision-camera-face-detector";

import { MIN_FACE_SIZE } from "@/proctoring/onDevice/config";

const DEFAULT_SAMPLE_PHOTO: ImageSourcePropType = require("@/assets/images/user_img/default_male.png");

// How long to wait for `useCameraDevice` to find a front camera before
// treating it as a real failure rather than still-initializing. Generous
// enough to cover a slow/cold camera stack, short enough that a genuinely
// broken camera doesn't leave the trainee/trainer staring at a spinner
// with no explanation of what's wrong.
const DEVICE_TIMEOUT_MS = 5000;

export function useSecurityCheckIn() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice("front");

  // True once DEVICE_TIMEOUT_MS has passed with no device found - the
  // camera view shows a real "Camera failed to start" error with a Retry
  // action instead of an indefinite spinner. `retryAttempt` just re-arms
  // the timer for another window; there's no native "recheck devices" API
  // to call directly, but the underlying device list can and does update
  // on its own (e.g. another app releasing the camera), so giving it
  // another timeout window is a real retry, not just a fake progress bar.
  const [deviceTimedOut, setDeviceTimedOut] = useState(false);
  const [retryAttempt, setRetryAttempt] = useState(0);

  useEffect(() => {
    // Once a device shows up, this branch stops mattering entirely - the
    // camera view below only ever checks `deviceTimedOut` inside a `!device`
    // condition, so a stale `true` left over from an earlier failed attempt
    // is harmless once `device` exists.
    if (device) return;
    const timer = setTimeout(() => setDeviceTimedOut(true), DEVICE_TIMEOUT_MS);
    return () => clearTimeout(timer);
  }, [device, retryAttempt]);

  const retryDevice = () => {
    setDeviceTimedOut(false);
    setRetryAttempt((n) => n + 1);
  };
  // mirrorMode defaults to "auto", which mirrors front-camera output to match
  // the mirrored live selfie preview — the same behavior the previous
  // expo-camera implementation needed an explicit isImageMirror flag for.
  //
  // This is a face-presence check-in photo, not a print-quality shot - the
  // hook's own defaults (UHD_4_3 = 3024x4032 @ 0.9 quality) produce a
  // multi-megabyte JPEG that then gets uploaded with no further compression
  // (see secureCheckIn), which is what actually made "Mark Attendance" feel
  // slow on venue Wi-Fi/mobile data. HD_4_3 at a lower quality is still
  // plenty to see a face and cuts the upload to a fraction of the size.
  const photoOutput = usePhotoOutput({
    targetResolution: CommonResolutions.HD_4_3,
    quality: 0.7,
  });
  const cameraRef = useRef<CameraRef>(null);

  const [capturing, setCapturing] = useState(false);
  const [photoSource, setPhotoSource] = useState<ImageSourcePropType | null>(null);

  // Live, per-frame "is a face currently in the viewfinder" signal - this is
  // presence only (not full proctoring: no pose/liveness/single-face
  // checks), just enough to stop a blank or pointed-away photo from ever
  // being captured for a check-in/check-out.
  const [faceDetected, setFaceDetected] = useState(false);

  const faceDetectorOutput = useFaceDetectorOutput({
    performanceMode: "fast",
    runLandmarks: false,
    runContours: false,
    runClassifications: false,
    trackingEnabled: false,
    minFaceSize: MIN_FACE_SIZE,
    onFacesDetected(faces) {
      setFaceDetected(faces.length > 0);
    },
    onError(error) {
      // Skip the frame rather than flipping faceDetected either way - a
      // transient detector error shouldn't silently bypass the requirement,
      // but it also shouldn't permanently brick capture off one bad frame.
      console.warn("useSecurityCheckIn: face detector error, skipping frame.", error);
    },
  });

  // Both outputs run together, the whole time - an earlier version of this
  // hook swapped between a face-detector-only phase and a photo-only phase
  // to work around a theorized "camera can't negotiate two outputs at once"
  // failure, but that was never actually confirmed, it added a real
  // reconfiguration delay to every check-in, and the real bug turned out to
  // be the `!device` fallback below. Reverted back to the simple/fast form.
  const cameraOutputs = useMemo(() => [photoOutput, faceDetectorOutput], [photoOutput, faceDetectorOutput]);

  // No-op now that outputs never change - kept so CameraViewfinder can keep
  // wiring `onStarted` unconditionally without a special case.
  const handleCameraStarted = () => {};
  // Always true - there's no output-reconfiguration phase to wait for
  // anymore. Kept (rather than removed) purely so CameraViewfinder's hint
  // banner logic doesn't need touching.
  const photoReady = true;

  // Only web gets a pass on the face requirement (no real camera API there
  // to run detection against at all - see handleCapture's sample-photo
  // fallback, which is scoped the same way). A native device with no
  // camera found is a real failure, not a reason to skip the check - it
  // must still show a face before capture is allowed, same as everywhere
  // else; previously `!device` alone satisfied this condition, which meant
  // a device that failed to initialize its camera silently bypassed the
  // face-detection requirement entirely instead of being blocked.
  const canCapture = Platform.OS === "web" || faceDetected;

  // Request camera permission on mount
  useEffect(() => {
    if (!hasPermission) {
      requestPermission();
    }
  }, [hasPermission, requestPermission]);

  const applySamplePhoto = () => {
    // Resolve the bundled asset to a real `{ uri }` so the upload paths
    // (which need a URI, not a require() id) still work.
    const resolved = Image.resolveAssetSource(DEFAULT_SAMPLE_PHOTO);
    setPhotoSource(resolved?.uri ? { uri: resolved.uri } : DEFAULT_SAMPLE_PHOTO);
  };

  const handleCapture = async () => {
    // Belt-and-suspenders: the capture button is already disabled while this
    // is false, but never actually take the photo without a face in frame
    // even if something slips past that (e.g. a very fast double-tap).
    if (!canCapture) return;

    setCapturing(true);
    try {
      if (cameraRef.current && device) {
        const photoFile = await photoOutput.capturePhotoToFile({}, {});
        const uri = photoFile.filePath.startsWith("file://") ? photoFile.filePath : `file://${photoFile.filePath}`;
        setPhotoSource({ uri });
        return;
      }

      // No live camera device - only expected on web, which has no real
      // camera API in this app, so a sample photo lets the flow still be
      // exercised there. On a real device this means the camera genuinely
      // never initialized - fall through to the error below instead of
      // quietly accepting a placeholder for what's a face-verification
      // check-in.
      if (Platform.OS === "web") {
        applySamplePhoto();
        return;
      }
      Alert.alert(
        "Camera unavailable",
        "Couldn't access the camera. Please check that camera permission is granted and try again.",
      );
    } catch {
      if (Platform.OS === "web") {
        applySamplePhoto();
      } else {
        Alert.alert("Capture failed", "Couldn't capture a photo. Please try again.");
      }
    } finally {
      setCapturing(false);
    }
  };

  const handleRetake = () => {
    setPhotoSource(null);
    setFaceDetected(false);
  };

  return {
    hasPermission,
    requestPermission,
    device,
    deviceTimedOut,
    retryDevice,
    cameraOutputs,
    handleCameraStarted,
    faceDetected,
    photoReady,
    canCapture,
    cameraRef,
    capturing,
    photoSource,
    hasPhoto: photoSource !== null,
    handleCapture,
    handleRetake,
  };
}
