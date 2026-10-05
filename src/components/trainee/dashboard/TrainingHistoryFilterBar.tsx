import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { DateTimeField } from "@/components/training/add-training/DateTimeField";
import { SearchableSelect, SelectOption } from "@/components/ui/SearchableSelect";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

const STATUS_OPTIONS: SelectOption[] = [
  { label: "All Status", value: "" },
  { label: "Completed", value: "Completed" },
  { label: "Ongoing", value: "Ongoing" },
  { label: "Not Started", value: "Scheduled" },
  { label: "Missed", value: "Missed" },
  { label: "Absent", value: "Absent" },
];

type TrainingHistoryFilterBarProps = {
  fromDate: string;
  toDate: string;
  onFromDateChange: (value: string) => void;
  onToDateChange: (value: string) => void;
  status: string;
  onStatusChange: (value: string) => void;
  /** Opened from a Dashboard metric card: that card's name, shown as a removable filter. */
  cardLabel?: string | null;
  onClearCard?: () => void;
  onClear: () => void;
  hasFilter: boolean;
};

// Same Date Range filter pattern as the trainer's Sessions screen
// (SessionsFilterPanel) - two DateTimeFields feeding a from/to range,
// compared against each row's raw "YYYY-MM-DD" date, plus a Status select
// filtered against each row's own outcome (TrainingDetailsTable's status).
export default function TrainingHistoryFilterBar({
  fromDate,
  toDate,
  onFromDateChange,
  onToDateChange,
  status,
  onStatusChange,
  cardLabel,
  onClearCard,
  onClear,
  hasFilter,
}: TrainingHistoryFilterBarProps) {
  return (
    <View style={styles.card}>
      {cardLabel ? (
        <View style={styles.cardFilterRow}>
          <AppText style={styles.sectionLabel}>Dashboard Card</AppText>
          <Pressable
            onPress={onClearCard}
            style={styles.cardChip}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel={`Remove the ${cardLabel} filter`}
          >
            <AppText style={styles.cardChipText} weight={FontWeight.bold} color={Colors.mainColour1}>
              {cardLabel}
            </AppText>
            <Ionicons name="close" size={12} color={Colors.mainColour1} />
          </Pressable>
        </View>
      ) : null}
      <View style={styles.headerRow}>
        <AppText style={styles.sectionLabel}>Date Range</AppText>
        {hasFilter && (
          <Pressable onPress={onClear} hitSlop={8} accessibilityRole="button" accessibilityLabel="Clear filters">
            <AppText style={styles.clearText} weight={FontWeight.bold} color={Colors.mainColour1}>
              Clear
            </AppText>
          </Pressable>
        )}
      </View>
      <View style={styles.dateRow}>
        <View style={styles.dateField}>
          <DateTimeField value={fromDate} mode="date" compact onChange={onFromDateChange} />
        </View>
        <View style={styles.dateField}>
          <DateTimeField value={toDate} mode="date" compact onChange={onToDateChange} minimumDate={fromDate ? new Date(fromDate) : undefined} />
        </View>
      </View>

      <AppText style={[styles.sectionLabel, styles.statusLabel]}>Status</AppText>
      <SearchableSelect
        placeholder="All Status"
        value={status}
        options={STATUS_OPTIONS}
        onSelect={(option) => onStatusChange(option.value)}
        icon="filter-outline"
        compact
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 2,
    marginHorizontal: 16,
    marginTop: 14,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  sectionLabel: {
    fontSize: 10.5,
    fontWeight: "700",
    color: Colors.gray400,
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  clearText: { fontSize: 11 },
  cardFilterRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  cardChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: Colors.mainColour1,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  cardChipText: { fontSize: 11 },
  dateRow: {
    flexDirection: "row",
    gap: 10,
  },
  dateField: {
    flex: 1,
  },
  statusLabel: {
    marginTop: 14,
    marginBottom: 8,
  },
});
