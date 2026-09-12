import React from "react";
import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

type WaitingCardProps = {
  title?: string;
  subtitle?: string;
  color?: string;
  backgroundColor?: string;
  icon?: keyof typeof Ionicons.glyphMap;
};

export default function WaitingCard({
  title = "Please Wait",
  subtitle = "Trainer will unlock soon...",
  color = Colors.headerBlue,
  backgroundColor = Colors.waitingBlueBg,
  icon = "hourglass-outline",
}: WaitingCardProps) {
  return (
    <View style={[styles.container, { backgroundColor }]}>
      <Ionicons
        name={icon}
        size={24}
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
          variant="caption"
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
    backgroundColor: Colors.waitingBlueBg,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 10,
  },
  textWrap: {
    gap: 1,
  },
});