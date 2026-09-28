import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, TextInput } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";

import { CameraViewfinder, useSecurityCheckIn } from "@/components/attendance/security-checkin";
import { LivenessInstructionOverlay, useFaceLivenessGate } from "@/components/liveness-check";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { UploadFile } from "@/api/training";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import AttendanceSheetField from "./AttendanceSheetField";

type TrainerCheckOutModalProps = {
  visible: boolean;
  submitting: boolean;
  onClose: () => void;
  onConfirm: (photo: UploadFile, attendanceSheet: UploadFile, totalPax: number) => void;
};

// How long to let the camera session settle after the live face-detector
// output is detached before actually firing the still capture - some
// devices cap how many concurrent camera streams they can run and throw
// from capturePhotoToFile if the shutter fires mid-reconfiguration.
const DETACH_SETTLE_MS = 350;

export default function TrainerCheckOutModal({ visible, submitting, onClose, onConfirm }: TrainerCheckOutModalProps) {
  const camera = useSecurityCheckIn();
  const [sheet, setSheet] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [totalPax, setTotalPax] = useState("");

  // Runs only while the modal is open, the camera has permission, and no
  // photo has been captured yet - stops (and re-arms on retake) otherwise.
  const liveness = useFaceLivenessGate({ active: visible && camera.hasPermission && !camera.hasPhoto });

  // True only for the brief window between tapping Capture and the shutter
  // actually firing - see DETACH_SETTLE_MS above for why the detector output
  // needs to be gone before that.
  const [detachingForCapture, setDetachingForCapture] = useState(false);
  const checkedPhotoUriRef = useRef<string | null>(null);

  const pickSheet = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "image/*"],
      copyToCacheDirectory: true,
      multiple: false,
      base64: false,
    });
    if (!result.canceled && result.assets?.[0]) setSheet(result.assets[0]);
  };

  const photoUri =
    camera.photoSource && typeof camera.photoSource === "object" && "uri" in camera.photoSource
      ? (camera.photoSource as { uri: string }).uri
      : null;

  const handleRetakeAndReset = () => {
    camera.handleRetake();
    liveness.reset();
    checkedPhotoUriRef.current = null;
  };

  const handleSecureCapture = async () => {
    if (!liveness.verified) return;
    setDetachingForCapture(true);
    await new Promise((resolve) => setTimeout(resolve, DETACH_SETTLE_MS));
    await camera.handleCapture();
    setDetachingForCapture(false);
  };

  // Defense-in-depth: the live check above only reflects the feed up to the
  // moment just before the shutter fires, not the literal captured frame -
  // this analyzes the actual saved photo and forces a retake if it somehow
  // doesn't show exactly one face (e.g. the camera was nudged during the
  // DETACH_SETTLE_MS settle window).
  useEffect(() => {
    if (!photoUri) return;
    if (checkedPhotoUriRef.current === photoUri) return;
    checkedPhotoUriRef.current = photoUri;

    let cancelled = false;
    (async () => {
      const result = await liveness.verifyCapturedPhoto(photoUri);
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
  }, [photoUri]);

  const paxValue = Number(totalPax);
  const paxValid = totalPax.trim() !== "" && Number.isInteger(paxValue) && paxValue >= 0;

  const submit = () => {
    if (!photoUri || !sheet || !paxValid) return;
    onConfirm(
      { uri: photoUri, name: "checkout.jpg", type: "image/jpeg" },
      { uri: sheet.uri, name: sheet.name || "attendance-sheet", type: sheet.mimeType || "application/octet-stream" },
      paxValue,
    );
  };

  const canSubmit = !!photoUri && !!sheet && paxValid && !submitting;
  const captureDisabled = camera.capturing || detachingForCapture || (!camera.hasPhoto && !liveness.verified);

  return (
    <AppModal visible={visible} onClose={onClose} position="center">
      <ScrollView style={styles.card} contentContainerStyle={styles.cardContent} showsVerticalScrollIndicator={false}>
        <AppText style={styles.title} weight={FontWeight.semiBold}>
          Security Check-Out
        </AppText>
        <AppText style={styles.subtitle}>
          Please capture a clear photo of your face to verify your identity.
        </AppText>

        <CameraViewfinder
          hasPhoto={camera.hasPhoto}
          photoSource={camera.photoSource}
          hasPermission={camera.hasPermission}
          requestPermission={camera.requestPermission}
          device={camera.device}
          deviceTimedOut={camera.deviceTimedOut}
          retryDevice={camera.retryDevice}
          photoOutput={camera.photoOutput}
          cameraRef={camera.cameraRef}
          // Stays attached for as long as there's no photo yet, so presence
          // is re-checked live right up until the moment Capture is tapped -
          // only detached for the brief DETACH_SETTLE_MS window around the
          // actual shutter call (see handleSecureCapture and the device
          // stream-limit note there).
          extraOutputs={!camera.hasPhoto && !detachingForCapture ? [liveness.faceDetectorOutput] : undefined}
          overlay={
            !camera.hasPhoto && (
              <LivenessInstructionOverlay
                step={liveness.step}
                instruction={liveness.instruction}
                detectorError={liveness.detectorError}
                onRetry={liveness.reset}
              />
            )
          }
        />

        <Pressable
          style={[styles.captureBtn, captureDisabled && styles.dim]}
          onPress={camera.hasPhoto ? handleRetakeAndReset : handleSecureCapture}
          disabled={captureDisabled}
        >
          {camera.capturing || detachingForCapture ? (
            <ActivityIndicator size="small" color={Colors.white} />
          ) : (
            <>
              <Ionicons name={camera.hasPhoto ? "refresh" : "camera"} size={18} color={Colors.white} />
              <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.captureText}>
                {camera.hasPhoto ? "Retake Photo" : "Capture Photo"}
              </AppText>
            </>
          )}
        </Pressable>

        <AppText style={styles.fieldLabel} weight={FontWeight.semiBold}>
          Total Pax (Trainees)
        </AppText>
        <TextInput
          style={styles.paxInput}
          value={totalPax}
          onChangeText={(text) => setTotalPax(text.replace(/[^0-9]/g, ""))}
          keyboardType="number-pad"
          placeholder="Number of trainees present"
          placeholderTextColor={Colors.gray400}
        />

        <AttendanceSheetField
          fileName={sheet?.name ?? null}
          onPick={pickSheet}
          onClear={() => setSheet(null)}
        />

        <Pressable style={[styles.submitBtn, !canSubmit && styles.dim]} onPress={submit} disabled={!canSubmit}>
          {submitting ? (
            <ActivityIndicator size="small" color={Colors.white} />
          ) : (
            <AppText color={Colors.white} weight={FontWeight.bold} style={styles.submitText}>
              Submit
            </AppText>
          )}
        </Pressable>
      </ScrollView>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  // flexShrink: AppModal (center) caps its height to the visible screen; this
  // lets the ScrollView take that clamp and scroll instead of overflowing.
  card: { width: "90%", maxWidth: 420, flexShrink: 1, alignSelf: "center", backgroundColor: Colors.white, borderRadius: 24 },
  cardContent: { padding: 20 },
  title: { fontSize: 22, color: Colors.black, textAlign: "center", letterSpacing: 0.2 },
  subtitle: { fontSize: 12, color: Colors.gray500, textAlign: "center", marginTop: 6, lineHeight: 18 },
  captureBtn: {
    height: 48, borderRadius: 10, backgroundColor: Colors.brandBlue,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 14,
  },
  captureText: { fontSize: 16 },
  fieldLabel: { fontSize: 13, color: Colors.gray700, marginTop: 14 },
  paxInput: {
    height: 44, borderRadius: 10, borderWidth: 1, borderColor: Colors.gray300,
    backgroundColor: Colors.white, paddingHorizontal: 12, marginTop: 8, fontSize: 14, color: Colors.black,
  },
  submitBtn: {
    height: 48, borderRadius: 10, backgroundColor: "#05A869",
    alignItems: "center", justifyContent: "center", marginTop: 12,
  },
  submitText: { fontSize: 16 },
  dim: { opacity: 0.45 },
});
