import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppButton from "@/components/ui/AppButton";
import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import { SearchableMultiSelect } from "@/components/ui/SearchableSelect";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Spacing } from "@/theme/spacing";
import { SectionTitle } from "./SectionTitle";
import { AddTrainingForm } from "./useAddTrainingForm";

export function ChecklistSection({ form }: { form: AddTrainingForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={5} title="Checklist" icon="checkmark-circle-outline" />
      <SearchableMultiSelect
        label="Select Required Checklist(s)"
        compact
        placeholder="Select checklist items"
        values={form.checklist}
        options={form.checklistOptions}
        onChange={form.setChecklist}
      />

      <Pressable style={styles.checkboxRow} onPress={() => form.setAgreeTerms((v) => !v)}>
        <View style={[styles.checkbox, form.agreeTerms && styles.checkboxChecked]}>
          {form.agreeTerms && <Ionicons name="checkmark" size={12} color={Colors.white} />}
        </View>
        <AppText style={styles.checkboxLabel}>
          I agree to the <AppText style={styles.termsLink} color={Colors.mainColour1}>Terms &amp; Conditions</AppText>.
        </AppText>
      </Pressable>

      {form.notice && <AppText style={styles.notice}>{form.notice}</AppText>}

      <AppButton title="Register Training Session" onPress={form.handleSubmit} loading={form.submitting} />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
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
  termsLink: { fontSize: Fonts.body, textDecorationLine: "underline" },
  notice: { color: Colors.danger, fontSize: Fonts.bodySm, textAlign: "center", marginBottom: 12 },
});
