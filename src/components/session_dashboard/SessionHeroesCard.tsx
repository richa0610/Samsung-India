import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { SessionHeroStat } from "@/api/training";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type SessionHeroesCardProps = {
  heroes: SessionHeroStat[];
  isSessionClosed?: boolean;
  hasStarted?: boolean;
};

const VISUAL: Record<string, { icon: keyof typeof Ionicons.glyphMap; bg: string; color: string }> = {
  LIVE_QUIZ: { icon: "rocket", bg: "#FEE2E2", color: "#EF4444" },
  STANDARD_TEST: { icon: "clipboard", bg: "#EFF6FF", color: "#0066FF" },
};

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metricItem}>
      <AppText style={styles.metricLabel}>{label}</AppText>
      <AppText style={styles.metricValue}>{value}</AppText>
    </View>
  );
}

export default function SessionHeroesCard({ heroes, hasStarted = true }: SessionHeroesCardProps) {
  return (
    <View style={styles.container}>
      <AppText style={styles.sectionTitle}>SESSION HEROES</AppText>

      {heroes.length === 0 && (
        <View style={styles.heroCard}>
          <AppText style={styles.emptyText}>
            {hasStarted
              ? "No quiz or test module in this session."
              : "Hero stats appear once quizzes / tests are attempted."}
          </AppText>
        </View>
      )}

      {heroes.map((hero) => {
        const v = VISUAL[hero.moduleKey] ?? VISUAL.STANDARD_TEST;
        const hasScores = hero.participants > 0;
        return (
          <View key={hero.moduleKey} style={styles.heroCard}>
            <View style={styles.cardHeader}>
              <View style={styles.leftTitleRow}>
                <View style={[styles.iconCircle, { backgroundColor: v.bg }]}>
                  <Ionicons name={v.icon} size={18} color={v.color} />
                </View>
                <View>
                  <AppText style={styles.heroTitle}>{hero.label} Hero</AppText>
                  <View style={styles.badgesRow}>
                    <View style={styles.darkBadge}>
                      <AppText style={styles.darkBadgeText}>
                        {hasScores ? (hero.topName ?? "—") : "Standby"}
                      </AppText>
                    </View>
                    <View style={styles.greyBadge}>
                      <AppText style={styles.greyBadgeText}>{hero.participants} attempted</AppText>
                    </View>
                  </View>
                </View>
              </View>
            </View>

            <View style={styles.metricsRow}>
              <Metric label="Participants" value={hasScores ? String(hero.participants) : "-"} />
              <Metric label="Average" value={hasScores ? `${hero.averagePercent}%` : "-"} />
              <Metric label="Best" value={hasScores ? `${hero.bestPercent}%` : "-"} />
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginHorizontal: 14, marginTop: 12, gap: 8 },
  sectionTitle: {
    fontSize: 12.5,
    fontWeight: "800",
    color: "#111827",
    letterSpacing: 0.3,
    marginBottom: 2,
  },
  heroCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    ...Shadows.card,
  },
  emptyText: { fontSize: 11, color: "#6B7280", textAlign: "center", paddingVertical: 8 },
  cardHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  leftTitleRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconCircle: { width: 38, height: 38, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  heroTitle: { fontSize: 13, fontWeight: "800", color: "#111827" },
  badgesRow: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 3 },
  greyBadge: { backgroundColor: "#F3F4F6", paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  greyBadgeText: { fontSize: 8, fontWeight: "600", color: "#6B7280" },
  darkBadge: { backgroundColor: "#1F2937", paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  darkBadgeText: { fontSize: 8, fontWeight: "700", color: Colors.white },
  metricsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: Colors.gray50,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 8,
    marginTop: 10,
  },
  metricItem: { flex: 1, alignItems: "center" },
  metricLabel: { fontSize: 9, color: "#6B7280", fontWeight: "500" },
  metricValue: { fontSize: 13.5, fontWeight: "800", color: "#111827", marginTop: 2 },
});
