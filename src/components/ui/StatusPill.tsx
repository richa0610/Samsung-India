import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";
import { Radius } from "@/theme/radius";

export type StatusTone = "success" | "warning" | "danger" | "neutral";

const TONE_BACKGROUND: Record<StatusTone, string> = {
  success: Colors.success,
  warning: Colors.pendingColour,
  danger: Colors.danger,
  neutral: Colors.gray100,
};

const TONE_TEXT: Record<StatusTone, string> = {
  success: Colors.white,
  warning: Colors.white,
  danger: Colors.white,
  neutral: Colors.gray600,
};

export function StatusPill({ label, tone }: { label: string; tone: StatusTone }) {
  return (
    <View style={[styles.pill, { backgroundColor: TONE_BACKGROUND[tone] }]}>
      <AppText
        variant="overline"
        size={8}
        color={TONE_TEXT[tone]}
        weight={FontWeight.semiBold}
        align="center"
      >
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    alignSelf: "center",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: Radius.md,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
});
