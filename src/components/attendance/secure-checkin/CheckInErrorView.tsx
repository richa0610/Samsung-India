import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Fonts } from "@/theme/fonts";

type CheckInErrorViewProps = {
  errorMessage: string;
  isBlocked: boolean;
  onOpenSettings: () => void;
  onRetry: () => void;
  onBack: () => void;
};

export default function CheckInErrorView({ errorMessage, isBlocked, onOpenSettings, onRetry, onBack }: CheckInErrorViewProps) {
  return (
    <SafeAreaView style={styles.loadingContainer}>
      <Ionicons name="alert-circle-outline" size={48} color={Colors.danger} />
      <AppText style={styles.loadingText}>{errorMessage}</AppText>

      <View style={styles.errorActions}>
        {isBlocked ? (
          <Pressable style={styles.primaryButton} onPress={onOpenSettings}>
            <Ionicons name="settings-outline" size={16} color={Colors.white} />
            <AppText color={Colors.white} weight={FontWeight.medium}>
              Open Device Settings
            </AppText>
          </Pressable>
        ) : (
          <Pressable style={styles.primaryButton} onPress={onRetry}>
            <Ionicons name="refresh" size={16} color={Colors.white} />
            <AppText color={Colors.white} weight={FontWeight.medium}>
              Allow Location & Try Again
            </AppText>
          </Pressable>
        )}

        <Pressable style={styles.backLink} onPress={onBack} hitSlop={8}>
          <AppText style={styles.homeText} color={Colors.gray600}>
            Go Back
          </AppText>
        </Pressable>
      </View>
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
  errorActions: {
    width: "100%",
    maxWidth: 280,
    alignItems: "center",
    gap: 12,
    marginTop: 8,
  },
  primaryButton: {
    width: "100%",
    backgroundColor: Colors.recordedGreen,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
  },
  backLink: { paddingVertical: 6 },
  homeText: { fontSize: Fonts.caption },
});
