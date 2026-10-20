import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { CHOOSE_COMPANY_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

import { useChooseCompany } from "./useChooseCompany";

/** After an admin with access to several companies signs in (no company code - user, 2026-10-19):
 *  one row per company; tapping one opens it. */
export default function ChooseCompanyScreen() {
  const insets = useSafeAreaInsets();
  const { companies, choose, choosing, error, back } = useChooseCompany();

  return (
    <View style={[styles.container, { paddingTop: insets.top + 16 }]}>
      <StatusBar style="dark" />
      <Pressable onPress={back} style={styles.back} hitSlop={8} accessibilityRole="button" accessibilityLabel={CHOOSE_COMPANY_TEXT.back}>
        <Ionicons name="chevron-back" size={20} color={Colors.textHeading} />
        <AppText color={Colors.textHeading}>{CHOOSE_COMPANY_TEXT.back}</AppText>
      </Pressable>

      <ScrollView contentContainerStyle={styles.body}>
        <AppText variant="h2" color={Colors.textHeading} weight={FontWeight.bold}>
          {CHOOSE_COMPANY_TEXT.title}
        </AppText>
        <AppText variant="bodySmall" color={Colors.loginSubtext} style={styles.subtitle}>
          {CHOOSE_COMPANY_TEXT.subtitle}
        </AppText>

        {companies.map((company) => (
          <Pressable
            key={company.tenantId}
            onPress={() => choose(company.tenantId)}
            disabled={choosing !== null}
            style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
            accessibilityRole="button"
            accessibilityLabel={company.companyName}
          >
            <Ionicons name="business-outline" size={22} color={Colors.loginAccent} />
            <View style={styles.rowText}>
              <AppText weight={FontWeight.semiBold} color={Colors.textHeading}>
                {company.companyName}
              </AppText>
              <AppText variant="caption" color={Colors.loginSubtext}>
                {company.tenantId}
              </AppText>
            </View>
            {choosing === company.tenantId ? (
              <ActivityIndicator color={Colors.loginAccent} />
            ) : (
              <Ionicons name="chevron-forward" size={18} color={Colors.loginSubtext} />
            )}
          </Pressable>
        ))}

        {error && (
          <AppText color={Colors.danger} style={styles.error} accessibilityRole="alert">
            {error}
          </AppText>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.white },
  back: { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 16 },
  body: { paddingHorizontal: 24, paddingTop: 24, paddingBottom: 32 },
  subtitle: { marginTop: 8, marginBottom: 20 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.surfaceBorder,
  },
  rowPressed: { opacity: 0.7 },
  rowText: { flex: 1, gap: 2 },
  error: { marginTop: 8, textAlign: "center" },
});
