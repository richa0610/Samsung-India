import { Modal, Platform, Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { SecurityViolationType } from "./violations";

export type SecurityViolationModalProps = {
  visible: boolean;
  violationType: SecurityViolationType | null;
  strikesRemaining: number;
  maxStrikes: number;
  onClose?: () => void;
  /** When true the Close button is hidden (terminal strike, auto-locking) */
  isTerminal?: boolean;
};

export default function SecurityViolationModal({
  visible,
  violationType,
  strikesRemaining,
  onClose,
  isTerminal = false,
}: SecurityViolationModalProps) {
  if (!visible || !violationType) return null;

  const handleClose = () => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
      setTimeout(() => {
        onClose?.();
      }, 10);
    } else {
      onClose?.();
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={isTerminal ? undefined : handleClose}
    >
      <View style={styles.backdrop}>
        <View style={styles.card}>
          {/* Header row */}
          <View style={styles.headerRow}>
            <View style={styles.redDot} />
            <AppText style={styles.headingText} weight={FontWeight.bold}>
              SECURITY VIOLATION DETECTED
            </AppText>
          </View>

          {/* Details */}
          <View style={styles.body}>
            <AppText style={styles.detailText}>
              <AppText style={styles.detailLabel}>Issue: </AppText>
              {violationType}
            </AppText>
            <AppText style={styles.detailText}>
              <AppText style={styles.detailLabel}>Strikes Remaining: </AppText>
              {strikesRemaining}
            </AppText>

            <AppText style={styles.warningText}>
              Please maintain focus on the screen.
            </AppText>
          </View>

          {/* Close action — hidden on terminal strike */}
          {!isTerminal && onClose && (
            <Pressable
              style={styles.closeButton}
              onPress={handleClose}
              accessibilityRole="button"
              accessibilityLabel="Close warning"
            >
              <AppText style={styles.closeText} weight={FontWeight.semiBold}>
                Close
              </AppText>
            </Pressable>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "transparent",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  card: {
    width: "100%",
    maxWidth: 380,
    backgroundColor: "#1C1C1E",
    borderRadius: 16,
    paddingTop: 16,
    paddingBottom: 12,
    paddingHorizontal: 18,
    ...createShadow({ x: 0, y: 8, blur: 16, opacity: 0.55, elevation: 12 }),
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 14,
  },
  redDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: "#EF4444",
  },
  headingText: {
    color: "#FFFFFF",
    fontSize: 13.5,
    letterSpacing: 0.3,
    flex: 1,
  },
  body: {
    gap: 6,
    marginBottom: 16,
  },
  detailText: {
    color: "#E5E7EB",
    fontSize: 14,
    lineHeight: 20,
  },
  detailLabel: {
    color: "#E5E7EB",
    fontSize: 14,
  },
  warningText: {
    color: "#D1D5DB",
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
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
