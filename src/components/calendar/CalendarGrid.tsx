import { StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import CalendarDay from "./CalendarDay";
import {
  WEEKDAYS,
  generateMonthGrid,
  isBetweenDates,
  isSameDay,
} from "./calendarUtils";

type CalendarGridProps = {
  year: number;
  month: number;
  startDate: Date | null;
  endDate: Date | null;
  onSelectDate: (date: Date) => void;
  isDateDisabled?: (date: Date) => boolean;
};

export default function CalendarGrid({
  year,
  month,
  startDate,
  endDate,
  onSelectDate,
  isDateDisabled,
}: CalendarGridProps) {
  const days = generateMonthGrid(year, month);

  return (
    <View style={styles.container}>
      {/* Weekday Row */}
      <View style={styles.weekdaysRow}>
        {WEEKDAYS.map((weekday) => (
          <AppText key={weekday} style={styles.weekdayLabel}>
            {weekday}
          </AppText>
        ))}
      </View>

      {/* Days Grid */}
      <View style={styles.grid}>
        {days.map((item, index) => {
          const isStart = isSameDay(item.date, startDate);
          const isEnd = isSameDay(item.date, endDate);
          const inRange = isBetweenDates(item.date, startDate, endDate);
          const disabled = isDateDisabled ? isDateDisabled(item.date) : false;

          return (
            <CalendarDay
              key={`${item.date.toISOString()}-${index}`}
              date={item.date}
              dayNumber={item.dayNumber}
              isCurrentMonth={item.isCurrentMonth}
              isStart={isStart}
              isEnd={isEnd}
              isInRange={inRange}
              disabled={disabled}
              onSelect={onSelectDate}
            />
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
  },
  weekdaysRow: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 3,
  },
  weekdayLabel: {
    width: 18.5,
    textAlign: "center",
    fontSize: 8,
    color: "#6B7280",
    fontWeight: "500",
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-around",
  },
});
