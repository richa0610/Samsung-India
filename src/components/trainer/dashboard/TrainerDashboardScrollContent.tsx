import { useRouter } from "expo-router";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";

import { TrainingAgendaItem } from "@/api/training";
import Calendar from "@/components/calendar/Calendar";
import { DatePreset, DateRange } from "@/components/trainer/DateDrop";
import { Colors } from "@/theme/colors";
import { DashboardStats } from "./dashboardUtils";
import DashboardHeader from "./DashboardHeader";
import QuickActionsCard from "./QuickActionsCard";
import RecentSessionsCard from "./RecentSessionsCard";
import SummaryStatsRow from "./SummaryStatsRow";
import TrainingEfficiencyCard from "./TrainingEfficiencyCard";

type TrainerDashboardScrollContentProps = {
  adminName: string;
  companyId: string;
  dateRange: DateRange;
  datePreset: DatePreset;
  onApplyDateRange: (range: DateRange, preset: DatePreset) => void;
  stats: DashboardStats;
  recentCompleted: TrainingAgendaItem[];
  refreshing: boolean;
  onRefresh: () => void;
  onOpenProfile: () => void;
  onLogout: () => void;
  onSelectSession: (conferenceUid: string) => void;
};

export default function TrainerDashboardScrollContent({
  adminName,
  companyId,
  dateRange,
  datePreset,
  onApplyDateRange,
  stats,
  recentCompleted,
  refreshing,
  onRefresh,
  onOpenProfile,
  onLogout,
  onSelectSession,
}: TrainerDashboardScrollContentProps) {
  const router = useRouter();

  return (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.mainColour1]} tintColor={Colors.mainColour1} />
      }
    >
      <DashboardHeader name={adminName} companyId={companyId} onOpenProfile={onOpenProfile} onLogout={onLogout} />

      <Calendar range={dateRange} preset={datePreset} onApply={onApplyDateRange} />

      <SummaryStatsRow stats={stats} />

      <TrainingEfficiencyCard stats={stats} />

      <View style={styles.twoColumnRow}>
        <RecentSessionsCard
          sessions={recentCompleted}
          onViewAll={() => router.push({ pathname: "/sessions", params: { tab: "completed" } })}
          onSelectSession={onSelectSession}
        />
        <QuickActionsCard
          onCreateTraining={() => router.push("/add_training")}
          onTrainingList={() => router.push("/training_list")}
          onViewReports={() => router.push({ pathname: "/sessions", params: { tab: "completed" } })}
          onAddTrainee={() => router.push("/new_trainee")}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 24,
  },
  twoColumnRow: {
    flexDirection: "row",
    gap: 8,
    padding: 10,
    marginTop: 10,
  },
});
