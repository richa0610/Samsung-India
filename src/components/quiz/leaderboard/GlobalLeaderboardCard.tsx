import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import LeaderboardFilter, { LeaderboardFilterValues } from "@/components/quiz/LeaderboardFilter";
import LeaderboardRow, { LeaderboardUser } from "@/components/quiz/LeaderboardRow";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

type GlobalLeaderboardCardProps = {
  filterOpen: boolean;
  setFilterOpen: (open: boolean) => void;
  filterValues: LeaderboardFilterValues;
  setFilterValues: (values: LeaderboardFilterValues) => void;
  onApplyFilter: () => void;
  leaderboardUsers: LeaderboardUser[];
};

export default function GlobalLeaderboardCard({
  filterOpen,
  setFilterOpen,
  filterValues,
  setFilterValues,
  onApplyFilter,
  leaderboardUsers,
}: GlobalLeaderboardCardProps) {
  return (
    <View style={styles.leaderboardCard}>
      <View style={styles.cardHeader}>
        <View style={styles.titleRow}>
          <Ionicons name="trophy" size={16} color="#F59E0B" />
          <AppText style={styles.cardTitle} weight={FontWeight.bold}>
            Global Top 100
          </AppText>
        </View>

        <Pressable
          style={styles.filterBtn}
          onPress={() => setFilterOpen(!filterOpen)}
          hitSlop={8}
          accessibilityRole="button"
          accessibilityLabel="Toggle Leaderboard Filter"
        >
          <AppText style={styles.filterBtnText} color={Colors.headerBlue} weight={FontWeight.semiBold}>
            {filterOpen ? "Close" : "Filter"}
          </AppText>
          <Ionicons name={filterOpen ? "chevron-down" : "chevron-forward"} size={13} color={Colors.headerBlue} />
        </Pressable>
      </View>

      {filterOpen && (
        <LeaderboardFilter values={filterValues} onChangeValues={setFilterValues} onApply={onApplyFilter} />
      )}

      <View style={styles.rowsList}>
        {leaderboardUsers.map((user, index) => (
          <LeaderboardRow key={`${user.name}-${user.score}-${index}`} user={user} position={index + 1} />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  leaderboardCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 16,
    ...createShadow({ x: 0, y: 2, blur: 8, opacity: 0.06, elevation: 2 }),
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  cardTitle: {
    fontSize: 12,
    color: "#1E293B",
    letterSpacing: 0.4,
  },
  filterBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    paddingVertical: 2,
    paddingHorizontal: 4,
  },
  filterBtnText: {
    fontSize: 12,
  },
  rowsList: {
    gap: 0,
  },
});
