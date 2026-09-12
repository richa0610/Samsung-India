import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";

import { CameraViewfinder, useSecurityCheckIn } from "@/components/attendance/security-checkin";
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
  onConfirm: (photo: UploadFile, attendanceSheet: UploadFile) => void;
};

export default function TrainerCheckOutModal({ visible, submitting, onClose, onConfirm }: TrainerCheckOutModalProps) {
  const camera = useSecurityCheckIn();
  const [sheet, setSheet] = useState<DocumentPicker.DocumentPickerAsset | null>(null);

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

  const submit = () => {
    if (!photoUri || !sheet) return;
    onConfirm(
      { uri: photoUri, name: "checkout.jpg", type: "image/jpeg" },
      { uri: sheet.uri, name: sheet.name || "attendance-sheet", type: sheet.mimeType || "application/octet-stream" },
    );
  };

  const canSubmit = !!photoUri && !!sheet && !submitting;

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
          cameraOutputs={camera.cameraOutputs}
          onCameraStarted={camera.handleCameraStarted}
          faceDetected={camera.faceDetected}
          photoReady={camera.photoReady}
          canCapture={camera.canCapture}
          cameraRef={camera.cameraRef}
        />

        <Pressable
          style={[styles.captureBtn, (camera.capturing || (!camera.hasPhoto && !camera.canCapture)) && styles.dim]}
          onPress={camera.hasPhoto ? camera.handleRetake : camera.handleCapture}
          disabled={camera.capturing || (!camera.hasPhoto && !camera.canCapture)}
        >
          {camera.capturing ? (
            <ActivityIndicator size="small" color={Colors.white} />
          ) : (
            <>
              <Ionicons
                name={camera.hasPhoto ? "refresh" : camera.canCapture ? "camera" : "scan-outline"}
                size={18}
                color={Colors.white}
              />
              <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.captureText}>
                {camera.hasPhoto ? "Retake Photo" : camera.canCapture ? "Capture Photo" : "Face not detected"}
              </AppText>
            </>
          )}
        </Pressable>

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
  title: { fontSize: 22, color: "#111827", textAlign: "center", letterSpacing: 0.2 },
  subtitle: { fontSize: 12, color: "#6B7280", textAlign: "center", marginTop: 6, lineHeight: 18 },
  captureBtn: {
    height: 48, borderRadius: 10, backgroundColor: "#0066FF",
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 14,
  },
  captureText: { fontSize: 16 },
  submitBtn: {
    height: 48, borderRadius: 10, backgroundColor: "#05A869",
    alignItems: "center", justifyContent: "center", marginTop: 12,
  },
  submitText: { fontSize: 16 },
  dim: { opacity: 0.45 },
});
