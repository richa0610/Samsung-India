import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { ProctoringCameraArea, useOnDeviceProctoring } from "./on-device-panel";
import { SecurityViolationType } from "./violations";

/**
 * On-device replacement for ProctoringPanel: same props, same visual layout
 * (header/camera-area/footer badge — literally the same style rules below),
 * but detection runs locally via react-native-vision-camera + ML Kit instead
 * of snapshotting a JPEG every 500ms to the checkFrameForFaces backend
 * endpoint. See the "onDevice" module for the detection engine itself.
 */

type Props = {
  token: string | null;
  active: boolean;
  paused?: boolean;
  warningsCount?: number;
  latestViolation?: SecurityViolationType | null;
  /** Called with the violation type when any violation fires */
  onViolation?: (violationType: SecurityViolationType) => void;
  /** Called with the violation type on the earlier, non-strike WARNING tier */
  onWarning?: (violationType: SecurityViolationType) => void;
  /** Legacy callback when max warnings reached */
  onMaxWarnings?: () => void;
};

export default function OnDeviceProctoringPanel({ active, paused = false, warningsCount = 0, onViolation, onWarning }: Props) {
  const { hasPermission, requestPermission, device, faceDetectorOutput, footerLabel, isDangerBadge, footerIcon } =
    useOnDeviceProctoring({ active, paused, warningsCount, onViolation, onWarning });

  return (
    <View style={[styles.panel, isDangerBadge && styles.panelDanger]}>
      <View style={[styles.header, isDangerBadge && styles.headerDanger]}>
        <Ionicons name={isDangerBadge ? "alert-circle" : "shield-checkmark-outline"} size={11} color={Colors.white} />
        <AppText style={styles.headerText} weight={FontWeight.medium}>
          AI PROCTORING
        </AppText>
      </View>

      <ProctoringCameraArea
        hasPermission={hasPermission}
        requestPermission={requestPermission}
        device={device}
        faceDetectorOutput={faceDetectorOutput}
        active={active}
        footerLabel={footerLabel}
        footerIcon={footerIcon}
        isDangerBadge={isDangerBadge}
        warningsCount={warningsCount}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    width: "92%",
    maxWidth: 142,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: "#00A859",
    overflow: "hidden",
    backgroundColor: "#111827",
    alignSelf: "center",
  },
  panelDanger: { borderColor: "#DC2626" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingVertical: 4,
    backgroundColor: "#374151",
  },
  headerDanger: { backgroundColor: "#DC2626" },
  headerText: {
    color: Colors.white,
    fontSize: 9,
    letterSpacing: 0.5,
    alignSelf: "center",
  },
});
