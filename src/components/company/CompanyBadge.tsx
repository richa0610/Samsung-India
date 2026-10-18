import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Company } from "@/config/company";
import { COMPANY_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

type CompanyBadgeProps = {
  company: Company;
  onChange: () => void;
};

/** The company this phone signs in to, as a small pill - "🏢 Samsung India | Change". */
export default function CompanyBadge({ company, onChange }: CompanyBadgeProps) {
  return (
    <View style={styles.pill}>
      <Ionicons name="business-outline" size={14} color={Colors.loginAccent} />
      <AppText variant="bodySmall" color={Colors.textHeading} weight={FontWeight.semiBold} numberOfLines={1} style={styles.name}>
        {company.companyName}
      </AppText>
      <View style={styles.divider} />
      <Pressable
        onPress={onChange}
        hitSlop={10}
        accessibilityRole="button"
        accessibilityLabel={`${COMPANY_TEXT.change} ${COMPANY_TEXT.current.toLowerCase()}`}
      >
        <AppText variant="bodySmall" color={Colors.loginAccent} weight={FontWeight.semiBold}>
          {COMPANY_TEXT.change}
        </AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "center",
    maxWidth: "100%",
    marginTop: 14,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: Colors.brandTintSoft,
  },
  name: { marginLeft: 6, flexShrink: 1 },
  divider: { width: 1, height: 14, marginHorizontal: 10, backgroundColor: Colors.surfaceBorder },
});
