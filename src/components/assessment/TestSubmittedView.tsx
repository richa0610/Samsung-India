import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";
import {
  ConfettiHero,
  SubmissionActions,
  SubmissionSummaryCard,
  SubmissionSummaryRow,
  ThankYouBanner,
} from "./test-submitted";

export type { SubmissionSummaryRow } from "./test-submitted";

type Props = {
  rows: SubmissionSummaryRow[];
  onGoToDashboard: () => void;
  title?: string;
  thankYouText?: string;
};

export default function TestSubmittedView({
  rows,
  onGoToDashboard,
  title = "Test Submitted Successfully",
  thankYouText = "Your Test has been submitted successfully.\nYou will be notified once the results are available.",
}: Props) {
  return (
    <SafeAreaView style={styles.screenContainer} edges={["top", "bottom"]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        bounces={false}
      >
        <View style={styles.mainCard}>
          <ConfettiHero />

          <View style={styles.titleWrap}>
            <AppText variant="h2" weight={FontWeight.medium} align="center" style={styles.title}>
              {title}
            </AppText>
            <AppText variant="caption" color="#6B7280" align="center" style={styles.subtitle}>
              {"Your assessment has been submitted\nand recorded successfully."}
            </AppText>
          </View>

          <SubmissionSummaryCard rows={rows} />

          <ThankYouBanner thankYouText={thankYouText} />

          <SubmissionActions onGoToDashboard={onGoToDashboard} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screenContainer: {
    flex: 1,
    backgroundColor: "#F0F6FE",
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 16,
    justifyContent: "flex-end",
  },
  mainCard: {
    width: "100%",
    backgroundColor: Colors.white,
    borderRadius: 26,
    paddingHorizontal: 18,
    paddingTop: 22,
    paddingBottom: 18,
    alignItems: "center",
    justifyContent: "center",
    gap: 20,
    ...createShadow({ x: 0, y: 8, blur: 24, opacity: 0.08, elevation: 4 }),
  },
  titleWrap: {
    width: "100%",
    alignItems: "center",
  },
  title: {
    fontSize: 21,
    marginTop: 6,
    color: "#111827",
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 13,
    marginTop: 3,
    lineHeight: 17,
  },
});
