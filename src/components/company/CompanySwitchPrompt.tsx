import { Pressable, StyleSheet, View } from "react-native";

import AppButton from "@/components/ui/AppButton";
import AppText from "@/components/ui/AppText";
import { Company } from "@/config/company";
import { COMPANY_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

type CompanySwitchPromptProps = {
  /** The company the scanned QR code belongs to. */
  company: Company;
  onSwitch: () => void;
  onCancel: () => void;
};

/** "This training belongs to <company>. Switch this phone to that company?" - for a QR code from a
 *  company other than the one this phone signs in to. */
export default function CompanySwitchPrompt({ company, onSwitch, onCancel }: CompanySwitchPromptProps) {
  return (
    <View style={styles.container}>
      <AppText color={Colors.loginSubtext} align="center">
        {COMPANY_TEXT.qrBelongsTo}
      </AppText>
      <AppText variant="h3" color={Colors.textHeading} weight={FontWeight.semiBold} align="center" style={styles.name}>
        {company.companyName}
      </AppText>
      <AppText color={Colors.loginSubtext} align="center" style={styles.hint}>
        {COMPANY_TEXT.qrSwitchHint}
      </AppText>
      <AppButton title={COMPANY_TEXT.qrSwitch} onPress={onSwitch} />
      <Pressable onPress={onCancel} hitSlop={8} style={styles.cancel} accessibilityRole="button">
        <AppText color={Colors.loginAccent} weight={FontWeight.medium}>
          {COMPANY_TEXT.cancel}
        </AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignSelf: "stretch", marginTop: 8 },
  name: { marginTop: 4 },
  hint: { marginTop: 8, marginBottom: 16 },
  cancel: { alignSelf: "center", marginTop: 16 },
});
