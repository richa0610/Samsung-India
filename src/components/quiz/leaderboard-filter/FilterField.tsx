import { ReactNode } from "react";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";

type FilterFieldProps = {
  label: string;
  style?: object;
  children: ReactNode;
};

export default function FilterField({ label, style, children }: FilterFieldProps) {
  return (
    <View style={style ?? styles.fieldBlock}>
      <AppText style={styles.fieldLabel} weight={FontWeight.semiBold}>
        {label}
      </AppText>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  fieldBlock: {
    marginBottom: 8,
  },
  fieldLabel: {
    fontSize: 12,
    color: "#1E293B",
    letterSpacing: 0.3,
    marginBottom: 2,
  },
});
