import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import AppModal from "@/components/ui/AppModal";
import { ParticipantItem } from "./sessionDashboardTypes";
import { Colors } from "@/theme/colors";

type UnlockExamModalProps = {
  participant: ParticipantItem | null;
  onCancel: () => void;
  onConfirm: (reason: string) => void;
};

export default function UnlockExamModal({ participant, onCancel, onConfirm }: UnlockExamModalProps) {
  const [reason, setReason] = useState("");

  const handleCancel = () => {
    setReason("");
    onCancel();
  };

  const handleConfirm = () => {
    const trimmed = reason.trim();
    if (!trimmed) return;
    setReason("");
    onConfirm(trimmed);
  };

  const lock = participant?.proctoring;

  return (
    <AppModal
      visible={!!participant}
      onClose={handleCancel}
      position="center"
      contentStyle={styles.sheet}
    >
      <View style={styles.header}>
        <Ionicons name="warning" size={16} color={Colors.warning} />
        <AppText style={styles.title}>UNLOCK EXAM FOR : {participant?.name}</AppText>
      </View>

      {lock && (
        <AppText style={styles.limitNote}>
          Only {lock.maxUnlocks} unlocks are allowed per trainee in a training. This is unlock{" "}
          {lock.unlocksUsed + 1} of {lock.maxUnlocks}
          {lock.unlocksUsed + 1 >= lock.maxUnlocks ? " - after this, they can't be unlocked again." : "."}
        </AppText>
      )}

      <AppText style={styles.label}>Please enter reason:</AppText>
      <TextInput
        style={styles.input}
        value={reason}
        onChangeText={setReason}
        placeholder=""
        placeholderTextColor={Colors.gray500}
        multiline
      />

      <View style={styles.actionsRow}>
        <Pressable onPress={handleCancel} hitSlop={8}>
          <AppText style={styles.cancelText}>Cancel</AppText>
        </Pressable>
        <Pressable onPress={handleConfirm} disabled={!reason.trim()} hitSlop={8}>
          <AppText style={[styles.okText, !reason.trim() && styles.okTextDisabled]}>OK</AppText>
        </Pressable>
      </View>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: {
    backgroundColor: Colors.black,
    borderRadius: 12,
    padding: 18,
    width: "88%",
  },
  header: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  title: { flex: 1, fontSize: 14, fontWeight: "800", color: Colors.gray100, lineHeight: 19 },
  limitNote: { fontSize: 12, lineHeight: 17, color: Colors.warning, marginTop: 12 },
  label: { fontSize: 12, color: Colors.gray300, marginTop: 18, marginBottom: 8 },
  input: {
    backgroundColor: Colors.gray700,
    borderRadius: 8,
    minHeight: 44,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 12,
    color: Colors.gray100,
    textAlignVertical: "top",
  },
  actionsRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 20,
    marginTop: 18,
  },
  cancelText: { fontSize: 13, color: Colors.blue400, fontWeight: "600" },
  okText: { fontSize: 13, color: Colors.blue400, fontWeight: "800" },
  okTextDisabled: { opacity: 0.4 },
});
