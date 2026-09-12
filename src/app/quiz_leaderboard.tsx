import { StatusBar } from "expo-status-bar";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AccuracyScoreCard, GlobalLeaderboardCard, ResultsHero } from "@/components/quiz/leaderboard";
import PerformanceSummary from "@/components/quiz/PerformanceSummary";
import QuizLiveHeader from "@/components/quiz/QuizLiveHeader";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { useQuizLeaderboard } from "@/hooks/useQuizLeaderboard";

export default function QuizLeaderboardScreen() {
  const {
    insets,
    screenWidth,
    liveState,
    showResults,
    quizEnded,
    total,
    correct,
    accuracy,
    incorrect,
    timeTakenFormatted,
    filterOpen,
    setFilterOpen,
    filterValues,
    setFilterValues,
    leaderboardUsers,
    handleApplyFilter,
    handleContinue,
  } = useQuizLeaderboard();

  const emptyCopy =
    liveState === "in_progress" && quizEnded
      ? {
          title: "Live Quiz has ended",
          body: "This session's Live Quiz is over and you didn't submit an entry, so there's no rank to show.",
        }
      : liveState === "in_progress"
        ? {
            title: "Attend the Live Quiz first",
            body: "Answer each question as your trainer broadcasts it, then hit Final Submit — your rank will appear here right after.",
          }
        : {
            title: "No Live Quiz results yet",
            body: "Take part in a Live Quiz during a session and your rank will show up here.",
          };

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="light" animated />

      <QuizLiveHeader onSync={() => {}} onRefresh={() => {}} isConnected={true} />

      {!showResults ? (
        <View style={styles.pendingWrap}>
          <AppText style={styles.pendingTitle} weight={FontWeight.bold}>
            {emptyCopy.title}
          </AppText>
          <AppText style={styles.pendingBody} color={Colors.gray600}>
            {emptyCopy.body}
          </AppText>
          <Pressable style={styles.continueButton} onPress={handleContinue}>
            <AppText style={styles.continueButtonText} color={Colors.white} weight={FontWeight.bold}>
              Back to session
            </AppText>
          </Pressable>
        </View>
      ) : (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <ResultsHero screenWidth={screenWidth} />

        <AccuracyScoreCard
          accuracy={accuracy}
          correct={correct}
          total={total}
          timeTakenFormatted={timeTakenFormatted}
        />

        <PerformanceSummary
          correctCount={correct}
          incorrectCount={incorrect}
          accuracy={accuracy}
          timeTaken={timeTakenFormatted}
        />

        <GlobalLeaderboardCard
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          filterValues={filterValues}
          setFilterValues={setFilterValues}
          onApplyFilter={handleApplyFilter}
          leaderboardUsers={leaderboardUsers}
        />

        <Pressable
          style={styles.continueButton}
          onPress={handleContinue}
          accessibilityRole="button"
          accessibilityLabel="Continue to Dashboard"
        >
          <AppText style={styles.continueButtonText} color={Colors.white} weight={FontWeight.bold}>
            Continue
          </AppText>
        </Pressable>
      </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  statusBarBackground: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.headerBlue,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 36,
    gap: 12,
  },
  pendingWrap: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, paddingHorizontal: 28 },
  pendingTitle: { fontSize: 18, color: "#111827" },
  pendingBody: { fontSize: 13, textAlign: "center", lineHeight: 19 },
  continueButton: {
    height: 52,
    borderRadius: 14,
    backgroundColor: Colors.headerBlue,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 4,
  },
  continueButtonText: {
    fontSize: 16,
  },
});
