import React from "react";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type SurveyRadioOptionProps = {
  id: string;
  text: string;
  selected: boolean;
  onSelect: () => void;
};

export default function SurveyRadioOption({
  text,
  selected,
  onSelect,
}: SurveyRadioOptionProps) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.option,
        selected && styles.optionSelected,
        pressed && styles.optionPressed,
      ]}
      onPress={onSelect}
      accessibilityRole="radio"
      accessibilityState={{ selected }}
    >
      <View style={[styles.radio, selected && styles.radioSelected]}>
        {selected && <View style={styles.radioDot} />}
      </View>
      <AppText
        style={[styles.optionText, selected && styles.optionTextSelected]}
        weight={selected ? FontWeight.semiBold : FontWeight.regular}
      >
        {text}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  option: {
    minHeight: 46,
    borderWidth: 1.2,
    borderColor: "#E5E7EB",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: Colors.white,
  },
  optionSelected: {
    borderColor: "#006AFF",
    backgroundColor: "#F0F6FF",
  },
  optionPressed: {
    opacity: 0.85,
  },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: "#D1D5DB",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
  },
  radioSelected: {
    borderColor: "#006AFF",
  },
  radioDot: {
    width: 11,
    height: 11,
    borderRadius: 5.5,
    backgroundColor: "#006AFF",
  },
  optionText: {
    flex: 1,
    fontSize: 13.5,
    lineHeight: 19,
    color: "#1F2937",
  },
  optionTextSelected: {
    color: "#006AFF",
  },
});
