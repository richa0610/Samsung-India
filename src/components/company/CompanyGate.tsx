import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { COMPANY_TEXT } from "@/constants/strings";
import { useCompany } from "@/hooks/useCompany";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

import CompanyCodeForm from "./CompanyCodeForm";

type CompanyGateProps = {
  children: React.ReactNode;
};

/**
 * The company code is mandatory before signing in (user, 2026-10-18): until this device has a
 * company, the gate shows the company code form instead of `children` (the sign-in options, a QR
 * join). Once it has one, it shows "Company: <name> · Change" above them.
 */
export default function CompanyGate({ children }: CompanyGateProps) {
  const company = useCompany();
  const [changing, setChanging] = useState(false);
  const stopChanging = () => setChanging(false);

  if (!company || changing) {
    return <CompanyCodeForm onDone={stopChanging} onCancel={company ? stopChanging : undefined} />;
  }

  return (
    <>
      <View style={styles.row}>
        <AppText variant="bodySmall" color={Colors.loginSubtext}>
          {`${COMPANY_TEXT.current}: `}
        </AppText>
        <AppText variant="bodySmall" color={Colors.textHeading} weight={FontWeight.semiBold}>
          {company.companyName}
        </AppText>
        <Pressable
          onPress={() => setChanging(true)}
          hitSlop={8}
          accessibilityRole="button"
          accessibilityLabel={`${COMPANY_TEXT.change} ${COMPANY_TEXT.current.toLowerCase()}`}
        >
          <AppText variant="bodySmall" color={Colors.loginAccent} weight={FontWeight.semiBold} style={styles.change}>
            {COMPANY_TEXT.change}
          </AppText>
        </Pressable>
      </View>
      {children}
    </>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", justifyContent: "center", flexWrap: "wrap", marginTop: 16 },
  change: { marginLeft: 10 },
});
