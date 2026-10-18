import { Pressable, StyleSheet, View } from "react-native";

import AppButton from "@/components/ui/AppButton";
import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { COMPANY_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

import { useCompanyCodeForm } from "./useCompanyCodeForm";

type CompanyCodeFormProps = {
  /** Called once the code is confirmed and saved. */
  onDone?: () => void;
  /** Shown only when there is already a company to go back to. */
  onCancel?: () => void;
};

/** "Enter your company code" - ties this device to one company before anyone signs in. */
export default function CompanyCodeForm({ onDone, onCancel }: CompanyCodeFormProps) {
  const { code, changeCode, error, loading, submit } = useCompanyCodeForm(onDone);

  return (
    <View style={styles.container}>
      <AppText variant="h3" color={Colors.textHeading} align="center" style={styles.title}>
        {COMPANY_TEXT.title}
      </AppText>
      <AppText variant="bodySmall" color={Colors.loginSubtext} align="center" style={styles.body}>
        {COMPANY_TEXT.body}
      </AppText>

      <AppInput
        label={COMPANY_TEXT.label}
        placeholder={COMPANY_TEXT.placeholder}
        icon="business-outline"
        value={code}
        onChangeText={changeCode}
        autoCapitalize="none"
        autoCorrect={false}
        maxLength={100}
        returnKeyType="go"
        onSubmitEditing={submit}
        placeholderTextColor={Colors.authPlaceholder}
        labelColor={Colors.authLabel}
        containerStyle={styles.field}
      />

      {error && (
        <AppText color={Colors.danger} style={styles.error} accessibilityRole="alert">
          {error}
        </AppText>
      )}

      <AppButton title={COMPANY_TEXT.submit} onPress={submit} loading={loading} />

      {onCancel && (
        <Pressable onPress={onCancel} hitSlop={8} style={styles.cancel} accessibilityRole="button">
          <AppText color={Colors.loginAccent} weight={FontWeight.medium}>
            {COMPANY_TEXT.cancel}
          </AppText>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignSelf: "stretch", marginTop: 24 },
  title: { fontWeight: "700" },
  body: { marginTop: 8, marginBottom: 20 },
  field: { marginBottom: 8 },
  error: { marginBottom: 12 },
  cancel: { alignSelf: "center", marginTop: 16 },
});
