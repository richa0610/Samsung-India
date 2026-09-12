import { ReactNode } from "react";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type SuiteFieldProps = {
  label: string;
  readonlyValue?: ReactNode;
  children: ReactNode;
};

export default function SuiteField({ label, readonlyValue, children }: SuiteFieldProps) {
  return (
    <View style={styles.third}>
      <AppText style={styles.fieldLabel} weight={FontWeight.medium}>
        {label}
      </AppText>
      {readonlyValue !== undefined ? (
        <AppText style={styles.readonlyValue}>{readonlyValue}</AppText>
      ) : (
        children
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  third: { flex: 1 },
  fieldLabel: { fontSize: Fonts.caption, marginBottom: 4, color: Colors.gray600 },
  readonlyValue: {
    fontSize: Fonts.bodySm,
    paddingVertical: 8,
    color: Colors.gray600,
  },
});
