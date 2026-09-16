import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

type RadarHeroProps = {
  subtitleText: string;
};

export default function RadarHero({ subtitleText }: RadarHeroProps) {
  return (
    <View style={styles.heroArea}>
      <View style={styles.radarWrapper}>
        <View style={styles.radarOuterRing}>
          <View style={styles.radarMidRing}>
            <View style={styles.radarInnerRing}>
              <View style={styles.radarCenterCircle}>
                <Ionicons name="location-sharp" size={48} color="#00A86B" />
              </View>
            </View>
          </View>
        </View>
      </View>

      <AppText color={Colors.white} weight={FontWeight.semiBold} align="center" style={styles.title}>
        LOCATION VERIFIED
      </AppText>
      <AppText color="rgba(255, 255, 255, 0.95)" weight={FontWeight.medium} align="center" style={styles.subtitle}>
        {subtitleText}
      </AppText>

      <View style={styles.pillDivider} />
    </View>
  );
}

const styles = StyleSheet.create({
  heroArea: {
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.success,
    borderBottomLeftRadius: 40,
    borderBottomRightRadius: 40,
    paddingTop: 24,
    paddingBottom: 250,
    paddingHorizontal: 20,
  },
  radarWrapper: {
    width: 213,
    height: 213,
    alignItems: "center",
    justifyContent: "center",
  },
  radarOuterRing: {
    width: 213,
    height: 213,
    borderRadius: 106.5,
    backgroundColor: "rgba(255, 255, 255, 0.08)",
    alignItems: "center",
    justifyContent: "center",
  },
  radarMidRing: {
    width: 168,
    height: 168,
    borderRadius: 84,
    backgroundColor: "rgba(255, 255, 255, 0.12)",
    alignItems: "center",
    justifyContent: "center",
  },
  radarInnerRing: {
    width: 138,
    height: 138,
    borderRadius: 69,
    backgroundColor: "rgba(255, 255, 255, 0.20)",
    alignItems: "center",
    justifyContent: "center",
  },
  radarCenterCircle: {
    width: 104,
    height: 104,
    borderRadius: 52,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 3, blur: 6, opacity: 0.08, elevation: 2 }),
  },
  title: {
    marginTop: 18,
    letterSpacing: 0.5,
    fontSize: 29,
  },
  subtitle: {
    marginTop: 4,
    fontSize: 15,
  },
  pillDivider: {
    width: 60,
    height: 3,
    borderRadius: 2,
    backgroundColor: "rgba(255, 255, 255, 0.85)",
    marginTop: 12,
  },
});
