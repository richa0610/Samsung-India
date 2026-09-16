import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { Camera, CameraDevice, CameraOutput } from "react-native-vision-camera";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Fonts } from "@/theme/fonts";

type ProctoringCameraAreaProps = {
  hasPermission: boolean;
  requestPermission: () => void;
  device: CameraDevice | undefined;
  faceDetectorOutput: CameraOutput;
  active: boolean;
  footerLabel: string;
  footerIcon: keyof typeof Ionicons.glyphMap;
  isDangerBadge: boolean;
  warningsCount: number;
};

export default function ProctoringCameraArea({
  hasPermission,
  requestPermission,
  device,
  faceDetectorOutput,
  active,
  footerLabel,
  footerIcon,
  isDangerBadge,
  warningsCount,
}: ProctoringCameraAreaProps) {
  return (
    <View style={styles.cameraArea}>
      {!hasPermission ? (
        <View style={styles.permissionPrompt}>
          <Ionicons name="camera-outline" size={22} color={Colors.white} />
          <AppText style={styles.permissionText}>Camera access is required for this proctored test.</AppText>
          <Pressable style={styles.permissionButton} onPress={requestPermission}>
            <AppText style={styles.permissionButtonText} weight={FontWeight.semiBold}>
              Enable Camera
            </AppText>
          </Pressable>
        </View>
      ) : !device ? (
        <ActivityIndicator color={Colors.white} />
      ) : (
        <>
          <Camera style={styles.camera} device={device} isActive={active} outputs={[faceDetectorOutput]} />
          <View
            style={[
              styles.footer,
              isDangerBadge && styles.footerDanger,
              !isDangerBadge && warningsCount > 0 && styles.footerWarning,
            ]}
          >
            <Ionicons name={footerIcon} size={12} color={Colors.white} />
            <AppText style={styles.footerText} weight={FontWeight.bold} numberOfLines={2}>
              {footerLabel}
            </AppText>
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  cameraArea: {
    height: 86,
    backgroundColor: "#1F2937",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  camera: { width: "100%", height: "100%" },
  permissionPrompt: {
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingHorizontal: 12,
  },
  permissionText: {
    color: Colors.white,
    fontSize: Fonts.overline,
    textAlign: "center",
  },
  permissionButton: {
    marginTop: 2,
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  permissionButtonText: { color: Colors.white, fontSize: Fonts.overline },
  footer: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingVertical: 5,
    paddingHorizontal: 4,
    backgroundColor: Colors.success,
    flexWrap: "wrap",
  },
  footerWarning: { backgroundColor: "#F59E0B" },
  footerDanger: { backgroundColor: "#DC2626" },
  footerText: {
    color: Colors.white,
    fontSize: 9.5,
    textAlign: "center",
    lineHeight: 12,
  },
});
