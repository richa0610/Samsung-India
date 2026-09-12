import React from "react";
import { ActivityIndicator, Platform, Pressable, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export type StartTestButtonProps = {
  title?: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
};

export default function StartTestButton({
  title = "I'm ready, Start Test",
  onPress,
  disabled = false,
  loading = false,
}: StartTestButtonProps) {
  const handlePress = () => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
      // Defer state update by one tick so blur fully executes before
      // ProctoringScreen unmounts — prevents aria-hidden focus warning.
      setTimeout(onPress, 10);
    } else {
      onPress();
    }
  };

  return (
    <Pressable
      style={({ pressed }) => [
        styles.button,
        (disabled || loading) && styles.disabledButton,
        pressed && !disabled && styles.pressed,
      ]}
      disabled={disabled || loading}
      onPress={handlePress}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled: disabled || loading }}
    >
      {loading ? (
        <ActivityIndicator color={Colors.white} size="small" />
      ) : (
        <>
          <Ionicons
            name="shield-checkmark-outline"
            size={20}
            color={Colors.white}
          />
          <AppText
            style={styles.buttonText}
            color={Colors.white}
            weight={FontWeight.bold}
          >
            {title}
          </AppText>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    height: 52,
    borderRadius: 14,
    backgroundColor: "#00A859",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    ...createShadow({
      x: 0,
      y: 3,
      blur: 6,
      color: "#00A859",
      opacity: 0.2,
      elevation: 3,
    }),
  },
  disabledButton: {
    opacity: 0.45,
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.99 }],
  },
  buttonText: {
    fontSize: 15,
    letterSpacing: 0.2,
  },
});
