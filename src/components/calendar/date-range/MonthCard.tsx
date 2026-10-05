import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import { Colors } from "@/theme/colors";
import CalendarGrid from "../CalendarGrid";
import CalendarHeader from "../CalendarHeader";
import { formatMonthDay } from "../calendarUtils";
import { useMonthYear } from "./useMonthYear";

type MonthCardProps = {
  title: string;
  summaryLabel: string;
  monthYear: ReturnType<typeof useMonthYear>;
  selectedStart: Date;
  selectedEnd: Date;
  /** null = nothing picked (shows "Not set"). */
  summaryDate: Date | null;
  onSelectDate: (date: Date) => void;
  onClear: () => void;
  isDateDisabled?: (date: Date) => boolean;
};

export default function MonthCard({
  title,
  summaryLabel,
  monthYear,
  selectedStart,
  selectedEnd,
  summaryDate,
  onSelectDate,
  onClear,
  isDateDisabled,
}: MonthCardProps) {
  const { month, year, setMonth, setYear, prevMonth, nextMonth } = monthYear;

  // Clear also brings the calendar back to the current month and year.
  const handleClear = () => {
    const today = new Date();
    setMonth(today.getMonth());
    setYear(today.getFullYear());
    onClear();
  };

  return (
    <View style={styles.card}>
      <View style={styles.titleRow}>
        <AppText style={styles.cardTitle}>{title}</AppText>
        <Pressable onPress={handleClear} hitSlop={6}>
          <AppText style={styles.clearText}>Clear</AppText>
        </Pressable>
      </View>

      <CalendarHeader
        currentMonth={month}
        currentYear={year}
        onPrevMonth={prevMonth}
        onNextMonth={nextMonth}
        onSelectMonth={setMonth}
        onSelectYear={setYear}
      />

      <CalendarGrid
        year={year}
        month={month}
        startDate={selectedStart}
        endDate={selectedEnd}
        onSelectDate={onSelectDate}
        isDateDisabled={isDateDisabled}
      />

      <View style={styles.summaryBadge}>
        <AppText style={styles.summaryLabel}>{summaryLabel}</AppText>
        <AppText style={styles.summaryValue}>{summaryDate ? formatMonthDay(summaryDate) : "Not set"}</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    padding: 4,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 9.5,
    fontWeight: "700",
    color: Colors.black,
    letterSpacing: 0.5,
  },
  clearText: {
    fontSize: 8.5,
    fontWeight: "600",
    color: Colors.mainColour1,
  },
  summaryBadge: {
    marginTop: 6,
    backgroundColor: Colors.blue50,
    borderRadius: 6,
    paddingVertical: 3.5,
    paddingHorizontal: 4,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  summaryLabel: {
    fontSize: 8,
    color: Colors.gray700,
  },
  summaryValue: {
    fontSize: 8.5,
    color: Colors.mainColour1,
    fontWeight: "700",
  },
});
