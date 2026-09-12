import { Modal, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { SecurityViolationType } from "./violations";

export type ProctoringSoftWarningProps = {
  visible: boolean;
  violationType: SecurityViolationType | null;
};

/**
 * Early, non-strike nudge shown at the WARNING severity tier — before a
 * detection has persisted long enough to escalate into a real VIOLATION
 * strike (see SecurityViolationModal). Auto-dismisses on its own (driven by
 * usePostTest's triggerSoftWarning); no close button, no strike counted.
 */
export default function ProctoringSoftWarning({
  visible,
  violationType,
}: ProctoringSoftWarningProps) {
  if (!visible || !violationType) return null;

  return (
    <Modal visible={visible} transparent animationType="fade" statusBarTranslucent>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <View style={styles.headerRow}>
            <View style={styles.amberDot} />
            <AppText style={styles.headingText} weight={FontWeight.bold}>
              POSSIBLE VIOLATION
            </AppText>
          </View>
          <AppText style={styles.detailText}>{violationType}</AppText>
          <AppText style={styles.hintText}>
            Please correct yourself to avoid a strike.
          </AppText>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "transparent",
    alignItems: "center",
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  card: {
    width: "100%",
    maxWidth: 380,
    backgroundColor: "#1C1C1E",
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: "#F59E0B",
    ...createShadow({ x: 0, y: 6, blur: 14, opacity: 0.45, elevation: 10 }),
  },
  headerRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 6 },
  amberDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: "#F59E0B" },
  headingText: { color: "#FFFFFF", fontSize: 12.5, letterSpacing: 0.3 },
  detailText: { color: "#E5E7EB", fontSize: 13.5, marginBottom: 4 },
  hintText: { color: "#D1D5DB", fontSize: 12.5 },
});
