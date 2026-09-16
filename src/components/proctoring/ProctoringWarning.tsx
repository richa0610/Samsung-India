import React from "react";
import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { FontWeight } from "@/theme/fontWeight";

export type ProctoringWarningProps = {
  title?: string;
  message?: string;
};

export default function ProctoringWarning({
  title = "Important",
  message = "if any suspicious activity is detected, it may result in termination of the test and appropriate action.",
}: ProctoringWarningProps) {
  return (
    <View style={styles.container}>
      <View style={styles.iconCircle}>
        <Ionicons name="lock-closed" size={18} color="#008744" />
      </View>
      <View style={styles.textColumn}>
        <AppText style={styles.title} weight={FontWeight.bold}>
          {title}
        </AppText>
        <AppText style={styles.message}>
          {message}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    backgroundColor: "#EBFBF2",
    borderRadius: 14,
    padding: 12,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#C6F2DE",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },
  textColumn: {
    flex: 1,
    gap: 2,
  },
  title: {
    fontSize: 13.5,
    color: "#111827",
  },
  message: {
    fontSize: 11,
    lineHeight: 16,
    color: "#4B5563",
  },
});
