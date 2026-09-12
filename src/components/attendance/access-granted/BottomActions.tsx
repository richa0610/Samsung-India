import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

type BottomActionsProps = {
  onContinue: () => void;
  onHome: () => void;
};

export default function BottomActions({ onContinue, onHome }: BottomActionsProps) {
  return (
    <View style={styles.bottomActions}>
      <Pressable
        style={styles.continueButton}
        onPress={onContinue}
        accessibilityRole="button"
        accessibilityLabel="Great, Continue"
      >
        <AppText variant="h3" color={Colors.white} weight={FontWeight.bold}>
          Great, Continue
        </AppText>
      </Pressable>

      <Pressable style={styles.homeLink} onPress={onHome} accessibilityRole="button" accessibilityLabel="Back to Home" hitSlop={8}>
        <Ionicons name="home-outline" size={15} color={Colors.success} />
        <AppText variant="caption" color={Colors.success} weight={FontWeight.semiBold}>
          Back to Home
        </AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  bottomActions: {
    width: "100%",
    alignItems: "center",
    gap: 10,
    marginTop: 20,
  },
  continueButton: {
    width: "100%",
    height: 52,
    borderRadius: 12,
    backgroundColor: "#00A86B",
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 4, blur: 10, opacity: 0.12, elevation: 3 }),
  },
  homeLink: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 4,
  },
});
