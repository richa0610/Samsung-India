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

// A score's colour from how well it went - the value shown is unchanged.
const SCORE_TONES = [
  { from: 0.75, color: "#059669", bg: Colors.successBgSoft },
  { from: 0.4, color: "#B45309", bg: "#FFFBEB" },
  { from: 0, color: Colors.danger, bg: Colors.dangerBgSoft },
];

type RankLook = { icon?: keyof typeof Ionicons.glyphMap; iconColor?: string; text: string; bg: string; border: string };

// Gold / silver / bronze for the session's top three; everyone else a calm blue.
const PODIUM: Record<string, RankLook> = {
  "1": { icon: "trophy", iconColor: "#D97706", text: "#92400E", bg: "#FEF3C7", border: "#FCD34D" },
  "2": { icon: "medal", iconColor: "#64748B", text: "#334155", bg: "#F1F5F9", border: "#CBD5E1" },
  "3": { icon: "medal", iconColor: "#C2410C", text: "#9A3412", bg: "#FFEDD5", border: "#FDBA74" },
};
const OTHER_RANK: RankLook = { text: Colors.blueAccent, bg: Colors.blue50, border: "#D6E6FF" };

/** 1 -> "1st", 2 -> "2nd", 11 -> "11th", 23 -> "23rd"; anything not a whole number as given. */
export function ordinal(rank: string): string {
  if (!/^\d+$/.test(rank)) return rank;
  const n = Number(rank);
  const lastTwo = n % 100;
  const suffix = lastTwo >= 11 && lastTwo <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[n % 10] ?? "th";
  return `${n}${suffix}`;
}

// The table's ranks are the trainee's place in that session (the column header says so).
const DEFAULT_RANK_SCOPE = "Session";

const HEADER_TINT = "#F5F9FF";
const STRIPE = "#FAFBFD";

function HeaderCell({ label, hint, col, center }: { label: string; hint?: string; col: object; center?: boolean }) {
  return (
    <View style={[styles.cell, col, center ? styles.centerAlign : undefined]}>
      <AppText variant="tiny" weight={FontWeight.bold} color={Colors.gray600} style={[styles.centerText, styles.headerLabel]}>
        {label}
      </AppText>
      {hint ? (
        <AppText variant="tiny" color={Colors.gray400} style={styles.centerText}>
          {hint}
        </AppText>
      ) : null}
    </View>
  );
}

function ScoreCell({ score }: { score?: string }) {
  const [got, outOf] = (score ?? "").split("/");
  const ratio = Number(got) / Number(outOf);
  if (!score || score === "-" || !outOf) {
    return (
      <View style={[styles.cell, styles.scoreCol, styles.centerAlign]}>
        <AppText variant="caption" color={Colors.gray400}>
          -
        </AppText>
      </View>
    );
  }
  const known = Number.isFinite(ratio);
  const tone = known ? SCORE_TONES.find((t) => ratio >= t.from) ?? SCORE_TONES[2] : null;
  return (
    <View style={[styles.cell, styles.scoreCol, styles.centerAlign]}>
      <View style={[styles.scorePill, { backgroundColor: tone?.bg ?? Colors.gray50 }]}>
        <AppText variant="caption" weight={FontWeight.bold} color={tone?.color ?? Colors.gray800}>
          {got}
        </AppText>
        <AppText variant="tiny" color={Colors.gray500}>
          /{outOf}
        </AppText>
      </View>
      {known && (
        <View style={styles.scoreTrack}>
          <View
            style={[styles.scoreFill, { width: `${Math.min(100, Math.max(0, ratio * 100))}%`, backgroundColor: tone?.color }]}
          />
        </View>
      )}
    </View>
  );
}

function RankCell({ ranking, scope }: { ranking?: string; scope?: string }) {
  if (!ranking || ranking === "-") {
    return (
      <View style={[styles.cell, styles.rankCol, styles.centerAlign]}>
        <AppText variant="caption" color={Colors.gray400}>
          -
        </AppText>
      </View>
    );
  }
  const look = PODIUM[ranking] ?? OTHER_RANK;
  return (
    <View style={[styles.cell, styles.rankCol, styles.centerAlign]}>
      <View
        style={[styles.rankPill, { backgroundColor: look.bg, borderColor: look.border }]}
        accessibilityLabel={`Ranked ${ordinal(ranking)}${scope ? ` in the ${scope.toLowerCase()}` : ""}`}
      >
        {look.icon && <Ionicons name={look.icon} size={14} color={look.iconColor} />}
        <AppText variant="caption" weight={FontWeight.bold} color={look.text}>
          {ordinal(ranking)}
        </AppText>
      </View>
      {/* Only a scope other than the column's own ("Session") needs saying per row. */}
      {scope && scope !== DEFAULT_RANK_SCOPE ? (
        <AppText variant="tiny" color={Colors.gray500} style={styles.rankScope}>
          {scope}
        </AppText>
      ) : null}
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
        <View style={styles.accentBar} />
        <View style={styles.cardHeader}>
          <View style={styles.titleBadge}>
            <Ionicons name="document-text" size={16} color={Colors.white} />
          </View>
          <AppText variant="body" weight={FontWeight.bold} color={Colors.black} style={styles.sectionTitle}>
            Training Details
          </AppText>
          {onViewAll ? (
            <Pressable
              onPress={onViewAll}
              hitSlop={8}
              style={({ pressed }) => [styles.viewAllButton, pressed && styles.viewAllPressed]}
              accessibilityRole="button"
              accessibilityLabel="View all trainings"
            >
              <AppText variant="caption" weight={FontWeight.bold} color={Colors.mainColour1}>
                View All
              </AppText>
              <Ionicons name="chevron-forward" size={13} color={Colors.mainColour1} />
            </Pressable>
          ) : (
            // Only shown without onViewAll (the full history page, not the
            // dashboard's capped preview) - there, `trainings.length` is the
            // true total, not just how many rows happen to be visible.
            <View style={styles.countPill}>
              <AppText variant="caption" weight={FontWeight.bold} color={Colors.mainColour1}>
                {trainings.length}
              </AppText>
            </View>
          )}
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View>
            <View style={styles.headerRow}>
              <HeaderCell label="S.No" col={styles.serialCol} center />
              <HeaderCell label="Training" col={styles.nameCol} />
              <HeaderCell label="Status" col={styles.statusCol} />
              <HeaderCell label="Date" col={styles.dateCol} />
              <HeaderCell label="Post Test" col={styles.scoreCol} center />
              <HeaderCell label="Quiz" col={styles.scoreCol} hint="(Score)" center />
              <HeaderCell label="Ranking" col={styles.rankCol} hint={`(${DEFAULT_RANK_SCOPE})`} center />
              {onPressRow && <View style={styles.chevronCol} />}
            </View>

            {trainings.length === 0 && (
              <View style={styles.emptyRow}>
                <View style={styles.emptyIcon}>
                  <Ionicons name="file-tray-outline" size={22} color={Colors.gray400} />
                </View>
                <AppText variant="caption" color={Colors.gray400}>
                  No trainings yet
                </AppText>
              </View>
            )}

            {trainings.map((row, index) => {
              const status = STATUS_META[row.status];
              return (
                <Pressable
                  key={row.id}
                  style={({ pressed }) => [
                    styles.dataRow,
                    index % 2 === 1 && styles.stripedRow,
                    pressed && onPressRow ? styles.pressedRow : null,
                  ]}
                  onPress={onPressRow ? () => onPressRow(row.id) : undefined}
                  disabled={!onPressRow}
                  accessibilityRole={onPressRow ? "button" : undefined}
                  accessibilityLabel={onPressRow ? `View details for ${row.trainingName}` : undefined}
                >
                  {/* Position in the list as shown (newest first) - Training History keeps counting
                      as more pages load. */}
                  <View style={[styles.cell, styles.serialCol, styles.centerAlign]}>
                    <View style={styles.serialBadge}>
                      <AppText variant="tiny" weight={FontWeight.bold} color={Colors.mainColour1}>
                        {index + 1}
                      </AppText>
                    </View>
                  </View>

                  <View style={[styles.cell, styles.nameCol]}>
                    <AppText variant="caption" weight={FontWeight.bold} color={Colors.gray800} numberOfLines={2} style={styles.centerText}>
                      {row.trainingName}
                    </AppText>
                  </View>

                  <View style={[styles.cell, styles.statusCol]}>
                    <View style={[styles.statusPill, { backgroundColor: status.bg, borderColor: `${status.color}33` }]}>
                      <Ionicons name={status.icon} size={14} color={status.color} />
                      <AppText variant="caption" weight={FontWeight.bold} color={status.color}>
                        {trainingStatusLabel(row.status)}
                      </AppText>
                    </View>
                  </View>

                  <View style={[styles.cell, styles.dateCol]}>
                    <View style={styles.dateWrap}>
                      <View style={styles.dateIcon}>
                        <Ionicons name="calendar" size={14} color={Colors.mainColour1} />
                      </View>
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
                  <RankCell ranking={row.ranking} scope={row.rankingScope} />

                  {onPressRow && (
                    <View style={[styles.chevronCol, styles.centerAlign]}>
                      <Ionicons name="chevron-forward" size={16} color={Colors.gray300} />
                    </View>
                  )}
                </Pressable>
              );
            })}
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
  accentBar: { height: 4, backgroundColor: Colors.mainColour1 },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 14,
  },
  titleBadge: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
  },
  sectionTitle: { fontSize: 16, flex: 1 },
  viewAllButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    backgroundColor: Colors.blue50,
    borderRadius: Radius.pill,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  viewAllPressed: { opacity: 0.7 },
  countPill: {
    minWidth: 30,
    alignItems: "center",
    backgroundColor: Colors.blue50,
    borderRadius: Radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: HEADER_TINT,
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate200,
    borderTopWidth: 1,
    borderTopColor: Colors.slate100,
    paddingVertical: 8,
    gap: 1,
  },
  headerLabel: { textTransform: "uppercase", letterSpacing: 0.5 },
  dataRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderBottomWidth: 1,
    borderBottomColor: Colors.slate100,
    paddingVertical: 12,
    backgroundColor: Colors.white,
  },
  stripedRow: { backgroundColor: STRIPE },
  pressedRow: { backgroundColor: Colors.blue50 },
  emptyRow: { paddingVertical: 26, paddingHorizontal: 16, alignItems: "center", gap: 8 },
  emptyIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.gray100,
    alignItems: "center",
    justifyContent: "center",
  },
  cell: { paddingHorizontal: 6, alignItems: "center", justifyContent: "center" },
  serialCol: { width: 52 },
  nameCol: { width: 140 },
  statusCol: { width: 120 },
  dateCol: { width: 140 },
  scoreCol: { width: 120 },
  rankCol: { width: 100 },
  chevronCol: { width: 28 },
  centerText: { textAlign: "center" },
  centerAlign: { alignItems: "center", justifyContent: "center" },
  serialBadge: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: Colors.blue50,
    borderWidth: 1,
    borderColor: "#D6E6FF",
    alignItems: "center",
    justifyContent: "center",
  },
  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: Radius.pill,
    borderWidth: 1,
  },
  dateWrap: { flexDirection: "row", alignItems: "center", gap: 8 },
  dateIcon: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
  },
  scorePill: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 2,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: Radius.pill,
  },
  scoreTrack: { width: 56, height: 4, borderRadius: 2, backgroundColor: Colors.gray100, marginTop: 5, overflow: "hidden" },
  scoreFill: { height: 4, borderRadius: 2 },
  rankPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 11,
    paddingVertical: 5,
    borderRadius: Radius.pill,
    borderWidth: 1,
  },
  rankScope: { marginTop: 2 },
});
