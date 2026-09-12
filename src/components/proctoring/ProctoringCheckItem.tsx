import React from "react";
import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

export type ProctoringCheckItemData = {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  description: string;
  checked?: boolean;
};

export type ProctoringCheckItemProps = {
  item: ProctoringCheckItemData;
};

export default function ProctoringCheckItem({ item }: ProctoringCheckItemProps) {
  const isChecked = item.checked ?? true;

  return (
    <View style={styles.container}>
      {/* Mint Icon Box */}
      <View style={styles.iconBox}>
        <Ionicons name={item.icon} size={20} color="#00A859" />
      </View>

      {/* Title & Description Column */}
      <View style={styles.textColumn}>
        <AppText
          style={styles.title}
          color={Colors.black}
          weight={FontWeight.bold}
        >
          {item.title}
        </AppText>
        <AppText style={styles.description} color={Colors.gray600}>
          {item.description}
        </AppText>
      </View>

      {/* Right Success Checkmark */}
      {isChecked && (
        <View style={styles.checkCircle}>
          <Ionicons name="checkmark" size={14} color={Colors.white} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    gap: 12,
  },
  iconBox: {
    width: 42,
    height: 42,
    borderRadius: 10,
    backgroundColor: "#D4F4E4",
    alignItems: "center",
    justifyContent: "center",
  },
  textColumn: {
    flex: 1,
    gap: 2,
  },
  title: {
    fontSize: 13.5,
    lineHeight: 18,
  },
  description: {
    fontSize: 11,
    lineHeight: 15,
  },
  checkCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "#00A859",
    alignItems: "center",
    justifyContent: "center",
  },
});
