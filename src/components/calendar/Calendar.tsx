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

export default function Calendar({ range, preset = "custom", defaultExpanded = false, onApply }: CalendarProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const [selectedStart, setSelectedStart] = useState<Date>(range.start);
  const [selectedEnd, setSelectedEnd] = useState<Date>(range.end);
  const [activePreset, setActivePreset] = useState<DatePreset>(preset);

  const fromMonthYear = useMonthYear(range.start);
  const toMonthYear = useMonthYear(range.end);

  const handleToggleExpand = () => {
    setIsExpanded((prev) => !prev);
  };

  // From must always be strictly before To - each calendar only ever
  // highlights its own single date (not both), and the To calendar disables
  // any date on or before the currently selected From date (and vice versa)
  // so an invalid or equal-day range can't be picked in the first place.
  const nextDay = (date: Date) =>
    new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1);

  const isFromDateDisabled = (date: Date) => date.getTime() >= selectedEnd.getTime();
  const isToDateDisabled = (date: Date) => date.getTime() <= selectedStart.getTime();

  // Picking a date only updates the local From/To selection - it does not
  // refresh the dashboard. The dashboard only re-fetches when the trainer
  // taps "Filter" (see `handleFilterPress`), so choosing From then To
  // doesn't trigger two separate loads with a half-picked range.
  const handleSelectStartDate = (date: Date) => {
    const newStart = startOfDay(date);
    setSelectedStart(newStart);
    setActivePreset("custom");

    if (newStart.getTime() >= selectedEnd.getTime()) {
      setSelectedEnd(nextDay(newStart));
    }
  };

  const handleSelectEndDate = (date: Date) => {
    const newEnd = startOfDay(date);
    if (newEnd.getTime() <= selectedStart.getTime()) {
      // The grid already disables these dates - defensive no-op only.
      return;
    }
    setSelectedEnd(newEnd);
    setActivePreset("custom");
  };

  // "Clear" resets just that one calendar's date back to today, independent
  // of the other calendar - not a true deselect, since the backend query
  // and the From<To invariant both require a valid date on each side.
  const handleClearStart = () => handleSelectStartDate(new Date());
  const handleClearEnd = () => {
    const today = startOfDay(new Date());
    if (today.getTime() > selectedStart.getTime()) {
      handleSelectEndDate(today);
    } else {
      setSelectedEnd(nextDay(selectedStart));
      setActivePreset("custom");
    }
  };

  const handleFilterPress = () => {
    onApply({ start: selectedStart, end: selectedEnd }, activePreset);
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
              selectedStart={selectedStart}
              selectedEnd={selectedStart}
              summaryDate={selectedStart}
              onSelectDate={handleSelectStartDate}
              onClear={handleClearStart}
              isDateDisabled={isFromDateDisabled}
            />

            <View style={styles.arrowContainer}>
              <Ionicons name="arrow-forward" size={14} color={Colors.mainColour1} />
            </View>

            <MonthCard
              title="TO :"
              summaryLabel="To Date"
              monthYear={toMonthYear}
              selectedStart={selectedEnd}
              selectedEnd={selectedEnd}
              summaryDate={selectedEnd}
              onSelectDate={handleSelectEndDate}
              onClear={handleClearEnd}
              isDateDisabled={isToDateDisabled}
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
    borderColor: "#EAECF0",
    padding: 10,
    marginHorizontal: 10,
    ...Shadows.card,
  },
  expandedContent: {
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: "#EAECF0",
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
