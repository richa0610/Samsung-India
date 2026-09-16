import { Image, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type ResultsHeroProps = {
  screenWidth: number;
};

export default function ResultsHero({ screenWidth }: ResultsHeroProps) {
  return (
    <View style={styles.trophyWrapper}>
      <View style={styles.trophyBanner}>
        <Image
          source={require("@/assets/images/win.webp")}
          style={{ width: screenWidth, height: 133 }}
          resizeMode="contain"
        />
      </View>
      <AppText style={styles.resultsTitle} weight={FontWeight.bold}>
        Results
      </AppText>
      <AppText style={styles.resultsSubtitle}>Great attempt! Keep going and improve your score.</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  trophyWrapper: {
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
    paddingTop: 4,
    paddingBottom: 4,
  },
  trophyBanner: {
    width: "100%",
    height: 133,
    alignItems: "center",
    justifyContent: "center",
    marginHorizontal: -16,
  },
  resultsTitle: {
    fontSize: 26,
    color: "#111827",
    marginTop: 6,
  },
  resultsSubtitle: {
    fontSize: 12.5,
    color: Colors.gray600,
    textAlign: "center",
    marginTop: 3,
  },
});
