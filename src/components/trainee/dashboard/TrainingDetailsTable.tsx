import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

export type TrainingStatus = "Completed" | "Ongoing" | "Scheduled" | "Missed" | "Absent";

export type TrainingRowData = {
  id: string;
  status: TrainingStatus;
  date: string;
  day: string;
  postTestScore?: string;
  quizScore?: string;
  ranking?: string;
  rankingScope?: "Global" | "State" | "Session";
  isLiveOrScheduled?: boolean;
};

const STATUS_META: Record<TrainingStatus, { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string }> = {
  Completed: { icon: "checkmark-circle-outline", color: "#059669", bg: "#ECFDF5" },
  Ongoing: { icon: "radio-outline", color: "#2563EB", bg: "#EFF6FF" },
  Scheduled: { icon: "time-outline", color: "#EA580C", bg: "#FFF7ED" },
  Missed: { icon: "close-circle-outline", color: "#DC2626", bg: "#FEF2F2" },
  Absent: { icon: "remove-circle-outline", color: "#6B7280", bg: "#F3F4F6" },
};

function HeaderCell({ label, hint, col, center }: { label: string; hint?: string; col: object; center?: boolean }) {
  return (
    <View style={[styles.cell, col, center ? styles.centerAlign : undefined]}>
      <AppText variant="caption" weight={FontWeight.bold} color="#374151" style={styles.centerText}>
        {label}
      </AppText>
      {hint ? (
        <AppText variant="tiny" color="#6B7280" style={styles.centerText}>
          {hint}
        </AppText>
      ) : null}
    </View>
  );
}

function ScoreCell({ score }: { score?: string }) {
  return (
    <View style={[styles.cell, styles.scoreCol, styles.centerAlign]}>
      {!score || score === "-" ? (
        <AppText variant="caption" color="#9CA3AF">
          -
        </AppText>
      ) : (
        <View style={styles.scoreRow}>
          <AppText variant="caption" weight={FontWeight.bold} color="#1F2937">
            {score.split("/")[0]}
          </AppText>
          <AppText variant="tiny" color="#6B7280">
            /{score.split("/")[1]}
          </AppText>
        </View>
      )}
    </View>
  );
}

type TrainingDetailsTableProps = {
  trainings?: TrainingRowData[];
  /** Shows a "View All" link top-right of the header, e.g. when this table
   *  is a capped preview (dashboard's 5 most recent) of a fuller history
   *  screen. Omit to render without it. */
  onViewAll?: () => void;
};

export default function TrainingDetailsTable({ trainings = [], onViewAll }: TrainingDetailsTableProps) {
  return (
    <View style={styles.container}>
      <View style={styles.tableCard}>
        <View style={styles.cardHeader}>
          <View style={styles.clipboardBadge}>
            <Ionicons name="document-text" size={17} color="#2563EB" />
          </View>
          <AppText variant="body" weight={FontWeight.bold} color="#111827" style={styles.sectionTitle}>
            Training Details
          </AppText>
          {onViewAll && (
            <Pressable onPress={onViewAll} hitSlop={8} accessibilityRole="button" accessibilityLabel="View all trainings">
              <AppText variant="caption" weight={FontWeight.bold} color="#2563EB">
                View All
              </AppText>
            </Pressable>
          )}
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View>
            <View style={styles.headerRow}>
              <HeaderCell label="Status" col={styles.statusCol} />
              <HeaderCell label="Date" col={styles.dateCol} />
              <HeaderCell label="Post Test" col={styles.scoreCol} center />
              <HeaderCell label="Quiz" col={styles.scoreCol} hint="(Score)" center />
              <HeaderCell label="Ranking" col={styles.rankCol} center />
            </View>

            {trainings.length === 0 && (
              <View style={styles.emptyRow}>
                <AppText variant="caption" color="#9CA3AF">
                  No trainings yet
                </AppText>
              </View>
            )}

            {trainings.map((row) => (
              <View key={row.id} style={styles.dataRow}>
                <View style={[styles.cell, styles.statusCol]}>
                  <View style={[styles.statusPill, { backgroundColor: STATUS_META[row.status].bg }]}>
                    <Ionicons name={STATUS_META[row.status].icon} size={15} color={STATUS_META[row.status].color} />
                    <AppText variant="caption" weight={FontWeight.bold} color={STATUS_META[row.status].color}>
                      {row.status}
                    </AppText>
                  </View>
                </View>

                <View style={[styles.cell, styles.dateCol]}>
                  <View style={styles.dateWrap}>
                    <Ionicons name="calendar-outline" size={18} color="#1E3A8A" />
                    <View>
                      <AppText variant="caption" weight={FontWeight.bold} color="#1F2937">
                        {row.date}
                      </AppText>
                      <AppText variant="tiny" color="#6B7280">
                        {row.day}
                      </AppText>
                    </View>
                  </View>
                </View>

                <ScoreCell score={row.postTestScore} />
                <ScoreCell score={row.quizScore} />

                <View style={[styles.cell, styles.rankCol, styles.centerAlign]}>
                  {!row.ranking || row.ranking === "-" ? (
                    <AppText variant="caption" color="#9CA3AF">
                      -
                    </AppText>
                  ) : (
                    <View style={styles.centerAlign}>
                      <AppText variant="caption" weight={FontWeight.bold} color="#111827">
                        {row.ranking}
                      </AppText>
                      {row.rankingScope ? (
                        <AppText variant="tiny" color="#6B7280">
                          {row.rankingScope}
                        </AppText>
                      ) : null}
                    </View>
                  )}
                </View>
              </View>
            ))}
          </View>
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingHorizontal: 16, marginTop: 18, marginBottom: 28 },
  tableCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    overflow: "hidden",
    ...Shadows.card,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 14,
  },
  clipboardBadge: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: "#EFF6FF",
    alignItems: "center",
    justifyContent: "center",
  },
  sectionTitle: { fontSize: 16, flex: 1 },
  headerRow: {
    flexDirection: "row",
    backgroundColor: "#FBFBFC",
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
    paddingVertical: 12,
  },
  dataRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
    paddingVertical: 16,
    alignItems: "center",
  },
  emptyRow: { paddingVertical: 22, paddingHorizontal: 16, alignItems: "center" },
  cell: { paddingHorizontal: 12, justifyContent: "center" },
  statusCol: { width: 120 },
  dateCol: { width: 140 },
  scoreCol: { width: 120 },
  rankCol: { width: 100 },
  centerText: { textAlign: "center" },
  centerAlign: { alignItems: "center", justifyContent: "center" },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: Radius.pill,
    alignSelf: "flex-start",
  },
  dateWrap: { flexDirection: "row", alignItems: "center", gap: 10 },
  scoreRow: { flexDirection: "row", alignItems: "center", gap: 3 },
});
