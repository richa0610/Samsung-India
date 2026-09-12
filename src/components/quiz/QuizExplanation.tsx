import React from "react";
import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type QuizExplanationProps = {
  explanation?: string | null;
};

export default function QuizExplanation({
  explanation = "The Galaxy S26 is not equipped with the Exynos 2600. It uses the Snapdragon 8 Gen 4 Chipset.",
}: QuizExplanationProps) {
  if (!explanation) return null;

  return (
    <View style={styles.container}>
      {/* Green circular icon */}
      <View style={styles.iconCircle}>
        <Ionicons name="information-circle" size={22} color={Colors.white} />
      </View>

      {/* Explanation Text */}
      <View style={styles.textWrap}>
        <AppText
          style={styles.title}
          color={Colors.recordedGreen}
          weight={FontWeight.bold}
        >
          Explanation
        </AppText>
        <AppText style={styles.bodyText} weight={FontWeight.medium}>
          {explanation}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    maxWidth: "100%",
    backgroundColor: "#D8F3E5",
    borderRadius: 14,
    padding: 13,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    marginTop: 14,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.recordedGreen,
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  textWrap: {
    flex: 1,
    gap: 3,
  },
  title: {
    fontSize: 14,
  },
  bodyText: {
    fontSize: 12,
    lineHeight: 17,
    color: "#1F2937",
  },
});
