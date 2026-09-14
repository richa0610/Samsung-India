import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import StatCard from "./StatCard";
import { DashboardStats } from "./dashboardUtils";

type SummaryStatsRowProps = {
  stats: DashboardStats;
};

export default function SummaryStatsRow({ stats }: SummaryStatsRowProps) {
  return (
    <View style={styles.container}>
      <StatCard
        icon={<Ionicons name="people" size={16} color="#2563EB" />}
        iconBg="#EFF6FF"
        title="Total Trainees"
        value={stats.totalTrainees}
        valueColor="#2563EB"
        subtext="All Active"
        subtextColor="#9CA3AF"
      />

      <StatCard
        icon={<Ionicons name="book-outline" size={16} color="#10B981" />}
        iconBg="#ECFDF5"
        title="Total Sessions"
        value={stats.totalSessions}
        valueColor="#10B981"
        subtext="This Period"
        subtextColor="#9CA3AF"
      />

      <StatCard
        icon={<Ionicons name="calendar-outline" size={16} color="#F59E0B" />}
        iconBg="#FFFBEB"
        title="Completed"
        value={stats.completed}
        valueColor="#F59E0B"
        subtext="This Period"
        subtextColor="#9CA3AF"
      />

      <StatCard
        icon={<Ionicons name="time-outline" size={16} color="#EF4444" />}
        iconBg="#FEF2F2"
        title="Pending"
        value={stats.pending}
        valueColor="#EF4444"
        subtext="This Period"
        subtextColor="#EF4444"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: 10,
    marginTop: 10,
  },
});
