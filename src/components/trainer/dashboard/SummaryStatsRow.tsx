import { StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import StatCard from "./StatCard";
import { DashboardStats } from "./dashboardUtils";
import { Colors } from "@/theme/colors";

type SummaryStatsRowProps = {
  stats: DashboardStats;
};

export default function SummaryStatsRow({ stats }: SummaryStatsRowProps) {
  return (
    <View style={styles.container}>
      <StatCard
        icon={<Ionicons name="book-outline" size={16} color={Colors.statusGreen} />}
        iconBg={Colors.successBgSoft}
        title="Total Sessions"
        value={stats.totalSessions}
        valueColor={Colors.statusGreen}
      />

      <StatCard
        icon={<Ionicons name="calendar-outline" size={16} color={Colors.warning} />}
        iconBg="#FFFBEB"
        title="Completed"
        value={stats.completed}
        valueColor={Colors.warning}
      />

      <StatCard
        icon={<Ionicons name="time-outline" size={16} color={Colors.red} />}
        iconBg={Colors.dangerBgSoft}
        title="Planned"
        value={stats.pending}
        valueColor={Colors.red}
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
