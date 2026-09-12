import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/typography";
import AttendanceBanner from "./AttendanceBanner";

type AttendanceErrorViewProps = {
  error: string | null;
  onRetry: () => void;
  onBack: () => void;
};

export default function AttendanceErrorView({ error, onRetry, onBack }: AttendanceErrorViewProps) {
  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <AttendanceBanner onBack={onBack} />
      <View style={styles.loadingContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={Colors.danger} />
        <AppText style={styles.loadingText}>{error}</AppText>
        <Pressable style={styles.retryButton} onPress={onRetry}>
          <AppText color={Colors.white} weight={FontWeight.medium}>
            Try Again
          </AppText>
        </Pressable>
        <Pressable onPress={onBack} hitSlop={8}>
          <AppText style={styles.homeText} color={Colors.gray600}>
            Go Back
          </AppText>
        </Pressable>
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
  retryButton: {
    backgroundColor: Colors.success,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 4,
  },
  homeText: { fontSize: Fonts.caption },
});
