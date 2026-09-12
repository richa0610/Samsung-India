import React, { useState } from "react";
import {
  Pressable,
  StyleSheet,
  TextInput,
  View,
  TextInputProps,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "./AppText";
import { Colors } from "@/theme/colors";
import { APP_FONT_FAMILY } from "@/theme/fontFamily";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/typography";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";

interface AppInputProps extends TextInputProps {
  label?: string;
  caption?: string;
  icon?: keyof typeof Ionicons.glyphMap;
  // Smaller height/padding for tight layouts like dense multi-field forms.
  compact?: boolean;
}

export default function AppInput({
  label,
  caption,
  icon,
  compact = false,
  style,
  secureTextEntry,
  ...props
}: AppInputProps) {
  // Any password field gets a show/hide eye toggle for free.
  const isPassword = !!secureTextEntry;
  const [hidden, setHidden] = useState(true);

  return (
    <View style={styles.container}>
      {label && (
        <AppText size={Fonts.body} weight={FontWeight.medium} color={Colors.black} style={styles.label}>
          {label}
        </AppText>
      )}

      <View style={styles.inputRow}>
        {icon && <Ionicons name={icon} size={compact ? 14 : 16} color={Colors.gray600} style={styles.icon} />}
        <TextInput
          style={[
            styles.input,
            compact && styles.inputCompact,
            icon && styles.inputWithIcon,
            isPassword && styles.inputWithTrailing,
            props.editable === false && styles.inputDisabled,
            style,
          ]}
          placeholderTextColor={Colors.gray400}
          secureTextEntry={isPassword && hidden}
          {...props}
        />
        {isPassword && (
          <Pressable
            style={styles.trailingBtn}
            onPress={() => setHidden((v) => !v)}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={hidden ? "Show password" : "Hide password"}
          >
            <Ionicons
              name={hidden ? "eye-off-outline" : "eye-outline"}
              size={compact ? 16 : 18}
              color={Colors.gray600}
            />
          </Pressable>
        )}
      </View>

      {caption && (
        <AppText variant="overline" color={Colors.gray600} style={styles.caption}>
          {caption}
        </AppText>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    marginBottom: Spacing.lg,
  },
  label: {
    marginBottom: Spacing.sm,
  },

  inputRow: {
    flexDirection: "row",
    alignItems: "center",
  },

  icon: {
    position: "absolute",
    left: Spacing.lg,
    zIndex: 1,
  },

  input: {
    flex: 1,
    height: 50,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    paddingHorizontal: Spacing.lg,
    fontSize: Fonts.body,
    backgroundColor: Colors.white,
    fontFamily: APP_FONT_FAMILY,
    includeFontPadding: false,
  },

  inputCompact: {
    height: 38,
    paddingHorizontal: Spacing.md,
    fontSize: Fonts.xs,
  },

  inputWithIcon: {
    paddingLeft: Spacing.lg + 16 + 8,
  },

  inputWithTrailing: {
    paddingRight: Spacing.lg + 18 + 8,
  },

  trailingBtn: {
    position: "absolute",
    right: Spacing.lg,
    height: "100%",
    justifyContent: "center",
    zIndex: 1,
  },

  inputDisabled: {
    backgroundColor: Colors.gray100,
    color: Colors.gray600,
  },

  caption: {
    marginTop: Spacing.sm,
  },
});
