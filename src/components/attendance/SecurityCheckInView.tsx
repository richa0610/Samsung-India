import { StatusBar } from "expo-status-bar";
import { useEffect, useRef, useState } from "react";
import { Alert, ImageSourcePropType, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { LivenessInstructionOverlay, useFaceLivenessGate } from "@/components/liveness-check";
import AppText from "@/components/ui/AppText";
import { Breakpoints } from "@/theme/breakpoints";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import {
  CameraViewfinder,
  NoPhotoControls,
  PhotoCapturedControls,
  SecurityCheckInFooter,
  useSecurityCheckIn,
} from "./security-checkin";

export type SecurityCheckInViewProps = {
  onProceed: (photoSource: ImageSourcePropType) => void;
  onBack?: () => void;
};

// How long to let the camera session settle after the live face-detector
// output is detached before actually firing the still capture - some
// devices cap how many concurrent camera streams they can run and throw
// from capturePhotoToFile if the shutter fires mid-reconfiguration.
const DETACH_SETTLE_MS = 350;

export default function SecurityCheckInView({ onProceed }: SecurityCheckInViewProps) {
  const insets = useSafeAreaInsets();
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

  // Runs only while there's no photo yet - stops (and re-arms on retake) otherwise.
  const liveness = useFaceLivenessGate({ active: hasPermission && !hasPhoto });

  // True only for the brief window between tapping Capture and the shutter
  // actually firing - see DETACH_SETTLE_MS above for why the detector output
  // needs to be gone before that.
  const [detachingForCapture, setDetachingForCapture] = useState(false);
  const checkedPhotoUriRef = useRef<string | null>(null);

  const handleProceedPress = () => {
    if (!photoSource) return;
    onProceed(photoSource);
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
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="dark" animated />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.card}>
          <AppText style={styles.title} weight={FontWeight.semiBold}>
            Security Check-In
          </AppText>
          <AppText style={styles.subtitle}>Please capture a clear photo of your face{"\n"}to verify your identity.</AppText>

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
            <PhotoCapturedControls onRetake={handleRetakeAndReset} onProceed={handleProceedPress} />
          )}
        </View>

        <SecurityCheckInFooter hasPhoto={hasPhoto} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    paddingTop: 50,
  },
  statusBarBackground: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 20,
    justifyContent: "space-between",
  },
  card: {
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    alignSelf: "center",
    backgroundColor: Colors.white,
    borderRadius: 24,
    padding: 20,
    flex: 1,
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 4, blur: 12, opacity: 0.08, elevation: 3 }),
  },
  title: {
    fontSize: 24,
    color: "#111827",
    textAlign: "center",
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "center",
    marginTop: 6,
    marginBottom: 10,
    lineHeight: 18,
  },
});
