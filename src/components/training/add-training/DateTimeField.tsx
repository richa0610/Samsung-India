import { useState } from "react";
import { Platform, Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import DateTimePicker, { DateTimePickerAndroid } from "@react-native-community/datetimepicker";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";
import { displayDate, formatDate, formatTime } from "./formatting";

export function DateTimeField({
  label,
  value,
  mode,
  onChange,
  plain = false,
  disabled = false,
  compact = false,
  minimumDate,
}: {
  label?: string;
  value: string;
  mode: "date" | "time";
  onChange: (formatted: string) => void;
  // Attendance's Check-In/Check-Out fields render as a bare bordered box
  // with no leading icon or chevron, unlike the rest of the form's fields.
  plain?: boolean;
  disabled?: boolean;
  // Smaller height/padding for tight layouts like the sessions filter panel.
  compact?: boolean;
  // Earliest selectable date - e.g. today, so training dates can't be
  // backdated.
  minimumDate?: Date;
}) {
  const [showPicker, setShowPicker] = useState(false);

  const open = () => {
    if (disabled) return;
    if (Platform.OS === "android") {
      DateTimePickerAndroid.open({
        value: new Date(),
        mode,
        is24Hour: false,
        minimumDate,
        onChange: (_event, selected) => {
          if (selected) onChange(mode === "date" ? formatDate(selected) : formatTime(selected));
        },
      });
    } else {
      setShowPicker(true);
    }
  };

  return (
    <View style={styles.field}>
      {label && (
        <AppText style={styles.fieldLabel} weight={FontWeight.medium}>{label}</AppText>
      )}
      <Pressable
        style={[
          styles.pickerField,
          compact && styles.pickerFieldCompact,
          plain && styles.pickerFieldPlain,
          disabled && styles.pickerFieldDisabled,
        ]}
        onPress={open}
      >
        {!plain && (
          <Ionicons
            name={mode === "date" ? "calendar-outline" : "time-outline"}
            size={compact ? 14 : 16}
            color={Colors.gray600}
          />
        )}
        <AppText style={[styles.pickerFieldText, compact && styles.pickerFieldTextCompact]} color={value ? Colors.black : Colors.gray400}>
          {value ? (mode === "date" ? displayDate(value) : value) : mode === "date" ? "Select Date" : "Select Time"}
        </AppText>
        {!plain && (
          <Ionicons
            name="chevron-down"
            size={compact ? 14 : 16}
            color={Colors.gray600}
            style={styles.pickerFieldChevron}
          />
        )}
      </Pressable>

      {Platform.OS === "ios" && showPicker && (
        <View style={styles.inlinePicker}>
          <DateTimePicker
            value={new Date()}
            mode={mode}
            display="spinner"
            minimumDate={minimumDate}
            onChange={(_event, selected) => {
              if (selected) onChange(mode === "date" ? formatDate(selected) : formatTime(selected));
            }}
          />
          <Pressable style={styles.doneButton} onPress={() => setShowPicker(false)}>
            <AppText color={Colors.mainColour1} weight={FontWeight.semiBold}>Done</AppText>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { marginBottom: Spacing.lg },
  fieldLabel: { fontSize: Fonts.body, marginBottom: Spacing.sm },
  pickerField: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    height: 50,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    paddingHorizontal: Spacing.lg,
    backgroundColor: Colors.white,
  },
  pickerFieldText: { fontSize: Fonts.xs, flex: 1 },
  pickerFieldTextCompact: { fontSize: 12 },
  pickerFieldChevron: { marginLeft: -4 },
  pickerFieldCompact: { height: 38, paddingHorizontal: Spacing.md, gap: 6 },
  pickerFieldPlain: { justifyContent: "flex-start" },
  pickerFieldDisabled: { backgroundColor: Colors.gray100 },
  inlinePicker: { alignItems: "flex-end", marginTop: -Spacing.sm, marginBottom: Spacing.sm },
  doneButton: { paddingVertical: 6, paddingHorizontal: 4 },
});
