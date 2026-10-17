import { ActivityIndicator, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";

export default function SurveyLoadingView() {
  return (
    <SafeAreaView style={styles.loadingContainer}>
      <ActivityIndicator color={Colors.mainColour1} size="large" />
      <AppText style={styles.loadingText}>Loading the survey…</AppText>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    backgroundColor: "#EBF3FB",
  },
  loadingText: {
    color: Colors.gray600,
    fontSize: 14,
  },
});
