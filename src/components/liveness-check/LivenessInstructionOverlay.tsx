import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import type { LivenessStep } from "./types";

type LivenessInstructionOverlayProps = {
  step: LivenessStep;
  instruction: string;
  detectorError: string | null;
  onRetry: () => void;
};

const ICONS: Partial<Record<LivenessStep, keyof typeof Ionicons.glyphMap>> = {
  NO_FACE: "scan-outline",
  MULTIPLE_FACES: "people-outline",
  POSITIONING: "scan-outline",
  LOOK_STRAIGHT: "eye-outline",
  MOVE_HEAD: "sync-outline",
  VERIFIED: "checkmark-circle",
  TIMED_OUT: "alert-circle",
};

/** Sits on top of the live camera preview during useFaceLivenessGate - shows the current instruction, a spinner while checking, and a retry action on timeout/error. */
export default function LivenessInstructionOverlay({ step, instruction, detectorError, onRetry }: LivenessInstructionOverlayProps) {
  const isTimedOut = step === "TIMED_OUT";
  const isVerified = step === "VERIFIED";

  return (
    <View style={styles.container} pointerEvents="box-none">
      <View style={[styles.badge, isVerified && styles.badgeSuccess, isTimedOut && styles.badgeError]}>
        {!isVerified && !isTimedOut && <ActivityIndicator size="small" color={Colors.white} style={styles.spinner} />}
        <Ionicons name={ICONS[step] ?? "scan-outline"} size={16} color={Colors.white} />
        <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.text} numberOfLines={2}>
          {instruction}
        </AppText>
      </View>

      {detectorError && (
        <View style={styles.errorBanner}>
          <AppText color={Colors.white} style={styles.errorText}>
            {detectorError}
          </AppText>
        </View>
      )}

      {isTimedOut && (
        <Pressable style={styles.retryButton} onPress={onRetry} accessibilityRole="button" accessibilityLabel="Retry verification">
          <Ionicons name="refresh" size={16} color={Colors.white} />
          <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.retryText}>
            Try Again
          </AppText>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "flex-end",
    padding: 12,
    gap: 8,
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "rgba(17, 24, 39, 0.82)",
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    maxWidth: "100%",
  },
  badgeSuccess: { backgroundColor: "rgba(5, 150, 105, 0.9)" },
  badgeError: { backgroundColor: "rgba(220, 38, 38, 0.9)" },
  spinner: { marginRight: 2 },
  text: { fontSize: 13, flexShrink: 1 },
  errorBanner: {
    backgroundColor: "rgba(220, 38, 38, 0.85)",
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  errorText: { fontSize: 11, textAlign: "center" },
  retryButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#0066FF",
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  retryText: { fontSize: 14 },
});
