import { useEffect, useRef, useState } from "react";
import { Alert, Image, ImageSourcePropType, Platform } from "react-native";
import { CameraRef, CommonResolutions, useCameraDevice, useCameraPermission, usePhotoOutput } from "react-native-vision-camera";
import { useImageFaceDetector } from "react-native-vision-camera-face-detector";

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

  // Detects faces on the already-captured still photo, not on live camera
  // frames - an earlier version ran a live per-frame detector as a second,
  // concurrent camera output, which is what made capture itself fail on
  // some devices (they can't negotiate two outputs sharing the camera at
  // once). Checking the one resulting file after a normal single-output
  // capture needs no second output at all. Same ML Kit engine and
  // threshold as live proctoring (see @/proctoring/onDevice/config).
  const imageFaceDetector = useImageFaceDetector({
    performanceMode: "fast",
    runLandmarks: false,
    runContours: false,
    runClassifications: false,
    trackingEnabled: false,
    minFaceSize: MIN_FACE_SIZE,
  });

  // Camera is ready to attempt a capture - this is about device/permission
  // readiness now, not face presence (that's checked after capture, on the
  // resulting file - see handleCapture).
  const canCapture = Platform.OS === "web" || !!device;

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
    if (!canCapture) return;

    setCapturing(true);
    try {
      if (cameraRef.current && device) {
        const photoFile = await photoOutput.capturePhotoToFile({}, {});
        const uri = photoFile.filePath.startsWith("file://") ? photoFile.filePath : `file://${photoFile.filePath}`;

        let faces: unknown[] = [];
        try {
          faces = imageFaceDetector.detectFaces(uri);
        } catch (err) {
          // Couldn't even run the check - treat as "not verified" rather
          // than silently accepting an unverified photo.
          console.warn("useSecurityCheckIn: image face detection failed.", err);
        }
        if (faces.length === 0) {
          Alert.alert("Face not detected", "We couldn't find a face in that photo. Please try again with your face clearly visible.");
          return;
        }

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
  };

  return {
    hasPermission,
    requestPermission,
    device,
    deviceTimedOut,
    retryDevice,
    photoOutput,
    canCapture,
    cameraRef,
    capturing,
    photoSource,
    hasPhoto: photoSource !== null,
    handleCapture,
    handleRetake,
  };
}
