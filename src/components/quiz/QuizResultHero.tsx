import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

export type QuizResultType = "correct" | "incorrect" | "timeout";

export type QuizResultHeroProps = {
  type: QuizResultType;
  title?: string;
  subtitle?: string;
};

export default function QuizResultHero({
  type,
  title,
  subtitle,
}: QuizResultHeroProps) {
  const isCorrect = type === "correct";
  const isIncorrect = type === "incorrect";
  const isTimeout = type === "timeout";

  const defaultTitle = isCorrect
    ? "Correct!"
    : isIncorrect
      ? "Incorrect!"
      : "Time's Up!";

  const defaultSubtitle = isCorrect
    ? "Great Job! You selected the right answer"
    : isIncorrect
      ? "Oops! That's not the right answer"
      : "Better luck next time! Keep practicing\nto improve your score";

  const heroColor = isCorrect
    ? Colors.recordedGreen
    : isIncorrect
      ? Colors.danger
      : "#FF3B30";

  return (
    <View style={styles.container}>
      {/* Visual Graphic with Confetti */}
      <View style={styles.graphicWrapper}>
        {/* Confetti Particles */}
        {!isTimeout && (
          <>
            <View style={[styles.particle, styles.particle1]} />
            <View style={[styles.particle, styles.particle2]} />
            <View style={[styles.particle, styles.particle3]} />
            <View style={[styles.particle, styles.particle4]} />
            <View style={[styles.particle, styles.particle5]} />
            <View style={[styles.particle, styles.particle6]} />
          </>
        )}

        {isTimeout ? (
          /* Ringing Alarm Clock Visual */
          <View style={styles.alarmWrapper}>
            <View style={styles.lightningLeft}>
              <Ionicons name="flash" size={16} color="#FF3B30" />
            </View>
            <View style={styles.alarmCircle}>
              <Ionicons name="alarm" size={58} color="#FF3B30" />
              <View style={styles.alarmExclamation}>
                <Ionicons name="alert" size={24} color="#FF3B30" />
              </View>
            </View>
            <View style={styles.lightningRight}>
              <Ionicons name="flash" size={16} color="#FF3B30" />
            </View>
          </View>
        ) : (
          /* Checkmark or Cross Badge */
          <View
            style={[
              styles.iconCircleOuter,
              { backgroundColor: isCorrect ? "#D4F4E4" : "#FEE2E2" },
            ]}
          >
            <View
              style={[styles.iconCircleInner, { backgroundColor: heroColor }]}
            >
              <Ionicons
                name={isCorrect ? "checkmark" : "close"}
                size={44}
                color={Colors.white}
              />
            </View>
          </View>
        )}
      </View>

      {/* Hero Title */}
      <AppText
        style={[styles.heroTitle, { color: heroColor }]}
        weight={FontWeight.bold}
      >
        {title ?? defaultTitle}
      </AppText>

      {/* Hero Subtitle */}
      <AppText style={styles.heroSubtitle} weight={FontWeight.medium}>
        {subtitle ?? defaultSubtitle}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  graphicWrapper: {
    width: 130,
    height: 100,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  iconCircleOuter: {
    width: 92,
    height: 92,
    borderRadius: 46,
    alignItems: "center",
    justifyContent: "center",
  },
  iconCircleInner: {
    width: 74,
    height: 74,
    borderRadius: 37,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 3, blur: 6, opacity: 0.12, elevation: 3 }),
  },
  alarmWrapper: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  alarmCircle: {
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  alarmExclamation: {
    position: "absolute",
    top: 19,
  },
  lightningLeft: {
    transform: [{ rotate: "-25deg" }],
  },
  lightningRight: {
    transform: [{ rotate: "25deg" }],
  },
  particle: {
    position: "absolute",
    width: 8,
    height: 8,
    borderRadius: 2,
  },
  particle1: {
    top: 4,
    left: 10,
    backgroundColor: "#FBBF24",
    transform: [{ rotate: "15deg" }],
  },
  particle2: {
    top: 8,
    right: 14,
    backgroundColor: "#EF4444",
    transform: [{ rotate: "45deg" }],
  },
  particle3: {
    bottom: 12,
    left: 4,
    backgroundColor: "#3B82F6",
    width: 10,
    height: 5,
    transform: [{ rotate: "-30deg" }],
  },
  particle4: {
    bottom: 8,
    right: 8,
    backgroundColor: "#10B981",
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  particle5: {
    top: 48,
    left: -2,
    backgroundColor: "#EC4899",
    width: 6,
    height: 6,
  },
  particle6: {
    top: 42,
    right: -2,
    backgroundColor: "#F59E0B",
    transform: [{ rotate: "20deg" }],
  },
  heroTitle: {
    fontSize: 26,
    lineHeight: 32,
    marginTop: 8,
  },
  heroSubtitle: {
    fontSize: 13,
    lineHeight: 18,
    color: Colors.gray600,
    textAlign: "center",
    marginTop: 3,
  },
});
