import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
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
import LogoutConfirmModal from "@/components/ui/LogoutConfirmModal";
import { TraineeTab } from "@/hooks/useTraineeHome";
import { useTraineeDashboard } from "@/hooks/useTraineeDashboard";
import { Colors } from "@/theme/colors";
import { canNavigate } from "@/utils/navigationGuard";

const rankLabel = (rank: number | null) => (rank != null ? `# ${rank.toLocaleString()}` : "Unranked");

// This screen only ever renders while its own tab is active - selecting a
// different tab navigates away (see handleTabSelect) rather than updating
// state in place, so there's no need for this to be React state.
const ACTIVE_TAB: TraineeTab = "dashboard";

export default function TraineeDashboardScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const {
    trainee,
    session,
    dashboard,
    refreshing,
    handleRefresh,
    confirmLogoutOpen,
    requestLogout,
    cancelLogout,
    confirmLogout,
  } = useTraineeDashboard();

  const handleTabSelect = (tab: TraineeTab) => {
    // No setActiveTab(tab) here - every branch below navigates away
    // immediately, so updating this screen's own state right before it
    // unmounts was dead work that never painted. Worse: it queued a Fabric
    // view mutation for this screen in the exact same tick router.replace()
    // queues the transition's own mutations - a plausible contributor to
    // the "child already has a parent" crash on tab navigation.
    // Guards against that crash from firing a second replace() before the
    // previous tab's screen transition has finished mounting - see
    // utils/navigationGuard.ts.
    if (!canNavigate()) return;
    if (tab === "home") {
      router.replace("/session_detail");
    } else if (tab === "rank") {
      router.replace("/quiz_leaderboard");
    } else if (tab === "profile") {
      router.replace("/profile");
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
          onLogout={requestLogout}
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
          onPressRow={(conferenceUid) => router.push({ pathname: "/training_detail", params: { conferenceUid } })}
        />
      </ScrollView>

      <TraineeBottomNavigation activeTab={ACTIVE_TAB} onSelectTab={handleTabSelect} />
      <LogoutConfirmModal visible={confirmLogoutOpen} onCancel={cancelLogout} onConfirm={confirmLogout} />
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
