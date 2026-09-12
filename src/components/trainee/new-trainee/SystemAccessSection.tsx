import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppButton from "@/components/ui/AppButton";
import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Spacing } from "@/theme/spacing";
import { NewTraineeForm } from "./useNewTraineeForm";

export function SystemAccessSection({ form }: { form: NewTraineeForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={6} title="System Access" icon="lock-closed-outline" />

      <View style={styles.noticeRow}>
        <Ionicons name="information-circle-outline" size={16} color={Colors.gray600} />
        <AppText style={styles.noticeText} color={Colors.gray600}>
          Login credentials are automatically generated based on the trainee UID.
        </AppText>
      </View>

      <AppInput label="Username (Same as UID)" value={form.traineeUid} editable={false} />
      <AppInput
        label="System Generated Password"
        value={form.password}
        editable={false}
        caption="This password will be hashed securely upon saving."
      />

      <Pressable style={styles.checkboxRow} onPress={() => form.setVerified((v) => !v)}>
        <View style={[styles.checkbox, form.verified && styles.checkboxChecked]}>
          {form.verified && <Ionicons name="checkmark" size={12} color={Colors.white} />}
        </View>
        <AppText style={styles.checkboxLabel}>
          I verify that all the information entered above is correct and verified
        </AppText>
      </Pressable>

      {form.notice && <AppText style={styles.notice}>{form.notice}</AppText>}

      <AppButton title="Register Trainee" onPress={form.handleSubmit} loading={form.submitting} />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
  noticeRow: { flexDirection: "row", gap: 8, marginBottom: Spacing.lg, alignItems: "flex-start" },
  noticeText: { fontSize: Fonts.bodySm, flex: 1 },
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: Spacing.lg },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.gray400,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: { backgroundColor: Colors.mainColour1, borderColor: Colors.mainColour1 },
  checkboxLabel: { fontSize: Fonts.body, flex: 1 },
  notice: { color: Colors.danger, fontSize: Fonts.bodySm, textAlign: "center", marginBottom: 12 },
});
