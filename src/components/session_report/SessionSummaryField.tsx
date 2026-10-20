import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

type SessionSummaryFieldProps = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
  fullWidth?: boolean;
};

export default function SessionSummaryField({ icon, label, value, fullWidth }: SessionSummaryFieldProps) {
  return (
    <View style={[styles.field, fullWidth && styles.fieldFullWidth]}>
      <View style={styles.iconBox}>
        <Ionicons name={icon} size={16} color={Colors.mainColour1} />
      </View>
      <View style={styles.fieldTextWrap}>
        <AppText style={styles.fieldLabel} color={Colors.gray600}>{label}</AppText>
        <AppText style={styles.fieldValue} weight={FontWeight.medium} numberOfLines={fullWidth ? 2 : 1}>
          {value}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    width: "48%",
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    padding: 5,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.md,
  },
  fieldFullWidth: { width: "100%", marginTop: 10 },
  iconBox: {
    width: 20,
    height: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  fieldTextWrap: { flex: 1, gap: 0 },
  fieldLabel: { fontSize: Fonts.overline },
  fieldValue: { fontSize: Fonts.bodySm },
});
