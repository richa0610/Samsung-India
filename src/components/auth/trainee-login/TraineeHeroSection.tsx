import { useRouter } from "expo-router";
import { Pressable, StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Spacing } from "@/theme/spacing";
import { FontWeight } from "@/theme/typography";

/** Left-aligned hero text leaves right side open for the background's 3D graduation cap */
const HERO_TEXT_WIDTH = 0.52;

type TraineeHeroSectionProps = {
  onSkip?: () => void;
};

export default function TraineeHeroSection({ onSkip }: TraineeHeroSectionProps) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();

  const handleSkip = onSkip ?? (() => (router.canGoBack() ? router.back() : router.replace("/")));

  return (
    <View style={[styles.container, { paddingTop: insets.top + Spacing.sm }]}>
      {/* Top Header: TOPS Brand & Skip */}
      <View style={styles.topRow}>
        <View style={styles.brandBlock} accessible accessibilityRole="header" accessibilityLabel="TOPS">
          <AppText style={styles.brandTitle}>TOPS</AppText>
        </View>

        <Pressable
          onPress={handleSkip}
          hitSlop={12}
          style={styles.skipButton}
          accessibilityRole="button"
          accessibilityLabel="Skip"
        >
          <AppText style={styles.skipText}>Skip</AppText>
        </Pressable>
      </View>


      {/* Hero Headline & Subtitle */}
      <View style={[styles.heroContent, { width: width * HERO_TEXT_WIDTH }]}>
        <AppText variant="hero" color={Colors.authHeadline} weight={FontWeight.bold} style={styles.headline}>
          Learn.
        </AppText>
        <AppText variant="hero" color={Colors.authHeadline} weight={FontWeight.bold} style={styles.headline}>
          Assess.
        </AppText>
        <AppText variant="hero" color={Colors.primary} weight={FontWeight.bold} style={styles.headlineAccent}>
          Grow together.
        </AppText>

        <AppText color={Colors.textSupporting} style={styles.subtitle}>
          Access your trainings,{"\n"}assessments and track{"\n"}your progress.
        </AppText>

        {/* Carousel Indicator Dots */}
        <View style={styles.dotsRow} accessible accessibilityRole="tablist">
          <View style={styles.activeDot} />
          <View style={styles.inactiveDot} />
          <View style={styles.inactiveDot} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: Spacing.xl,
    marginBottom: Spacing.md,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    marginBottom: Spacing.lg,
  },
  brandBlock: {
    alignItems: "flex-start",
  },
  brandTitle: {
    color: Colors.primary,
    fontSize: 22,
    fontWeight: "900",
    letterSpacing: 2,
  },

  skipButton: {
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
  },
  skipText: {
    color: Colors.textSupporting,
    fontSize: 14,
    fontWeight: "500",
  },
  heroContent: {
    marginTop: Spacing.xs,
  },
  headline: {
    fontSize: 26,
    lineHeight: 32,
    letterSpacing: -0.5,
  },
  headlineAccent: {
    fontSize: 26,
    lineHeight: 32,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 18,
    marginTop: Spacing.sm,
  },
  dotsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: Spacing.md,
    marginBottom: Spacing.xs,
  },
  activeDot: {
    width: 18,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.primary,
  },
  inactiveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.gray300,
  },
});
