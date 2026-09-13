import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, Image, ImageSourcePropType, Platform } from "react-native";
import {
  CameraRef,
  CommonResolutions,
  useCameraDevice,
  useCameraPermission,
  usePhotoOutput,
} from "react-native-vision-camera";
import { createImageFaceDetector, useFaceDetectorOutput } from "react-native-vision-camera-face-detector";

const DEFAULT_SAMPLE_PHOTO: ImageSourcePropType = require("@/assets/images/user_img/default_male.png");

// Deliberately its own, stricter threshold rather than reusing proctoring's
// shared MIN_FACE_SIZE (0.12, tuned for a face at normal laptop/desk
// distance during an exam). A check-in selfie is held close to the camera,
// so a real face should fill much more of the frame - a real device
// confirmed "fast" mode + 0.12 will report a face on a blank wall/shirt/
// ceiling with no face in it at all.
const CHECK_IN_MIN_FACE_SIZE = 0.35;

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
  // True once the camera has reconfigured onto photoOutput alone after a
  // face was found - see cameraOutputs below for why that reconfiguration
  // has to happen at all, and handleCameraStarted for when this flips true.
  const [photoReady, setPhotoReady] = useState(false);

  const faceDetectorOutput = useFaceDetectorOutput({
    // "accurate" trades a bit of per-frame speed for real facial-structure
    // analysis instead of a coarse/fast heuristic - confirmed necessary:
    // "fast" mode reported a face pointed at a plain wall/shirt/ceiling on
    // a real device. This only runs while scanning for a face to enable
    // the button, not continuously during a whole exam, so the extra cost
    // per frame is an easy trade for not accepting a false positive.
    performanceMode: "accurate",
    runLandmarks: false,
    runContours: false,
    runClassifications: false,
    trackingEnabled: false,
    minFaceSize: CHECK_IN_MIN_FACE_SIZE,
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

  // Final check on the actual captured file, in handleCapture below - the
  // live detector above only guarantees a face was visible a moment
  // *before* the shutter fired, not that it's still in the exact frame
  // that got saved (e.g. moving/looking away right as the button is
  // tapped). Same engine, same tuned settings as the live detector, just
  // its one-shot static-image API instead of its per-frame camera output.
  //
  // Built via the raw `createImageFaceDetector` factory instead of the
  // package's own `useImageFaceDetector` hook: that hook's `detectFaces`
  // wrapper always converts whatever you pass it back into a plain string
  // before calling the native method - and passing a plain string is
  // confirmed (via a real device crash) to throw "Invalid image type.
  // Expected string or { uri }" out of the library's own native code. The
  // factory's detector has no such wrapper, so `{ uri }` reaches native
  // code as an object, which native's own resolver does handle.
  const imageFaceDetector = useMemo(
    () =>
      createImageFaceDetector({
        performanceMode: "accurate",
        runLandmarks: false,
        runContours: false,
        runClassifications: false,
        trackingEnabled: false,
        minFaceSize: CHECK_IN_MIN_FACE_SIZE,
      }),
    [],
  );

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

  // Only web gets a pass on the face requirement (no real camera API there
  // to run detection against at all - see handleCapture's sample-photo
  // fallback, which is scoped the same way). A native device with no
  // camera found is a real failure, not a reason to skip the check - it
  // must still show a face before capture is allowed, same as everywhere
  // else; previously `!device` alone satisfied this condition, which meant
  // a device that failed to initialize its camera silently bypassed the
  // face-detection requirement entirely instead of being blocked.
  const canCapture = Platform.OS === "web" || (faceDetected && photoReady);

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

        // Final gate: verify the actual saved file, not just the live
        // signal from a moment earlier. Both "genuinely no face" and "the
        // check itself failed" reject this attempt the same way for the
        // trainee/trainer - fail closed either way, per spec: an
        // unverifiable photo is never accepted just because the checker
        // broke. They're shown as two different alerts ONLY so the two
        // cases stay distinguishable during testing (a real "no face"
        // result vs. useImageFaceDetector erroring the way it did on an
        // earlier attempt) - collapse back to one shared message once
        // that's confirmed stable.
        try {
          // { uri } object form, not the bare string - confirmed via a real
          // device crash that passing a plain string here throws
          // "Invalid image type. Expected string or { uri }" from the
          // library's own native code (HybridImageFaceDetector.
          // resolveInputImage) despite a string being the documented usage -
          // a JS-to-native marshaling bug on this library's end for that
          // input shape. The object form routes through its other accepted
          // branch instead.
          const facesFound = imageFaceDetector.detectFaces({ uri }).length;
          if (facesFound === 0) {
            Alert.alert("Face not detected", "Please retake the picture with your face clearly visible.");
            return;
          }
        } catch (err) {
          const message = err instanceof Error ? err.message : String(err);
          console.warn("useSecurityCheckIn: post-capture face check failed.", err);
          Alert.alert("Face check failed - please retake", message);
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
    // Back to scanning: cameraOutputs swaps back to the face detector on
    // its own once faceDetected flips false.
    setFaceDetected(false);
    setPhotoReady(false);
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
