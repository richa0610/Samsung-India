import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { formatLeaderboardName } from "./formatLeaderboardName";

export type LeaderboardUser = {
  name: string;
  score: string;
  accuracy: string;
  isYou?: boolean;
};

export type LeaderboardRowProps = {
  user: LeaderboardUser;
  position: number;
};

export default function LeaderboardRow({ user, position }: LeaderboardRowProps) {
  const isYou = Boolean(user.isYou || user.name.toUpperCase() === "YOU");
  const displayName = formatLeaderboardName(user.name);

  return (
    <View style={[styles.row, isYou && styles.youRow]}>
      <View style={[styles.avatar, isYou && styles.youAvatar]}>
        <AppText style={styles.positionText} color={isYou ? Colors.headerBlue : "#475569"} weight={FontWeight.bold}>
          {position}
        </AppText>
      </View>

      <AppText style={[styles.name, isYou && styles.youName]} weight={isYou ? FontWeight.bold : FontWeight.semiBold} numberOfLines={1}>
        {displayName}
      </AppText>

      <View style={styles.scoreContainer}>
        <AppText style={styles.scoreText} color={Colors.headerBlue} weight={FontWeight.bold}>
          {user.score}
        </AppText>
        <AppText style={styles.accuracyText}> ({user.accuracy})</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    height: 48,
    borderWidth: 1,
    borderColor: Colors.slate200,
    borderRadius: 10,
    paddingHorizontal: 12,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    backgroundColor: Colors.white,
  },
  youRow: {
    backgroundColor: "#DCEBFE",
    borderColor: "#BFDBFE",
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#DBEAFE",
    marginRight: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  youAvatar: {
    backgroundColor: "#C2DCFF",
  },
  positionText: {
    fontSize: 13,
  },
  name: {
    flex: 1,
    fontSize: 13,
    color: "#1E293B",
    letterSpacing: 0.2,
  },
  youName: {
    color: "#0F172A",
    fontSize: 13.5,
  },
  scoreContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  scoreText: {
    fontSize: 13,
  },
  accuracyText: {
    fontSize: 12,
    color: "#64748B",
  },
});
