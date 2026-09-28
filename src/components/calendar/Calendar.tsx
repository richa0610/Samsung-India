import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { DateRangeFilterBar, MonthCard, RangeInfoBanner, useMonthYear } from "./date-range";
import { DatePreset, DateRange, startOfDay } from "./calendarUtils";

type CalendarProps = {
  range: DateRange;
  preset?: DatePreset;
  defaultExpanded?: boolean;
  onApply: (range: DateRange, preset: DatePreset) => void;
};

// Stands in for "no date picked" where a calendar grid needs a Date to compare
// against - far enough in the past that nothing on screen is highlighted.
const NO_DATE = new Date(0);

export default function Calendar({ range, preset = "custom", defaultExpanded = false, onApply }: CalendarProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  // null = that side was cleared and has no date picked.
  const [selectedStart, setSelectedStart] = useState<Date | null>(range.start);
  const [selectedEnd, setSelectedEnd] = useState<Date | null>(range.end);
  const [activePreset, setActivePreset] = useState<DatePreset>(preset);

  const fromMonthYear = useMonthYear(range.start);
  const toMonthYear = useMonthYear(range.end);

  const handleToggleExpand = () => {
    setIsExpanded((prev) => !prev);
  };

  // Neither calendar restricts which date (or year) can be picked.
  // Picking a date only updates the local From/To selection - it does not
  // refresh the dashboard. The dashboard only re-fetches when the trainer
  // taps "Filter" (see `handleFilterPress`), so choosing From then To
  // doesn't trigger two separate loads with a half-picked range. If the two
  // dates would end up the wrong way round, the other side follows.
  const handleSelectStartDate = (date: Date) => {
    const newStart = startOfDay(date);
    setSelectedStart(newStart);
    setActivePreset("custom");
    if (selectedEnd && newStart.getTime() > selectedEnd.getTime()) setSelectedEnd(newStart);
  };

  const handleSelectEndDate = (date: Date) => {
    const newEnd = startOfDay(date);
    setSelectedEnd(newEnd);
    setActivePreset("custom");
    if (selectedStart && selectedStart.getTime() > newEnd.getTime()) setSelectedStart(newEnd);
  };

  // "Clear" empties just that one calendar's date.
  const handleClearStart = () => {
    setSelectedStart(null);
    setActivePreset("custom");
  };
  const handleClearEnd = () => {
    setSelectedEnd(null);
    setActivePreset("custom");
  };

  const handleFilterPress = () => {
    // A side left empty defaults to today (the backend needs both ends).
    const today = startOfDay(new Date());
    let start = selectedStart ?? today;
    let end = selectedEnd ?? today;
    if (start.getTime() > end.getTime()) [start, end] = [end, start];
    setSelectedStart(start);
    setSelectedEnd(end);
    onApply({ start, end }, selectedStart || selectedEnd ? activePreset : "today");
    setIsExpanded((prev) => !prev);
  };

  return (
    <View style={styles.container}>
      <DateRangeFilterBar
        selectedStart={selectedStart}
        selectedEnd={selectedEnd}
        onToggleExpand={handleToggleExpand}
        onFilterPress={handleFilterPress}
      />

      {isExpanded && (
        <View style={styles.expandedContent}>
          <View style={styles.divider} />

          <View style={styles.calendarsRow}>
            <MonthCard
              title="FROM :"
              summaryLabel="From Date"
              monthYear={fromMonthYear}
              selectedStart={selectedStart ?? NO_DATE}
              selectedEnd={selectedStart ?? NO_DATE}
              summaryDate={selectedStart}
              onSelectDate={handleSelectStartDate}
              onClear={handleClearStart}
            />

            <View style={styles.arrowContainer}>
              <Ionicons name="arrow-forward" size={14} color={Colors.mainColour1} />
            </View>

            <MonthCard
              title="TO :"
              summaryLabel="To Date"
              monthYear={toMonthYear}
              selectedStart={selectedEnd ?? NO_DATE}
              selectedEnd={selectedEnd ?? NO_DATE}
              summaryDate={selectedEnd}
              onSelectDate={handleSelectEndDate}
              onClear={handleClearEnd}
            />
          </View>

          <RangeInfoBanner selectedStart={selectedStart} selectedEnd={selectedEnd} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: Colors.borderLight,
    padding: 10,
    marginHorizontal: 10,
    ...Shadows.card,
  },
  expandedContent: {
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderLight,
    marginTop: 8,
    marginBottom: 6,
    marginHorizontal: 2,
  },
  calendarsRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 2,
  },
  arrowContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 0,
    width: 14,
  },
});
