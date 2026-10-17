import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontSize, FontWeight } from "@/theme/typography";

type SubmissionActionsProps = {
  onGoToDashboard: () => void;
};

export default function SubmissionActions({ onGoToDashboard }: SubmissionActionsProps) {
  return (
    <View style={styles.bottomSection}>
      <Pressable
        style={styles.dashboardButton}
        onPress={onGoToDashboard}
        accessibilityRole="button"
        accessibilityLabel="Go To Dashboard"
      >
        <Ionicons name="home-outline" size={20} color={Colors.white} />
        <AppText variant="label" color={Colors.white} weight={FontWeight.bold}>
          Go To Dashboard
        </AppText>
      </Pressable>

      <View style={styles.secureNotice}>
        <View style={styles.secureBadge}>
          <Ionicons name="lock-closed" size={12} color={Colors.statusGreen} />
        </View>
        <AppText style={styles.secureBadgeText} variant="caption" color={Colors.gray500} weight={FontWeight.medium}>
          Your data is secure and encrypted
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bottomSection: {
    width: "100%",
    alignItems: "center",
  },
  dashboardButton: {
    width: "100%",
    minHeight: 44,
    borderRadius: 12,
    backgroundColor: Colors.successTeal,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    ...createShadow({ x: 0, y: 3, blur: 10, opacity: 0.12, elevation: 3 }),
  },
  secureNotice: {
    marginTop: 30,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  secureBadge: {
    alignItems: "center",
    justifyContent: "center",
  },
  secureBadgeText: {
    fontSize: FontSize.caption,
  },
});
