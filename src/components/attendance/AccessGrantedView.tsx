import { StatusBar } from "expo-status-bar";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { Breakpoints } from "@/theme/breakpoints";
import { Colors } from "@/theme/colors";
import {
  AccessGrantedDetail,
  BottomActions,
  DetailsCard,
  SuccessHero,
} from "./access-granted";

export type { AccessGrantedDetail } from "./access-granted";

type Props = {
  details: AccessGrantedDetail[];
  onContinue: () => void;
  onHome: () => void;
};

export default function AccessGrantedView({ details, onContinue, onHome }: Props) {
  const insets = useSafeAreaInsets();

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="light" animated />
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} bounces={false}>
        <SuccessHero />

        <View style={styles.content}>
          <DetailsCard details={details} />
          <BottomActions onContinue={onContinue} onHome={onHome} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.successBackground,
  },
  statusBarBackground: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.success,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: "space-between",
  },
  content: {
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    alignSelf: "center",
    paddingHorizontal: 20,
    marginTop: -205,
    flex: 1,
    justifyContent: "space-between",
    paddingBottom: 24,
  },
});
