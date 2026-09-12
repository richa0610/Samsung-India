import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { TopPerformer } from "./sessionDashboardTypes";

type TopPerformersCardProps = {
  performers: TopPerformer[];
  hasStarted?: boolean;
  onViewAll?: () => void;
};

export default function TopPerformersCard({
  performers,
  hasStarted = true,
  onViewAll,
}: TopPerformersCardProps) {
  const hasData = performers.length > 0;

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <AppText style={styles.crownEmoji}>👑</AppText>
          <AppText style={styles.title}>TOP PERFORMERS</AppText>
        </View>

        {hasStarted && hasData && onViewAll && (
          <Pressable
            style={styles.toggleBtn}
            onPress={onViewAll}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel="View All"
          >
            <AppText style={styles.toggleText}>View All</AppText>
            <Ionicons name="chevron-forward" size={13} color="#0066FF" />
          </Pressable>
        )}
      </View>

      {/* Empty State */}
      {(!hasStarted || !hasData) && (
        <View style={styles.emptyState}>
          <AppText style={styles.emptyTrophy}>🏆</AppText>
          <AppText style={styles.emptyTitle}>Leaderboard Empty</AppText>
          <AppText style={styles.emptySubtitle}>
            Scores will appear here as participants finish quizzes
          </AppText>
        </View>
      )}

      {/* List */}
      {hasStarted && hasData && (
        <View style={styles.list}>
          {performers.map((performer, index) => (
            <View key={`${performer.id}-${index}`} style={styles.performerRow}>
              <View style={styles.leftInfo}>
                <View style={styles.avatarCircle}>
                  <Ionicons name="person" size={13} color="#8B5CF6" />
                </View>
                <AppText style={styles.name} numberOfLines={1}>
                  {performer.name}
                </AppText>
              </View>

              <AppText style={styles.scoreText}>
                {performer.score}/{performer.maxScore}{" "}
                <AppText style={styles.percentageText}>
                  [{performer.percentage}%]
                </AppText>
              </AppText>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    marginHorizontal: 14,
    marginTop: 10,
    ...Shadows.card,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  crownEmoji: {
    fontSize: 14,
  },
  title: {
    fontSize: 12.5,
    fontWeight: "800",
    color: "#111827",
    letterSpacing: 0.3,
  },
  toggleBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
  },
  toggleText: {
    fontSize: 11.5,
    color: "#0066FF",
    fontWeight: "700",
  },
  list: {
    gap: 6,
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 18,
    gap: 4,
  },
  emptyTrophy: {
    fontSize: 32,
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 13,
    fontWeight: "800",
    color: "#111827",
  },
  emptySubtitle: {
    fontSize: 11,
    color: "#6B7280",
    fontWeight: "500",
    textAlign: "center",
    paddingHorizontal: 20,
  },
  performerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    paddingVertical: 7,
    paddingHorizontal: 8,
  },
  leftInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flex: 1,
  },
  avatarCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#EDE9FE",
    alignItems: "center",
    justifyContent: "center",
  },
  name: {
    fontSize: 11,
    fontWeight: "700",
    color: "#111827",
    flex: 1,
  },
  scoreText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#0066FF",
  },
  percentageText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#6B7280",
  },
});
