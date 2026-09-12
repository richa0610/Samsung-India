import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type NoPhotoControlsProps = {
  // True while either capturing the photo or running the post-capture face
  // check on it (see useSecurityCheckIn.handleCapture) - one continuous
  // busy state from the trainee/trainer's point of view.
  capturing: boolean;
  // False while the camera itself isn't ready yet (permission/device) -
  // whether a face is present is only known after capture, not before.
  canCapture: boolean;
  onCapture: () => void;
};

export default function NoPhotoControls({ capturing, canCapture, onCapture }: NoPhotoControlsProps) {
  const disabled = capturing || !canCapture;

  return (
    <>
      <Pressable
        style={[styles.captureButton, disabled && styles.captureButtonDisabled]}
        onPress={onCapture}
        disabled={disabled}
        accessibilityRole="button"
        accessibilityLabel="Capture Photo"
      >
        {capturing ? (
          <ActivityIndicator size="small" color={Colors.white} />
        ) : (
          <>
            <Ionicons name="camera" size={20} color={Colors.white} />
            <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.captureButtonText}>
              Capture Photo
            </AppText>
          </>
        )}
      </Pressable>

      <View style={styles.actionsRow}>
        <View style={styles.disabledRetakeButton}>
          <Ionicons name="refresh" size={18} color="#9CA3AF" />
          <AppText color="#9CA3AF" weight={FontWeight.medium} style={styles.buttonText16}>
            Retake
          </AppText>
        </View>

        <View style={styles.disabledProceedButton}>
          <AppText color={Colors.white} weight={FontWeight.medium} style={styles.buttonText16}>
            Proceed
          </AppText>
          <Ionicons name="arrow-forward" size={16} color={Colors.white} />
        </View>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  captureButton: {
    width: "100%",
    height: 48,
    borderRadius: 10,
    backgroundColor: "#0066FF",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginTop: 16,
  },
  captureButtonDisabled: {
    opacity: 0.7,
  },
  captureButtonText: {
    fontSize: 18,
  },
  buttonText16: {
    fontSize: 16,
  },
  actionsRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 12,
  },
  disabledRetakeButton: {
    flex: 1,
    height: 44,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    backgroundColor: Colors.white,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    opacity: 0.6,
  },
  disabledProceedButton: {
    flex: 1,
    height: 44,
    borderRadius: 10,
    backgroundColor: "#10B981",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    opacity: 0.45,
  },
});
