import { ActivityIndicator, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import AttendanceBanner from "./AttendanceBanner";

type AttendanceCheckingInViewProps = {
  onBack: () => void;
};

export default function AttendanceCheckingInView({ onBack }: AttendanceCheckingInViewProps) {
  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <AttendanceBanner onBack={onBack} />
      <View style={styles.loadingContainer}>
        <ActivityIndicator color={Colors.success} size="large" />
        <AppText style={styles.loadingText}>Marking your attendance…</AppText>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingHorizontal: 24,
  },
  loadingText: {
    fontSize: Fonts.body,
    color: Colors.gray600,
    textAlign: "center",
  },
});
