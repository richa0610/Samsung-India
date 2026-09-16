import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { SearchableSelect, SelectOption } from "@/components/ui/SearchableSelect";
import { DateTimeField } from "@/components/training/add-training/DateTimeField";
import { Colors } from "@/theme/colors";
import { SessionFilters } from "./sessionsUtils";

type SessionsFilterPanelProps = {
  filters: SessionFilters;
  onChange: (patch: Partial<SessionFilters>) => void;
  locationOptions: SelectOption[];
  sessionTypeOptions: SelectOption[];
  // "dateOnly" renders just the Date Range fields, for the header's calendar shortcut.
  variant?: "full" | "dateOnly";
};

export default function SessionsFilterPanel({
  filters,
  onChange,
  locationOptions,
  sessionTypeOptions,
  variant = "full",
}: SessionsFilterPanelProps) {
  return (
    <View style={styles.card}>
      <AppText style={styles.sectionLabel}>Date Range</AppText>
      <View style={styles.dateRow}>
        <View style={styles.dateField}>
          <DateTimeField
            value={filters.fromDate}
            mode="date"
            compact
            onChange={(formatted) => onChange({ fromDate: formatted })}
          />
        </View>
        <View style={styles.dateField}>
          <DateTimeField
            value={filters.toDate}
            mode="date"
            compact
            onChange={(formatted) => onChange({ toDate: formatted })}
          />
        </View>
      </View>

      {variant === "full" && (
        <>
          <AppText style={styles.sectionLabel}>Location</AppText>
          <SearchableSelect
            placeholder="All Locations"
            value={filters.location}
            options={locationOptions}
            onSelect={(option) => onChange({ location: option.value })}
            icon="location-outline"
            compact
          />

          <AppText style={styles.sectionLabel}>Session Type</AppText>
          <SearchableSelect
            placeholder="All Types"
            value={filters.sessionType}
            options={sessionTypeOptions}
            onSelect={(option) => onChange({ sessionType: option.value })}
            icon="list-outline"
            compact
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingTop: 12,
    paddingBottom: 2,
    marginTop: 12,
  },
  sectionLabel: {
    fontSize: 10.5,
    fontWeight: "700",
    color: "#9CA3AF",
    letterSpacing: 0.6,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  dateRow: {
    flexDirection: "row",
    gap: 10,
  },
  dateField: {
    flex: 1,
  },
});
