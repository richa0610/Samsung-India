import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

export default function SecurityFooter() {
  return (
    <View style={styles.container}>
      <View style={styles.lockIcon}>
        <Ionicons name="lock-closed-outline" size={17} color={Colors.inputColour} />
      </View>
      <AppText style={styles.text}>Your information is secure</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "center",
  },
  lockIcon: {
    width: 15,
    height: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  text: {
    color: Colors.inputColour,
    fontSize: 14,
    fontWeight: FontWeight.regular,
    marginLeft: 8,
  },
});
