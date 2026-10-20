import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import LeaderboardRow, { LeaderboardUser } from "@/components/quiz/LeaderboardRow";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";

type GlobalLeaderboardCardProps = {
  leaderboardUsers: LeaderboardUser[];
};

export default function GlobalLeaderboardCard({ leaderboardUsers }: GlobalLeaderboardCardProps) {
  return (
    <View style={styles.leaderboardCard}>
      <View style={styles.cardHeader}>
        <View style={styles.titleRow}>
          <Ionicons name="trophy" size={16} color={Colors.warning} />
          <AppText style={styles.cardTitle} weight={FontWeight.bold}>
            Global Top 100
          </AppText>
        </View>
      </View>

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
    color: Colors.black,
    letterSpacing: 0.4,
  },
  rowsList: {
    gap: 0,
  },
});
