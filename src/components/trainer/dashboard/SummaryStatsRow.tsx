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
        icon={<Ionicons name="book-outline" size={16} color="#10B981" />}
        iconBg="#ECFDF5"
        title="Total Sessions"
        value={stats.totalSessions}
        valueColor="#10B981"
      />

      <StatCard
        icon={<Ionicons name="calendar-outline" size={16} color="#F59E0B" />}
        iconBg="#FFFBEB"
        title="Completed"
        value={stats.completed}
        valueColor="#F59E0B"
      />

      <StatCard
        icon={<Ionicons name="time-outline" size={16} color="#EF4444" />}
        iconBg="#FEF2F2"
        title="Planned"
        value={stats.pending}
        valueColor="#EF4444"
      />

      <StatCard
        icon={<Ionicons name="alert-circle-outline" size={16} color="#7C3AED" />}
        iconBg="#F5F3FF"
        title="Missed"
        value={stats.missed}
        valueColor="#7C3AED"
      />

      <StatCard
        icon={<Ionicons name="radio-outline" size={16} color="#0EA5E9" />}
        iconBg="#F0F9FF"
        title="Ongoing"
        value={stats.ongoing}
        valueColor="#0EA5E9"
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
