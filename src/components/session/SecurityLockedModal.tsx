import React from "react";
import { Modal, Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export type SecurityLockedModalProps = {
  visible: boolean;
  onClose: () => void;
  title?: string;
};

export default function SecurityLockedModal({
  visible,
  onClose,
  title = "LOCKED : Security Violation.",
}: SecurityLockedModalProps) {
  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onClose}
    >
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <AppText style={styles.title} weight={FontWeight.bold}>
            {title}
          </AppText>
          <Pressable
            style={styles.closeButton}
            onPress={onClose}
            accessibilityRole="button"
            accessibilityLabel="Close locked notice"
            hitSlop={8}
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
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.45)",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 24,
  },
  card: {
    width: "100%",
    maxWidth: 380,
    backgroundColor: "#1F2429",
    borderRadius: 14,
    paddingTop: 24,
    paddingBottom: 16,
    paddingHorizontal: 20,
    ...createShadow({ x: 0, y: 8, blur: 24, opacity: 0.4, elevation: 10 }),
  },
  title: {
    color: "#FFFFFF",
    fontSize: 16.5,
    letterSpacing: 0.2,
    marginBottom: 20,
  },
  closeButton: {
    alignSelf: "flex-end",
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  closeText: {
    color: "#0066FF",
    fontSize: 16,
  },
});
