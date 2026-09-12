import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { Colors } from "@/theme/colors";
import { MONTH_NAMES } from "./calendarUtils";
import MonthYearPickerPanel from "./MonthYearPickerPanel";

type MonthSelectorProps = {
  currentMonth: number;
  currentYear: number;
  onSelectMonth: (month: number) => void;
  onSelectYear: (year: number) => void;
};

export default function MonthSelector({ currentMonth, currentYear, onSelectMonth, onSelectYear }: MonthSelectorProps) {
  const [pickerMode, setPickerMode] = useState<"month" | "year" | null>(null);

  const years = Array.from({ length: 11 }, (_, i) => currentYear - 5 + i);

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
        <Ionicons name="chevron-down" size={9} color="#6B7280" />
      </Pressable>

      <Pressable
        style={styles.dropdownPill}
        onPress={() => setPickerMode((m) => (m === "year" ? null : "year"))}
        accessibilityRole="button"
        accessibilityLabel="Select year"
      >
        <AppText style={styles.dropdownPillText}>{currentYear}</AppText>
        <Ionicons name="chevron-down" size={9} color="#6B7280" />
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
    borderColor: "#D1D5DB",
    borderRadius: 4,
    paddingHorizontal: 4,
    paddingVertical: 1.5,
  },
  dropdownPillText: {
    fontSize: 8.5,
    color: "#1F2937",
    fontWeight: "500",
  },
});
