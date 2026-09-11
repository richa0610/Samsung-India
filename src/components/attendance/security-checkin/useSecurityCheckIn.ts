import { useEffect, useRef, useState } from "react";
import { Image, ImageSourcePropType } from "react-native";
import { CameraRef, useCameraDevice, useCameraPermission, usePhotoOutput } from "react-native-vision-camera";
import { useFaceDetectorOutput } from "react-native-vision-camera-face-detector";

import { MIN_FACE_SIZE } from "@/proctoring/onDevice/config";

const DEFAULT_SAMPLE_PHOTO: ImageSourcePropType = require("@/assets/images/user_img/default_male.png");

export function useSecurityCheckIn() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice("front");
  // mirrorMode defaults to "auto", which mirrors front-camera output to match
  // the mirrored live selfie preview — the same behavior the previous
  // expo-camera implementation needed an explicit isImageMirror flag for.
  const photoOutput = usePhotoOutput();
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

  // No live camera device (an emulator/web with no virtual camera) means
  // there's nothing to run face detection against - the detector will never
  // fire, so faceDetected would stay false forever. Don't block the existing
  // dev/testing fallback (a placeholder photo, see handleCapture) behind a
  // signal that can't possibly become true in that environment; only real
  // hardware devices are held to the face-must-be-visible requirement.
  const canCapture = !device || faceDetected;

  // Request camera permission on mount
  useEffect(() => {
    if (!hasPermission) {
      requestPermission();
    }
  }, [hasPermission, requestPermission]);

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
        setCapturing(false);
        return;
      }
    } catch {
      // Fallback for emulator / web / environment without active hardware camera stream
    }

    // Fallback sample photo for development / simulators / a camera that
    // won't capture. Resolve the bundled asset to a real `{ uri }` so the
    // upload paths (which need a URI, not a require() id) still work.
    const resolved = Image.resolveAssetSource(DEFAULT_SAMPLE_PHOTO);
    setPhotoSource(resolved?.uri ? { uri: resolved.uri } : DEFAULT_SAMPLE_PHOTO);
    setCapturing(false);
  };

  const handleRetake = () => {
    setPhotoSource(null);
  };

  return {
    hasPermission,
    requestPermission,
    device,
    photoOutput,
    faceDetectorOutput,
    faceDetected,
    canCapture,
    cameraRef,
    capturing,
    photoSource,
    hasPhoto: photoSource !== null,
    handleCapture,
    handleRetake,
  };
}
