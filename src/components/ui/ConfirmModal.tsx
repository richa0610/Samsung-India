import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";

type ConfirmTone = "primary" | "danger";

type ConfirmModalProps = {
  visible: boolean;
  message: string;
  title?: string;
  /** Optional icon shown in a tinted circle above the title, e.g. "log-out-outline". */
  icon?: keyof typeof Ionicons.glyphMap;
  /** Colors the icon badge + confirm button. Defaults to the app's main color. */
  tone?: ConfirmTone;
  cancelText?: string;
  confirmText?: string;
  onCancel: () => void;
  onConfirm: () => void;
};

const TONE_COLORS: Record<ConfirmTone, { badge: string; icon: string; button: string }> = {
  primary: { badge: "#E4ECFF", icon: Colors.mainColour1, button: Colors.mainColour1 },
  danger: { badge: "#FDE8E8", icon: Colors.danger, button: Colors.danger },
};

export default function ConfirmModal({
  visible,
  message,
  title,
  icon,
  tone = "primary",
  cancelText = "No",
  confirmText = "Yes",
  onCancel,
  onConfirm,
}: ConfirmModalProps) {
  const colors = TONE_COLORS[tone];

  return (
    <AppModal visible={visible} onClose={onCancel} position="center" showCloseButton={false}>
      {icon && (
        <View style={[styles.iconBadge, { backgroundColor: colors.badge }]}>
          <Ionicons name={icon} size={28} color={colors.icon} />
        </View>
      )}
      {title && (
        <AppText style={styles.title} weight={FontWeight.bold}>
          {title}
        </AppText>
      )}
      <AppText style={styles.message} color={Colors.gray600}>
        {message}
      </AppText>
      <View style={styles.actionRow}>
        <Pressable style={[styles.button, styles.cancelButton]} onPress={onCancel}>
          <AppText color={Colors.gray600} weight={FontWeight.semiBold}>
            {cancelText}
          </AppText>
        </Pressable>
        <Pressable style={[styles.button, { backgroundColor: colors.button }]} onPress={onConfirm}>
          <AppText color={Colors.white} weight={FontWeight.semiBold}>
            {confirmText}
          </AppText>
        </Pressable>
      </View>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  iconBadge: {
    alignSelf: "center",
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.md,
  },
  title: {
    textAlign: "center",
    fontSize: 18,
    color: Colors.black,
    marginBottom: Spacing.xs,
  },
  message: {
    textAlign: "center",
    marginBottom: Spacing.lg,
    lineHeight: 20,
  },
  actionRow: {
    flexDirection: "row",
    gap: Spacing.md,
  },
  button: {
    flex: 1,
    height: 46,
    borderRadius: Radius.xl,
    alignItems: "center",
    justifyContent: "center",
  },
  cancelButton: {
    backgroundColor: Colors.gray100,
  },
});
