import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet } from "react-native";
import AppText from "@/components/ui/AppText";

import AppModal from "@/components/ui/AppModal";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { MONTH_NAMES } from "./calendarUtils";

type MonthYearPickerPanelProps = {
  pickerMode: "month" | "year" | null;
  currentMonth: number;
  currentYear: number;
  years: number[];
  onSelectMonth: (month: number) => void;
  onSelectYear: (year: number) => void;
  onClose: () => void;
};

export default function MonthYearPickerPanel({
  pickerMode,
  currentMonth,
  currentYear,
  years,
  onSelectMonth,
  onSelectYear,
  onClose,
}: MonthYearPickerPanelProps) {
  return (
    // A bottom-sheet AppModal (native Modal underneath) rather than an
    // absolutely-positioned View nested inside the dashboard's outer
    // ScrollView - a same-direction nested ScrollView never scrolls
    // reliably there, since the outer one wins the touch responder.
    <AppModal
      visible={pickerMode !== null}
      onClose={onClose}
      position="bottom"
      title={pickerMode === "month" ? "Select Month" : "Select Year"}
      showCloseButton
      contentStyle={styles.sheet}
    >
      <ScrollView style={styles.modalList} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        {pickerMode === "month" &&
          MONTH_NAMES.map((name, index) => {
            const isSelected = currentMonth === index;
            return (
              <Pressable
                key={name}
                style={[styles.modalOption, isSelected && styles.modalOptionSelected]}
                onPress={() => {
                  onSelectMonth(index);
                  onClose();
                }}
              >
                <AppText style={[styles.modalOptionText, isSelected && styles.modalOptionTextSelected]}>{name}</AppText>
                {isSelected && <Ionicons name="checkmark" size={14} color={Colors.mainColour1} />}
              </Pressable>
            );
          })}

        {pickerMode === "year" &&
          years.map((year) => {
            const isSelected = currentYear === year;
            return (
              <Pressable
                key={year}
                style={[styles.modalOption, isSelected && styles.modalOptionSelected]}
                onPress={() => {
                  onSelectYear(year);
                  onClose();
                }}
              >
                <AppText style={[styles.modalOptionText, isSelected && styles.modalOptionTextSelected]}>{year}</AppText>
                {isSelected && <Ionicons name="checkmark" size={14} color={Colors.mainColour1} />}
              </Pressable>
            );
          })}
      </ScrollView>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: {
    paddingHorizontal: 10,
    paddingTop: 4,
    paddingBottom: 20,
  },
  modalList: {
    maxHeight: 360,
  },
  modalOption: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: Radius.sm,
  },
  modalOptionSelected: {
    backgroundColor: "#EFF6FF",
  },
  modalOptionText: {
    fontSize: 11,
    color: "#374151",
  },
  modalOptionTextSelected: {
    color: Colors.mainColour1,
    fontWeight: "700",
  },
});
