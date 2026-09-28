import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";
import { trainingStatusLabel } from "@/utils/trainingStatusLabel";

export type TrainingStatus = "Completed" | "Ongoing" | "Scheduled" | "Missed" | "Absent";

export type TrainingRowData = {
  id: string;
  trainingName: string;
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
  Completed: { icon: "checkmark-circle-outline", color: "#059669", bg: Colors.successBgSoft },
  Ongoing: { icon: "radio-outline", color: Colors.blueAccent, bg: Colors.blue50 },
  Scheduled: { icon: "time-outline", color: "#EA580C", bg: "#FFF7ED" },
  Missed: { icon: "close-circle-outline", color: Colors.danger, bg: Colors.dangerBgSoft },
  Absent: { icon: "remove-circle-outline", color: Colors.gray500, bg: Colors.gray100 },
};

function HeaderCell({ label, hint, col, center }: { label: string; hint?: string; col: object; center?: boolean }) {
  return (
    <View style={[styles.cell, col, center ? styles.centerAlign : undefined]}>
      <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray700} style={styles.centerText}>
        {label}
      </AppText>
      {hint ? (
        <AppText variant="tiny" color={Colors.gray500} style={styles.centerText}>
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
        <AppText variant="caption" color={Colors.gray400}>
          -
        </AppText>
      ) : (
        <View style={styles.scoreRow}>
          <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray800}>
            {score.split("/")[0]}
          </AppText>
          <AppText variant="tiny" color={Colors.gray500}>
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
  /** Tapping a row navigates to that training's full detail (modules +
   *  question review). Omit to keep rows non-interactive. */
  onPressRow?: (id: string) => void;
};

export default function TrainingDetailsTable({ trainings = [], onViewAll, onPressRow }: TrainingDetailsTableProps) {
  return (
    <View style={styles.container}>
      <View style={styles.tableCard}>
        <View style={styles.cardHeader}>
          <View style={styles.clipboardBadge}>
            <Ionicons name="document-text" size={17} color={Colors.blueAccent} />
          </View>
          <AppText variant="body" weight={FontWeight.bold} color={Colors.black} style={styles.sectionTitle}>
            Training Details
          </AppText>
          {onViewAll ? (
            <Pressable onPress={onViewAll} hitSlop={8} accessibilityRole="button" accessibilityLabel="View all trainings">
              <AppText variant="caption" weight={FontWeight.bold} color={Colors.blueAccent}>
                View All
              </AppText>
            </Pressable>
          ) : (
            // Only shown without onViewAll (the full history page, not the
            // dashboard's capped preview) - there, `trainings.length` is the
            // true total, not just how many rows happen to be visible.
            <View >
              <AppText variant="caption" weight={FontWeight.bold}  >
                ({trainings.length})
              </AppText>
            </View>
          )}
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View>
            <View style={styles.headerRow}>
              <HeaderCell label="Training" col={styles.nameCol} />
              <HeaderCell label="Status" col={styles.statusCol} />
              <HeaderCell label="Date" col={styles.dateCol} />
              <HeaderCell label="Post Test" col={styles.scoreCol} center />
              <HeaderCell label="Quiz" col={styles.scoreCol} hint="(Score)" center />
              <HeaderCell label="Ranking" col={styles.rankCol} center />
            </View>

            {trainings.length === 0 && (
              <View style={styles.emptyRow}>
                <AppText variant="caption" color={Colors.gray400}>
                  No trainings yet
                </AppText>
              </View>
            )}

            {trainings.map((row) => (
              <Pressable
                key={row.id}
                style={styles.dataRow}
                onPress={onPressRow ? () => onPressRow(row.id) : undefined}
                accessibilityRole={onPressRow ? "button" : undefined}
                accessibilityLabel={onPressRow ? `View details for ${row.trainingName}` : undefined}
              >
                <View style={[styles.cell, styles.nameCol]}>
                  <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray800} numberOfLines={2} style={styles.centerText}>
                    {row.trainingName}
                  </AppText>
                </View>

                <View style={[styles.cell, styles.statusCol]}>
                  <View style={[styles.statusPill, { backgroundColor: STATUS_META[row.status].bg }]}>
                    <Ionicons name={STATUS_META[row.status].icon} size={15} color={STATUS_META[row.status].color} />
                    <AppText variant="caption" weight={FontWeight.bold} color={STATUS_META[row.status].color}>
                      {trainingStatusLabel(row.status)}
                    </AppText>
                  </View>
                </View>

                <View style={[styles.cell, styles.dateCol]}>
                  <View style={styles.dateWrap}>
                    <Ionicons name="calendar-outline" size={18} color="#1E3A8A" />
                    <View>
                      <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray800}>
                        {row.date}
                      </AppText>
                      <AppText variant="tiny" color={Colors.gray500}>
                        {row.day}
                      </AppText>
                    </View>
                  </View>
                </View>

                <ScoreCell score={row.postTestScore} />
                <ScoreCell score={row.quizScore} />

                <View style={[styles.cell, styles.rankCol, styles.centerAlign]}>
                  {!row.ranking || row.ranking === "-" ? (
                    <AppText variant="caption" color={Colors.gray400}>
                      -
                    </AppText>
                  ) : (
                    <View style={styles.centerAlign}>
                      <AppText variant="caption" weight={FontWeight.bold} color={Colors.black}>
                        {row.ranking}
                      </AppText>
                      {row.rankingScope ? (
                        <AppText variant="tiny" color={Colors.gray500}>
                          {row.rankingScope}
                        </AppText>
                      ) : null}
                    </View>
                  )}
                </View>
              </Pressable>
            ))}
          </View>
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingHorizontal: 9, marginTop: 18, marginBottom: 6 },
  tableCard: {
    backgroundColor: Colors.white,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.gray200,
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
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
  },
  sectionTitle: { fontSize: 16, flex: 1 },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FBFBFC",
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate100,
    borderTopWidth: 1,
    borderTopColor: Colors.slate100,
    paddingVertical: 6,
    gap:1,
  },
  dataRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate100,
    paddingVertical: 10,
  },
  emptyRow: { paddingVertical: 22, paddingHorizontal: 16, alignItems: "center" },
  cell: { paddingHorizontal: 6, alignItems: "center", justifyContent: "center" },
  nameCol: { width: 140 },
  statusCol: { width: 120 },
  dateCol: { width: 140 },
  scoreCol: { width: 120 },
  rankCol: { width: 100 },
  centerText: { textAlign: "center" },
  centerAlign: { alignItems: "center", justifyContent: "center" },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: Radius.pill,
  },
  dateWrap: { flexDirection: "row", alignItems: "center", gap: 10 },
  scoreRow: { flexDirection: "row", alignItems: "center", gap: 3 },
});
