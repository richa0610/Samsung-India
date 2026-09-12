import React from "react";
import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type ProctoringHeaderProps = {
  title?: string;
  subtitle?: string;
};

export default function ProctoringHeader({
  title = "Proctoring Enabled",
  subtitle = "To ensure a fair and secure assessment, the following proctoring features will be active during your test.",
}: ProctoringHeaderProps) {
  return (
    <View style={styles.container}>
      {/* Center Shield Graphic with Decorative Dashed Lines */}
      <View style={styles.graphicRow}>
        {/* Left Dashed Line with Dots */}
        <View style={styles.dashLine}>
          <View style={styles.dot} />
          <View style={styles.smallDot} />
          <View style={styles.smallDot} />
          <View style={styles.smallDot} />
          <View style={styles.smallDot} />
          <View style={styles.dotOuter}>
            <View style={styles.dotInner} />
          </View>
        </View>

        {/* Center Shield with Camera Icon */}
        <View style={styles.shieldWrapper}>
          <View style={styles.shieldOutline}>
            <Ionicons name="camera" size={28} color="#00A859" />
          </View>
        </View>

        {/* Right Dashed Line with Dots */}
        <View style={styles.dashLine}>
          <View style={styles.dotOuter}>
            <View style={styles.dotInner} />
          </View>
          <View style={styles.smallDot} />
          <View style={styles.smallDot} />
          <View style={styles.smallDot} />
          <View style={styles.smallDot} />
          <View style={styles.dot} />
        </View>
      </View>

      {/* Title */}
      <AppText
        style={styles.title}
        color={Colors.black}
        weight={FontWeight.bold}
      >
        {title}
      </AppText>

      {/* Subtitle */}
      <AppText style={styles.subtitle} color={Colors.gray600}>
        {subtitle}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    paddingTop: 10,
    paddingBottom: 16,
  },
  graphicRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    marginBottom: 16,
    width: "100%",
  },
  dashLine: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 8,
  },
  dot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#A7F3D0",
  },
  smallDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: "#A7F3D0",
  },
  dotOuter: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: "#00A859",
    alignItems: "center",
    justifyContent: "center",
  },
  dotInner: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#00A859",
  },
  shieldWrapper: {
    alignItems: "center",
    justifyContent: "center",
  },
  shieldOutline: {
    width: 72,
    height: 80,
    borderRadius: 24,
    borderWidth: 2.5,
    borderColor: "#00A859",
    borderBottomLeftRadius: 36,
    borderBottomRightRadius: 36,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
  },
  title: {
    fontSize: 22,
    lineHeight: 28,
    textAlign: "center",
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 12.5,
    lineHeight: 18,
    textAlign: "center",
    marginTop: 6,
    paddingHorizontal: 12,
  },
});
