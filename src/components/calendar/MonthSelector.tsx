import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { Colors } from "@/theme/colors";
import { MONTH_NAMES } from "./calendarUtils";
import MonthYearPickerPanel from "./MonthYearPickerPanel";

const MIN_YEAR = 2000;

type MonthSelectorProps = {
  currentMonth: number;
  currentYear: number;
  onSelectMonth: (month: number) => void;
  onSelectYear: (year: number) => void;
};

export default function MonthSelector({ currentMonth, currentYear, onSelectMonth, onSelectYear }: MonthSelectorProps) {
  const [pickerMode, setPickerMode] = useState<"month" | "year" | null>(null);

  // A long, fixed range (not a window around the selected year) so the list
  // actually scrolls; the picker opens scrolled to the selected year.
  const thisYear = new Date().getFullYear();
  const firstYear = Math.min(MIN_YEAR, currentYear);
  const lastYear = Math.max(thisYear + 10, currentYear);
  const years = Array.from({ length: lastYear - firstYear + 1 }, (_, i) => firstYear + i);

  const close = () => setPickerMode(null);

  return (
    <View style={styles.container}>
      <Pressable
        style={styles.dropdownPill}
        onPress={() => setPickerMode((m) => (m === "month" ? null : "month"))}
        accessibilityRole="button"
        accessibilityLabel="Select month"
      >
        <AppText style={styles.dropdownPillText}>{MONTH_NAMES[currentMonth]}</AppText>
        <Ionicons name="chevron-down" size={9} color={Colors.gray500} />
      </Pressable>

      <Pressable
        style={styles.dropdownPill}
        onPress={() => setPickerMode((m) => (m === "year" ? null : "year"))}
        accessibilityRole="button"
        accessibilityLabel="Select year"
      >
        <AppText style={styles.dropdownPillText}>{currentYear}</AppText>
        <Ionicons name="chevron-down" size={9} color={Colors.gray500} />
      </Pressable>

      <MonthYearPickerPanel
        pickerMode={pickerMode}
        currentMonth={currentMonth}
        currentYear={currentYear}
        years={years}
        onSelectMonth={onSelectMonth}
        onSelectYear={onSelectYear}
        onClose={close}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    zIndex: 20,
  },
  dropdownPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.gray300,
    borderRadius: 4,
    paddingHorizontal: 4,
    paddingVertical: 1.5,
  },
  dropdownPillText: {
    fontSize: 8.5,
    color: Colors.gray800,
    fontWeight: "500",
  },
});
