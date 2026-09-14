import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import { Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import ProctoringCheckList, {
  DEFAULT_PROCTORING_CHECKS,
} from "./ProctoringCheckList";
import ProctoringHeader from "./ProctoringHeader";
import ProctoringPolicyCheckbox from "./ProctoringPolicyCheckbox";
import ProctoringWarning from "./ProctoringWarning";
import StartTestButton from "./StartTestButton";

export type ProctoringScreenProps = {
  onStartTest: () => void;
  onPolicyPress?: () => void;
  loading?: boolean;
  error?: string | null;
};

export default function ProctoringScreen({
  onStartTest,
  onPolicyPress,
  loading = false,
  error = null,
}: ProctoringScreenProps) {
  const [agreed, setAgreed] = useState(false);

  const handleStartPress = () => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
    }
    onStartTest();
  };

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <StatusBar style="dark" />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        bounces={false}
      >
        <View style={styles.mainCard}>
          {/* Top Section: Header + Checklist */}
          <View style={styles.topSection}>
            {/* Header with Camera Graphic */}
            <ProctoringHeader />

            {/* Checklist of Proctoring Features */}
            <ProctoringCheckList checks={DEFAULT_PROCTORING_CHECKS} />
          </View>

          {/* Bottom Section: Agreement + Warning + CTA Button */}
          <View style={styles.bottomSection}>
            {/* Privacy & Policy Agreement Checkbox */}
            <ProctoringPolicyCheckbox
              checked={agreed}
              onToggle={() => setAgreed(!agreed)}
              onPolicyPress={onPolicyPress}
            />

            {/* Critical Warning Box */}
            <ProctoringWarning />

            {/* Error Message if camera failed */}
            {error && (
              <View style={styles.errorBox}>
                <Ionicons name="alert-circle" size={16} color={Colors.danger} />
                <AppText
                  style={styles.errorText}
                  color={Colors.danger}
                  weight={FontWeight.medium}
                >
                  {error}
                </AppText>
              </View>
            )}

            {/* Start Test CTA Button */}
            <StartTestButton
              title="I'm ready, Start Test"
              onPress={handleStartPress}
              disabled={!agreed}
              loading={loading}
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F4F8FA",
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 12,
  },
  mainCard: {
    flex: 1,
    width: "100%",
    backgroundColor: Colors.white,
    borderRadius: 24,
    paddingHorizontal: 18,
    paddingTop: 14,
    paddingBottom: 16,
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 4, blur: 12, opacity: 0.06, elevation: 3 }),
  },
  topSection: {
    width: "100%",
  },
  bottomSection: {
    width: "100%",
    gap: 12,
    marginTop: 12,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#FEE2E2",
    borderRadius: 8,
    padding: 10,
  },
  errorText: {
    fontSize: 12,
    flex: 1,
  },
});
