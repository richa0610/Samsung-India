import { StatusBar } from "expo-status-bar";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { Colors } from "@/theme/colors";
import { LocationDetailsCard, LocationVerifiedInfo, RadarHero } from "./location-verified";

export type { LocationVerifiedInfo } from "./location-verified";

type Props = {
  info: LocationVerifiedInfo;
  onContinue: () => void;
};

export default function LocationVerifiedView({ info, onContinue }: Props) {
  const insets = useSafeAreaInsets();

  const formattedTime =
    info.verifiedTime ||
    new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  const venueName = [info.venueLabel, info.location].find((value) => value && value !== "--");
  const subtitleText = venueName ? `${formattedTime} · ${venueName}` : `Verified at ${formattedTime}`;

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="light" animated />
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} bounces={false}>
        <RadarHero subtitleText={subtitleText} />
        <LocationDetailsCard info={info} onContinue={onContinue} />
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
});
