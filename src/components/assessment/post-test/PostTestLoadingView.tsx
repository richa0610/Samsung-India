import { ActivityIndicator, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontSize } from "@/theme/typography";

export default function PostTestLoadingView() {
  return (
    <SafeAreaView style={styles.loadingContainer}>
      <ActivityIndicator color={Colors.primary} size="large" />
      <AppText style={styles.loadingText}>Loading the test…</AppText>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingHorizontal: 24,
  },
  loadingText: {
    fontSize: FontSize.label,
    color: Colors.gray600,
    textAlign: "center",
  },
});
