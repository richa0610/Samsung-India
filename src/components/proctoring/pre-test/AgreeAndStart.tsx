import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";

type AgreeAndStartProps = {
  onStart: () => void;
};

export default function AgreeAndStart({ onStart }: AgreeAndStartProps) {
  const [agreed, setAgreed] = useState(false);

  return (
    <>
      <Pressable style={styles.agreeRow} onPress={() => setAgreed((v) => !v)} hitSlop={8}>
        <View style={[styles.checkbox, agreed && styles.checkboxChecked]}>
          {agreed && <Ionicons name="checkmark" size={13} color={Colors.white} />}
        </View>
        <AppText style={styles.agreeText}>I understand the instructions.</AppText>
      </Pressable>

      <Pressable style={[styles.startButton, !agreed && styles.startButtonDisabled]} disabled={!agreed} onPress={onStart}>
        <Ionicons name="play" size={16} color={Colors.white} />
        <AppText color={Colors.white} weight={FontWeight.semiBold}>
          Start Test
        </AppText>
      </Pressable>
    </>
  );
}

const styles = StyleSheet.create({
  agreeRow: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 4 },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.gray400,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: { backgroundColor: Colors.mainColour1, borderColor: Colors.mainColour1 },
  agreeText: { fontSize: Fonts.bodySm },
  startButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: Colors.mainColour1,
    borderRadius: Radius.xxl,
    height: 52,
    marginTop: 4,
  },
  startButtonDisabled: { opacity: 0.5 },
});
