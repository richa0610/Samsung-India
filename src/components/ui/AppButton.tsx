import React from "react";
import {
  Pressable,
  StyleSheet,
  ActivityIndicator,
  StyleProp,
  ViewStyle,
  TextStyle,
  View,
} from "react-native";

import AppText from "./AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";
import { FontWeight } from "@/theme/typography";

type AppButtonProps = {
  title: string;
  onPress: () => void;

  loading?: boolean;
  disabled?: boolean;

  buttonStyle?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
};

export default function AppButton({
  title,
  onPress,
  loading = false,
  disabled = false,
  buttonStyle,
  textStyle,
  leftIcon,
  rightIcon,
}: AppButtonProps) {
  const handlePress = () => {
    if (typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
      setTimeout(onPress, 10);
    } else {
      onPress();
    }
  };

  return (
    <Pressable
      onPress={handlePress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.button,
        pressed && styles.pressed,
        (disabled || loading) && styles.disabled,
        buttonStyle,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={Colors.white} />
      ) : (
        <View style={styles.content}>
          {leftIcon}

          <AppText
            variant="body"
            weight={FontWeight.medium}
            color={Colors.white}
            style={[styles.text, textStyle]}
          >
            {title}
          </AppText>

          {rightIcon}
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: Colors.mainColour1,
    height: 52,
    borderRadius: Radius.xxl,
    justifyContent: "center",
    alignItems: "center",
  },

  pressed: {
    opacity: 0.8,
  },

  disabled: {
    opacity: 0.5,
  },

  text: {
    color: Colors.white,
  },
  content: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: Spacing.sm,
  },
});
