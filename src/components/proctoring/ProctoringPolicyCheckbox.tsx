import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type ProctoringPolicyCheckboxProps = {
  checked: boolean;
  onChange?: (checked: boolean) => void;
  onToggle?: () => void;
  onPolicyPress?: () => void;
};

export default function ProctoringPolicyCheckbox({
  checked,
  onChange,
  onToggle,
  onPolicyPress,
}: ProctoringPolicyCheckboxProps) {
  const handleToggle = () => {
    if (onChange) {
      onChange(!checked);
    } else if (onToggle) {
      onToggle();
    }
  };

  return (
    <View style={styles.container}>
      <Pressable
        style={styles.pressableRow}
        onPress={handleToggle}
        hitSlop={8}
        accessibilityRole="checkbox"
        accessibilityState={{ checked }}
        accessibilityLabel="I have read and agree to the proctoring policy"
      >
        <View style={[styles.checkbox, checked && styles.checkboxChecked]}>
          {checked && (
            <Ionicons name="checkmark" size={13} color={Colors.white} />
          )}
        </View>

        <AppText style={styles.label}>
          I have read and agree to the{" "}
          <AppText
            style={styles.policyLink}
            weight={FontWeight.semiBold}
            onPress={onPolicyPress ?? handleToggle}
          >
            proctoring policy.
          </AppText>
        </AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 2,
  },
  pressableRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: "#9CA3AF",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
  },
  checkboxChecked: {
    backgroundColor: "#00A859",
    borderColor: "#00A859",
  },
  label: {
    fontSize: 11.5,
    color: "#374151",
    flex: 1,
  },
  policyLink: {
    color: "#006AFF",
  },
});
