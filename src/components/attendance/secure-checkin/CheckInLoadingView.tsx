import { ActivityIndicator, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";

type CheckInLoadingViewProps = {
  step: "locating" | "submitting";
};

export default function CheckInLoadingView({ step }: CheckInLoadingViewProps) {
  return (
    <SafeAreaView style={styles.loadingContainer}>
      <ActivityIndicator color={Colors.recordedGreen} size="large" />
      <AppText style={styles.loadingText}>
        {step === "locating" ? "Verifying your location…" : "Submitting your check-in…"}
      </AppText>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 14,
    paddingHorizontal: 24,
    backgroundColor: Colors.background,
  },
  loadingText: {
    fontSize: Fonts.body,
    color: Colors.gray600,
    textAlign: "center",
    lineHeight: 22,
  },
});
