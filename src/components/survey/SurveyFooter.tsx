import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  View,
} from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export type SurveyFooterProps = {
  title?: string;
  onContinue: () => void;
  disabled?: boolean;
  loading?: boolean;
};

export default function SurveyFooter({
  title = "Continue",
  onContinue,
  disabled = false,
  loading = false,
}: SurveyFooterProps) {
  const handlePress = () => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
      setTimeout(onContinue, 10);
    } else {
      onContinue();
    }
  };

  return (
    <View style={styles.footerWrapper}>
      <Pressable
        style={({ pressed }) => [
          styles.button,
          (disabled || loading) && styles.buttonDisabled,
          pressed && !disabled && styles.buttonPressed,
        ]}
        onPress={handlePress}
        disabled={disabled || loading}
        accessibilityRole="button"
        accessibilityLabel={title}
        accessibilityState={{ disabled: disabled || loading }}
      >
        {loading ? (
          <ActivityIndicator color={Colors.white} size="small" />
        ) : (
          <AppText
            style={styles.buttonText}
            color={Colors.white}
            weight={FontWeight.bold}
          >
            {title}
          </AppText>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  footerWrapper: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 14,
    backgroundColor: "#EBF3FB",
    borderTopWidth: 1,
    borderTopColor: "rgba(0, 106, 255, 0.08)",
  },
  button: {
    height: 50,
    borderRadius: 12,
    backgroundColor: "#006AFF",
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({
      x: 0,
      y: 4,
      blur: 10,
      color: "#006AFF",
      opacity: 0.25,
      elevation: 4,
    }),
  },
  buttonDisabled: {
    opacity: 0.55,
  },
  buttonPressed: {
    opacity: 0.9,
    transform: [{ scale: 0.99 }],
  },
  buttonText: {
    fontSize: 15.5,
    letterSpacing: 0.2,
  },
});
