import { StyleSheet } from "react-native";

import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";

/** Shared by AttendanceModuleCard + ModuleCard so the flow cards stay identical. */
export const flowCardStyles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    padding: 14,
    marginBottom: 12,
  },
  header: { flexDirection: "row", alignItems: "center", gap: 8, paddingBottom: 12 },
  headerTitle: { fontSize: Fonts.body, letterSpacing: 0.3 },
  headerDivider: { height: 1, backgroundColor: Colors.gray200, marginBottom: 14 },
  row: { flexDirection: "row", gap: 12 },
  half: { flex: 1 },
  fieldLabel: { fontSize: Fonts.body, marginBottom: Spacing.sm },
  questionsLabelRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: Spacing.sm },
  maxBadge: { backgroundColor: Colors.success, borderRadius: Radius.pill, paddingHorizontal: 8, paddingVertical: 2 },
  maxBadgeText: { fontSize: Fonts.overline },
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: Spacing.lg },
  checkboxRowTight: { marginBottom: Spacing.sm },
  geoHint: { fontSize: Fonts.caption, marginTop: 6, lineHeight: 16 },
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
});
