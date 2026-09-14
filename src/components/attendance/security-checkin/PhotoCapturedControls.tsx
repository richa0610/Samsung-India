import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type PhotoCapturedControlsProps = {
  onRetake: () => void;
  onProceed: () => void;
};

export default function PhotoCapturedControls({ onRetake, onProceed }: PhotoCapturedControlsProps) {
  return (
    <>
      <View style={styles.greenTipsBanner}>
        <View style={styles.greenDot} />
        <View style={styles.tipsTextColumn}>
          <AppText style={styles.tipsTitle} weight={FontWeight.bold}>
            Tips for best results
          </AppText>
          <AppText style={styles.tipsSubtitle}>
            Ensure good lighting, look straight at the camera and remove anything that covers your face.
          </AppText>
        </View>
        <Ionicons name="chevron-forward" size={16} color="#374151" />
      </View>

      <View style={styles.actionsRow}>
        <Pressable style={styles.enabledRetakeButton} onPress={onRetake} accessibilityRole="button" accessibilityLabel="Retake Photo">
          <Ionicons name="refresh" size={18} color="#374151" />
          <AppText color="#374151" weight={FontWeight.semiBold} style={styles.buttonText16}>
            Retake
          </AppText>
        </Pressable>

        <Pressable style={styles.enabledProceedButton} onPress={onProceed} accessibilityRole="button" accessibilityLabel="Proceed to Home">
          <AppText color={Colors.white} weight={FontWeight.bold} style={styles.buttonText16}>
            Proceed
          </AppText>
          <Ionicons name="arrow-forward" size={18} color={Colors.white} />
        </Pressable>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  greenTipsBanner: {
    backgroundColor: "#E6F8F0",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 14,
  },
  greenDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#10B981",
  },
  tipsTextColumn: {
    flex: 1,
    gap: 2,
  },
  tipsTitle: {
    fontSize: 12,
    color: "#111827",
  },
  tipsSubtitle: {
    fontSize: 10,
    color: "#4B5563",
    lineHeight: 14,
  },
  actionsRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 12,
  },
  buttonText16: {
    fontSize: 16,
  },
  enabledRetakeButton: {
    flex: 1,
    height: 46,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#374151",
    backgroundColor: Colors.white,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  enabledProceedButton: {
    flex: 1,
    height: 46,
    borderRadius: 10,
    backgroundColor: "#05A869",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
});
