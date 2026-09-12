import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import {
  SafeAreaView,
  useSafeAreaInsets,
} from "react-native-safe-area-context";

import { TraineeBottomNavigation, TrainingSessionHeader } from "@/components/session";
import {
  Global_Percentage,
  TraineeMetricsGrid,
  TrainingDetailsTable,
  toTrainingRows,
} from "@/components/trainee/dashboard";
import { TraineeTab } from "@/hooks/useTraineeHome";
import { useTraineeDashboard } from "@/hooks/useTraineeDashboard";
import { Colors } from "@/theme/colors";

const rankLabel = (rank: number | null) => (rank != null ? `# ${rank.toLocaleString()}` : "Unranked");

export default function TraineeDashboardScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<TraineeTab>("dashboard");

  const {
    trainee,
    session,
    dashboard,
    refreshing,
    handleRefresh,
    handleLogout,
  } = useTraineeDashboard();

  const handleTabSelect = (tab: TraineeTab) => {
    setActiveTab(tab);
    if (tab === "home") {
      router.replace("/session_detail");
    } else if (tab === "rank") {
      router.push("/quiz_leaderboard");
    } else if (tab === "profile") {
      router.push("/profile");
    }
  };

  const metrics = dashboard?.metrics;
  const performance = dashboard?.performance;
  const ranking = dashboard?.ranking;

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="light" animated />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[Colors.headerBlue]}
            tintColor={Colors.headerBlue}
          />
        }
      >
        <TrainingSessionHeader
          userName={trainee?.name ?? undefined}
          gender={trainee?.gender}
          profilePhoto={trainee?.profilePhoto}
          confirmationStatus={session?.confirmationStatus ?? "Not Confirmed"}
          sessionType={session?.sessionType ?? undefined}
          title={session?.title ?? undefined}
          date={session?.date ?? undefined}
          location={session?.location ?? undefined}
          isOnline
          onLogout={handleLogout}
        />

        <TraineeMetricsGrid
          totalTrainings={metrics?.totalTrainings ?? 0}
          presentCount={metrics?.present ?? 0}
          absentCount={metrics?.absent ?? 0}
          scheduledCount={metrics?.scheduled ?? 0}
        />

        <Global_Percentage
          percentage={Math.round(performance?.percentage ?? 0)}
          totalScore={performance?.totalScore ?? 0}
          maxScore={performance?.maxScore ?? 0}
          periodGain={performance?.periodGain ?? null}
          globalRank={rankLabel(ranking?.globalRank ?? null)}
          globalPercentile={Math.round(ranking?.globalPercentile ?? 0)}
          stateRank={rankLabel(ranking?.stateRank ?? null)}
          statePercentile={Math.round(ranking?.statePercentile ?? 0)}
        />

        <TrainingDetailsTable
          trainings={toTrainingRows(dashboard?.trainings ?? [])}
          onViewAll={() => router.push("/training_history")}
        />
      </ScrollView>

      <TraineeBottomNavigation activeTab={activeTab} onSelectTab={handleTabSelect} />
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
    paddingBottom: 32,
  },
});
