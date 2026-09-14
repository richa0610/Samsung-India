import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import Sparkle from "@/assets/images/svg/sparkle.svg";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

export default function SuccessHero() {
  return (
    <View style={styles.successArea}>
      <View style={styles.successHalo}>
        <Sparkle width={170} height={80} style={styles.sparkle} />
        <View style={styles.successRing}>
          <View style={styles.successCircle}>
            <Ionicons name="checkmark" size={48} color={Colors.success} />
          </View>
        </View>
      </View>

      <AppText variant="h1" color={Colors.white} weight={FontWeight.bold} align="center" style={styles.title}>
        Access Granted!
      </AppText>
      <AppText variant="label" color="rgba(255, 255, 255, 0.95)" align="center" style={styles.subtitle}>
        Your attendance is permanently recorded.
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  successArea: {
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.success,
    borderBottomLeftRadius: 40,
    borderBottomRightRadius: 40,
    paddingTop: 60,
    paddingBottom: 235,
    paddingHorizontal: 20,
  },
  successHalo: {
    width: 170,
    height: 170,
    borderRadius: 85,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255, 255, 255, 0.035)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.06)",
  },
  sparkle: { position: "absolute", top: -28, zIndex: 0 },
  successRing: {
    width: 134,
    height: 134,
    zIndex: 1,
    borderRadius: 67,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255, 255, 255, 0.07)",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
  },
  successCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 3, blur: 6, opacity: 0.08, elevation: 2 }),
  },
  title: {
    marginTop: 16,
  },
  subtitle: {
    marginTop: 4,
  },
});
