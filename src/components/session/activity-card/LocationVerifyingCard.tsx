import { ActivityIndicator, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";

export default function LocationVerifyingCard() {
  return (
    <View style={styles.container}>
      <ActivityIndicator color={Colors.headerBlue} size="small" />

      <View style={styles.textWrap}>
        <AppText variant="label" color={Colors.headerBlue} weight={FontWeight.bold}>
          Verifying Location
        </AppText>
        <AppText variant="caption" color={Colors.headerBlue} weight={FontWeight.medium}>
          Checking you're at the venue...
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
