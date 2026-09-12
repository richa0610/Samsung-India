import React from "react";
import {
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  View,
} from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { SecurityViolationType } from "@/components/proctoring/violations";

export type SecurityLockedViewProps = {
  violationType?: SecurityViolationType | null;
  onClose: () => void;
};

export default function SecurityLockedView({
  violationType,
  onClose,
}: SecurityLockedViewProps) {
  const handleClose = () => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
      setTimeout(onClose, 10);
    } else {
      onClose();
    }
  };

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={undefined}
    >
      {/* Semi-transparent overlay so content behind is still faintly visible */}
      <View style={styles.overlay} pointerEvents="box-none">
        <View style={styles.card}>
          <AppText style={styles.title} weight={FontWeight.bold}>
            LOCKED : Security Violation.
          </AppText>

          {violationType ? (
            <AppText style={styles.subtitle}>
              Reason: {violationType}
            </AppText>
          ) : null}

          <AppText style={styles.description}>
            Your Post Test has been automatically terminated due to a proctoring
            violation. You cannot continue this test.
          </AppText>

          <Pressable
            style={styles.closeButton}
            onPress={handleClose}
            accessibilityRole="button"
            accessibilityLabel="Close and return to home"
          >
            <AppText style={styles.closeText} weight={FontWeight.semiBold}>
              Close
            </AppText>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.55)",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  card: {
    width: "100%",
    maxWidth: 380,
    backgroundColor: "#1C1C1E",
    borderRadius: 16,
    padding: 22,
    ...createShadow({ x: 0, y: 8, blur: 16, opacity: 0.55, elevation: 12 }),
  },
  title: {
    color: Colors.white,
    fontSize: 18,
    lineHeight: 24,
    marginBottom: 8,
  },
  subtitle: {
    color: "#EF4444",
    fontSize: 13,
    marginBottom: 10,
  },
  description: {
    color: "#9CA3AF",
    fontSize: 13.5,
    lineHeight: 20,
    marginBottom: 20,
  },
  closeButton: {
    alignSelf: "flex-end",
    paddingVertical: 4,
    paddingHorizontal: 6,
  },
  closeText: {
    color: "#60A5FA",
    fontSize: 15,
  },
});
