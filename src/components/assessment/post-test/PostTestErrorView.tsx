import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontSize, FontWeight } from "@/theme/typography";

type PostTestErrorViewProps = {
  error: string | null;
  onRetry: () => void;
};

export default function PostTestErrorView({ error, onRetry }: PostTestErrorViewProps) {
  return (
    <SafeAreaView style={styles.loadingContainer}>
      <Ionicons name="alert-circle-outline" size={48} color={Colors.danger} />
      <AppText style={styles.loadingText}>{error}</AppText>
      <Pressable style={styles.retryButton} onPress={onRetry}>
        <AppText color={Colors.white} weight={FontWeight.medium}>
          Try Again
        </AppText>
      </Pressable>
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
  retryButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
});
