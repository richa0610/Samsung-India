import { Colors } from "@/theme/colors";
import { Pressable, StyleSheet } from "react-native";
import AppText from "@/components/ui/AppText";
import { isToday } from "./calendarUtils";

type CalendarDayProps = {
  date: Date;
  dayNumber: number;
  isCurrentMonth: boolean;
  isStart: boolean;
  isEnd: boolean;
  isInRange: boolean;
  disabled?: boolean;
  onSelect: (date: Date) => void;
};

export default function CalendarDay({
  date,
  dayNumber,
  isCurrentMonth,
  isStart,
  isEnd,
  isInRange,
  disabled = false,
  onSelect,
}: CalendarDayProps) {
  const isSelected = isStart || isEnd;
  const isCurrentDay = isToday(date);

  return (
    <Pressable
      style={[
        styles.cell,
        isInRange && !isSelected && styles.cellInRange,
        isSelected && styles.cellSelected,
      ]}
      disabled={disabled}
      onPress={() => onSelect(date)}
    >
      <AppText
        style={[
          styles.text,
          !isCurrentMonth && styles.textOutside,
          isInRange && !isSelected && styles.textInRange,
          isCurrentDay && !isSelected && styles.textToday,
          isSelected && styles.textSelected,
          disabled && !isSelected && styles.textDisabled,
        ]}
      >
        {dayNumber}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  cell: {
    width: 18.5,
    height: 18.5,
    alignItems: "center",
    justifyContent: "center",
    marginVertical: 1,
    borderRadius: 4,
  },
  cellSelected: {
    backgroundColor: Colors.mainColour1,
  },
  cellInRange: {
    backgroundColor: Colors.blue50,
  },
  text: {
    fontSize: 8.5,
    color: Colors.gray800,
    fontWeight: "500",
  },
  textSelected: {
    color: Colors.white,
    fontWeight: "700",
  },
  textInRange: {
    color: Colors.mainColour1,
    fontWeight: "600",
  },
  textOutside: {
    color: Colors.gray300,
  },
  textDisabled: {
    color: Colors.gray300,
  },
  textToday: {
    fontWeight: "700",
    color: Colors.mainColour1,
  },
});
