import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { CONFETTI_ITEMS } from "./confettiItems";

export default function ConfettiHero() {
  return (
    <View style={styles.heroWrap}>
      {CONFETTI_ITEMS.map((item, index) => (
        <View
          key={index}
          style={[
            styles.confettiPiece,
            {
              top: item.top,
              bottom: item.bottom,
              left: item.left,
              right: item.right,
              backgroundColor: item.color,
              width: item.width,
              height: item.height,
              transform: [{ rotate: item.rotate }],
            },
          ]}
        />
      ))}

      <View style={styles.haloRing}>
        <View style={styles.checkCircle}>
          <Ionicons name="checkmark" size={36} color={Colors.white} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  heroWrap: {
    width: "100%",
    height: 85,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  confettiPiece: {
    position: "absolute",
    borderRadius: 2,
  },
  haloRing: {
    width: 95,
    height: 95,
    borderRadius: "50%",
    backgroundColor: "#D1FADF",
    alignItems: "center",
    justifyContent: "center",
  },
  checkCircle: {
    width: 78,
    height: 78,
    borderRadius: "50%",
    backgroundColor: "#00A86B",
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 3, blur: 8, opacity: 0.15, elevation: 3 }),
  },
});
