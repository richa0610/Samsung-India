import React from "react";
import { StyleSheet, View } from "react-native";
import { Picker } from "@react-native-picker/picker";

import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

interface AppSelectProps {
  selectedValue: string;
  onValueChange: (value: string) => void;
  items: {
    label: string;
    value: string;
  }[];
  // When false the picker is greyed out and can't be opened - used by
  // Edit Profile to lock fields that already have a saved value.
  enabled?: boolean;
}

export default function AppSelect({
  selectedValue,
  onValueChange,
  items,
  enabled = true,
}: AppSelectProps) {
  return (
    <View style={[styles.container, !enabled && styles.containerDisabled]}>
      <Picker
        selectedValue={selectedValue}
        onValueChange={onValueChange}
        enabled={enabled}
        style={styles.picker}
      >
        {items.map((item) => (
          <Picker.Item
            key={item.value}
            label={item.label}
            value={item.value}
            style={styles.item}
          />
        ))}
      </Picker>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    height: 50,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: 10,
    overflow: "hidden",
    backgroundColor: Colors.white,
    justifyContent: "center",
  },

  containerDisabled: {
    backgroundColor: Colors.gray100,
  },

  picker: {
    width: "100%",
    color: Colors.black,
    fontSize: Fonts.bodySm,
    backgroundColor: Colors.white,
    fontWeight: FontWeight.regular,
  },
  item: {
    color: Colors.black,
    fontSize: Fonts.bodySm,
    fontWeight: FontWeight.regular,
  },
});
