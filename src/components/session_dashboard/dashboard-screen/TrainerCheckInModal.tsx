import { useEffect, useRef, useState } from "react";
import { Alert, ScrollView, StyleSheet } from "react-native";

import {
  CameraViewfinder,
  NoPhotoControls,
  PhotoCapturedControls,
  SecurityCheckInFooter,
  useSecurityCheckIn,
} from "@/components/attendance/security-checkin";
import { LivenessInstructionOverlay, useFaceLivenessGate } from "@/components/liveness-check";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { Breakpoints } from "@/theme/breakpoints";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type TrainerCheckInPhoto = { uri: string; name: string; type: string };

type TrainerCheckInModalProps = {
  visible: boolean;
  onClose: () => void;
  onConfirm: (photo: TrainerCheckInPhoto) => void;
};

// How long to let the camera session settle after the live face-detector
// output is detached before actually firing the still capture - some
// devices cap how many concurrent camera streams they can run and throw
// from capturePhotoToFile if the shutter fires mid-reconfiguration.
const DETACH_SETTLE_MS = 350;

export default function TrainerCheckInModal({ visible, onClose, onConfirm }: TrainerCheckInModalProps) {
  const {
    hasPermission,
    requestPermission,
    device,
    deviceTimedOut,
    retryDevice,
    photoOutput,
    cameraRef,
    capturing,
    photoSource,
    hasPhoto,
    handleCapture,
    handleRetake,
  } = useSecurityCheckIn();

  // Runs only while the modal is open, the camera has permission, and no
  // photo has been captured yet - stops (and re-arms on retake) otherwise.
  const liveness = useFaceLivenessGate({ active: visible && hasPermission && !hasPhoto });

  // True only for the brief window between tapping Capture and the shutter
  // actually firing - see DETACH_SETTLE_MS above for why the detector output
  // needs to be gone before that, not just once verification first passed.
  const [detachingForCapture, setDetachingForCapture] = useState(false);
  const checkedPhotoUriRef = useRef<string | null>(null);

  const handleProceed = () => {
    if (!photoSource || typeof photoSource !== "object" || !("uri" in photoSource)) return;
    onConfirm({ uri: (photoSource as { uri: string }).uri, name: "trainer_checkin.jpg", type: "image/jpeg" });
  };

  const handleRetakeAndReset = () => {
    handleRetake();
    liveness.reset();
    checkedPhotoUriRef.current = null;
  };

  const handleSecureCapture = async () => {
    if (!liveness.verified) return;
    setDetachingForCapture(true);
    await new Promise((resolve) => setTimeout(resolve, DETACH_SETTLE_MS));
    await handleCapture();
    setDetachingForCapture(false);
  };

  // Defense-in-depth: the live check above only reflects the feed up to the
  // moment just before the shutter fires, not the literal captured frame -
  // this analyzes the actual saved photo and forces a retake if it somehow
  // doesn't show exactly one face (e.g. the camera was nudged during the
  // DETACH_SETTLE_MS settle window).
  useEffect(() => {
    if (!hasPhoto || !photoSource || typeof photoSource !== "object" || !("uri" in photoSource)) return;
    const uri = (photoSource as { uri: string }).uri;
    if (checkedPhotoUriRef.current === uri) return;
    checkedPhotoUriRef.current = uri;

    let cancelled = false;
    (async () => {
      const result = await liveness.verifyCapturedPhoto(uri);
      if (cancelled) return;
      if (!result.ok) {
        Alert.alert(
          result.faceCount === 0 ? "No face detected" : "Multiple faces detected",
          "The captured photo doesn't clearly show one face. Please retake it.",
        );
        handleRetakeAndReset();
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handleRetakeAndReset/liveness identity isn't the trigger, the captured uri is
  }, [hasPhoto, photoSource]);

  return (
    <AppModal visible={visible} onClose={onClose} position="center">
      <ScrollView style={styles.card} contentContainerStyle={styles.cardContent} showsVerticalScrollIndicator={false}>
        <AppText style={styles.title} weight={FontWeight.semiBold}>
          Trainer Check-In
        </AppText>
        <AppText style={styles.subtitle}>Please capture a clear photo of your face{"\n"}to start this session.</AppText>

        <CameraViewfinder
          hasPhoto={hasPhoto}
          photoSource={photoSource}
          hasPermission={hasPermission}
          requestPermission={requestPermission}
          device={device}
          deviceTimedOut={deviceTimedOut}
          retryDevice={retryDevice}
          photoOutput={photoOutput}
          cameraRef={cameraRef}
          // Stays attached for as long as there's no photo yet, so presence
          // is re-checked live right up until the moment Capture is tapped -
          // only detached for the brief DETACH_SETTLE_MS window around the
          // actual shutter call (see handleSecureCapture and the device
          // stream-limit note there).
          extraOutputs={!hasPhoto && !detachingForCapture ? [liveness.faceDetectorOutput] : undefined}
          overlay={
            !hasPhoto && (
              <LivenessInstructionOverlay
                step={liveness.step}
                instruction={liveness.instruction}
                detectorError={liveness.detectorError}
                onRetry={liveness.reset}
              />
            )
          }
        />

        {!hasPhoto ? (
          <NoPhotoControls
            capturing={capturing || detachingForCapture}
            onCapture={handleSecureCapture}
            disabled={!liveness.verified}
          />
        ) : (
          <PhotoCapturedControls onRetake={handleRetakeAndReset} onProceed={handleProceed} />
        )}

        <SecurityCheckInFooter hasPhoto={hasPhoto} />
      </ScrollView>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  card: {
    // Matches the trainee Security Check-In screen's card sizing exactly
    // (src/components/attendance/SecurityCheckInView.tsx) - full width up to
    // the same mobile breakpoint, filling the modal's available height
    // instead of shrinking to its content.
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    flex: 1,
    alignSelf: "center",
    backgroundColor: Colors.white,
    borderRadius: 24,
  },
  cardContent: {
    padding: 20,
  },
  title: {
    fontSize: 22,
    color: "#111827",
    textAlign: "center",
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 6,
    lineHeight: 18,
  },
});
