import { useEffect, useRef, useState } from "react";
import { Alert, Image, ImageSourcePropType, Platform } from "react-native";
import {
  CameraRef,
  CommonResolutions,
  useCameraDevice,
  useCameraPermission,
  usePhotoOutput,
} from "react-native-vision-camera";

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
      // quietly accepting a placeholder for what's a check-in photo.
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
    cameraRef,
    capturing,
    photoSource,
    hasPhoto: photoSource !== null,
    handleCapture,
    handleRetake,
  };
}
