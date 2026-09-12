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

export function useSecurityCheckIn() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice("front");
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
  // True once the camera has reconfigured onto photoOutput alone after a
  // face was found - see cameraOutputs below for why that reconfiguration
  // has to happen at all, and handleCameraStarted for when this flips true.
  const [photoReady, setPhotoReady] = useState(false);

  const faceDetectorOutput = useFaceDetectorOutput({
    performanceMode: "fast",
    runLandmarks: false,
    runContours: false,
    runClassifications: false,
    trackingEnabled: false,
    minFaceSize: MIN_FACE_SIZE,
    onFacesDetected(faces) {
      const detected = faces.length > 0;
      setFaceDetected((prev) => {
        if (detected && !prev) {
          // Just found a face for the first time this attempt - the camera
          // is about to drop this output and reconfigure onto photoOutput
          // alone (see cameraOutputs), so capture stays gated until
          // handleCameraStarted confirms that finished.
          setPhotoReady(false);
        }
        return detected;
      });
    },
    onError(error) {
      // Skip the frame rather than flipping faceDetected either way - a
      // transient detector error shouldn't silently bypass the requirement,
      // but it also shouldn't permanently brick capture off one bad frame.
      console.warn("useSecurityCheckIn: face detector error, skipping frame.", error);
    },
  });

  // Run the camera with ONE output at a time rather than both concurrently:
  // scan with just the (lightweight) face detector until a face shows up,
  // then swap to just the photo output for the actual capture. Some
  // devices' front cameras can't negotiate a format both outputs can share
  // simultaneously, which made the whole camera session fail to start the
  // moment live face detection was added - sequencing them avoids ever
  // asking for both formats at once.
  const cameraOutputs = useMemo(
    () => (faceDetected ? [photoOutput] : [faceDetectorOutput]),
    [faceDetected, photoOutput, faceDetectorOutput],
  );

  const handleCameraStarted = () => {
    // Only meaningful once we've actually switched onto photoOutput - the
    // very first "started" event (still scanning) shouldn't count.
    if (faceDetected) setPhotoReady(true);
  };

  // No live camera device (an emulator/web with no virtual camera) means
  // there's nothing to run face detection against - the detector will never
  // fire, so faceDetected would stay false forever. Don't block the existing
  // dev/testing fallback (a placeholder photo, see handleCapture) behind a
  // signal that can't possibly become true in that environment; only real
  // hardware devices are held to the face-must-be-visible requirement.
  const canCapture = !device || (faceDetected && photoReady);

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
    // Back to scanning: cameraOutputs swaps back to the face detector on
    // its own once faceDetected flips false.
    setFaceDetected(false);
    setPhotoReady(false);
  };

  return {
    hasPermission,
    requestPermission,
    device,
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
