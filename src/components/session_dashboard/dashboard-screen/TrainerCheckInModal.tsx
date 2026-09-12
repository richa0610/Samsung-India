import { ScrollView, StyleSheet } from "react-native";

import {
  CameraViewfinder,
  NoPhotoControls,
  PhotoCapturedControls,
  SecurityCheckInFooter,
  useSecurityCheckIn,
} from "@/components/attendance/security-checkin";
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

export default function TrainerCheckInModal({ visible, onClose, onConfirm }: TrainerCheckInModalProps) {
  const {
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
    hasPhoto,
    handleCapture,
    handleRetake,
  } = useSecurityCheckIn();

  const handleProceed = () => {
    if (!photoSource || typeof photoSource !== "object" || !("uri" in photoSource)) return;
    onConfirm({ uri: (photoSource as { uri: string }).uri, name: "trainer_checkin.jpg", type: "image/jpeg" });
  };

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
        />

        {!hasPhoto ? (
          <NoPhotoControls capturing={capturing} canCapture={canCapture} onCapture={handleCapture} />
        ) : (
          <PhotoCapturedControls onRetake={handleRetake} onProceed={handleProceed} />
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
