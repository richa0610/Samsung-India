import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { LOGIN_ROLE_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import RoleOptionCard, { ROLE_TONES } from "./RoleOptionCard";
import TrainerIcon from "./TrainerIcon";

export type StaffRole = "trainer" | "admin";

type Props = {
  visible: boolean;
  onClose: () => void;
  onChoose: (role: StaffRole) => void;
};

/** "Login as": the bottom sheet "Login here" opens, letting a trainer or an admin pick their login.
 *  Wording from LOGIN_ROLE_TEXT, colours from the theme. */
export default function LoginRoleSheet({ visible, onClose, onChoose }: Props) {
  return (
    <AppModal visible={visible} onClose={onClose} position="bottom" contentStyle={styles.sheet}>
      <View style={styles.handle} />

      <View style={styles.header}>
        <View style={styles.headerText}>
          <AppText color={Colors.sheetTitle} style={styles.title}>
            {LOGIN_ROLE_TEXT.title}
          </AppText>
          <AppText color={Colors.sheetSubtitle} style={styles.subtitle}>
            {LOGIN_ROLE_TEXT.subtitle}
          </AppText>
        </View>
        <Pressable
          onPress={onClose}
          hitSlop={10}
          style={styles.close}
          accessibilityRole="button"
          accessibilityLabel={LOGIN_ROLE_TEXT.close}
        >
          <Ionicons name="close" size={26} color={Colors.sheetClose} />
        </Pressable>
      </View>

      <View style={styles.cards}>
        <RoleOptionCard
          icon={<TrainerIcon size={32} color={Colors.roleTrainerIcon} />}
          title={LOGIN_ROLE_TEXT.trainer.title}
          body={LOGIN_ROLE_TEXT.trainer.body}
          tone={ROLE_TONES.trainer}
          onPress={() => onChoose("trainer")}
        />
        <RoleOptionCard
          icon={<Ionicons name="settings-outline" size={30} color={Colors.roleAdminIcon} />}
          title={LOGIN_ROLE_TEXT.admin.title}
          body={LOGIN_ROLE_TEXT.admin.body}
          tone={ROLE_TONES.admin}
          onPress={() => onChoose("admin")}
        />
      </View>

      <Pressable
        onPress={onClose}
        style={({ pressed }) => [styles.cancel, pressed && styles.cancelPressed]}
        accessibilityRole="button"
        accessibilityLabel={LOGIN_ROLE_TEXT.cancel}
      >
        <AppText color={Colors.neutralButtonText} style={styles.cancelText}>
          {LOGIN_ROLE_TEXT.cancel}
        </AppText>
      </Pressable>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: { paddingHorizontal: 22, paddingBottom: 16 },
  handle: { alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: Colors.sheetHandle, marginTop: 10 },
  header: { flexDirection: "row", alignItems: "flex-start", marginTop: 14 },
  headerText: { flex: 1 },
  title: { fontSize: 22, lineHeight: 28, fontWeight: "700" },
  subtitle: { fontSize: 15, lineHeight: 20, fontWeight: "400", marginTop: 4 },
  close: { width: 32, height: 32, alignItems: "flex-end", justifyContent: "center", marginTop: -2 },
  cards: { gap: 12, marginTop: 18 },
  cancel: {
    height: 46,
    borderRadius: 14,
    backgroundColor: Colors.neutralButtonBg,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 12,
  },
  cancelPressed: { opacity: 0.8 },
  cancelText: { fontSize: 15, lineHeight: 20, fontWeight: "600" },
});
