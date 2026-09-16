import React from "react";
import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

type RecordedCardProps = {
  title?: string;
  subtitle?: string;
  color?: string;
  backgroundColor?: string;
};

export default function RecordedCard({
  title = "Recorded",
  subtitle = "Good Job !",
  color = Colors.recordedGreen,
  backgroundColor = Colors.recordedGreenBg,
}: RecordedCardProps) {
  return (
    <View style={[styles.container, { backgroundColor }]}>
      <Ionicons
        name="checkmark-circle"
        size={26}
        color={color}
      />

      <View style={styles.textWrap}>
        <AppText
          variant="label"
          color={color}
          weight={FontWeight.bold}
        >
          {title}
        </AppText>

        <AppText
          variant="tiny"
          color={color}
          weight={FontWeight.medium}
        >
          {subtitle}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 10,
  },
  textWrap: {
    gap: 1,
  },
});
