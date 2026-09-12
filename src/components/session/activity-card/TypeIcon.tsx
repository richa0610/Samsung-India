import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import { Colors } from "@/theme/colors";

type TypeIconProps = {
  isAttendance: boolean;
  isQuiz: boolean;
};

export default function TypeIcon({ isAttendance, isQuiz }: TypeIconProps) {
  if (isAttendance) {
    return (
      <View style={[styles.typeIconWrap, { backgroundColor: "#D4F4E4" }]}>
        <Ionicons name="person" size={13} color={Colors.recordedGreen} />
      </View>
    );
  }

  return (
    <View style={[styles.typeIconWrap, { backgroundColor: "#DDEEFF" }]}>
      <Ionicons name={isQuiz ? "alarm" : "document-text"} size={13} color={Colors.headerBlue} />
    </View>
  );
}

const styles = StyleSheet.create({
  typeIconWrap: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
});
