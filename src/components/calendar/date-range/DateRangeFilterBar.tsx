import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import CalenderIcon from "@/assets/images/svg/calender.svg";
import { Colors } from "@/theme/colors";
import { formatDisplayDate } from "../calendarUtils";

type DateRangeFilterBarProps = {
  selectedStart: Date | null;
  selectedEnd: Date | null;
  onToggleExpand: () => void;
  onFilterPress: () => void;
};

export default function DateRangeFilterBar({ selectedStart, selectedEnd, onToggleExpand, onFilterPress }: DateRangeFilterBarProps) {
  return (
    <View style={styles.topFilterBar}>
      <Pressable style={styles.dateBox} onPress={onToggleExpand} accessibilityRole="button" accessibilityLabel="Select Start Date">
        <CalenderIcon width={13} height={13} color={Colors.mainColour1} stroke={Colors.mainColour1} />
        <AppText style={styles.dateBoxText}>{selectedStart ? formatDisplayDate(selectedStart) : "Select Date"}</AppText>
      </Pressable>

      <Ionicons name="arrow-forward" size={13} color={Colors.gray400} />

      <Pressable style={styles.dateBox} onPress={onToggleExpand} accessibilityRole="button" accessibilityLabel="Select End Date">
        <CalenderIcon width={13} height={13} color={Colors.mainColour1} stroke={Colors.mainColour1} />
        <AppText style={styles.dateBoxText}>{selectedEnd ? formatDisplayDate(selectedEnd) : "Select Date"}</AppText>
      </Pressable>

      <Pressable style={styles.filterButton} onPress={onFilterPress} accessibilityRole="button" accessibilityLabel="Filter">
        <CalenderIcon width={13} height={13} color={Colors.white} stroke={Colors.white} />
        <AppText style={styles.filterButtonText}>Filter</AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  topFilterBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 4,
  },
  dateBox: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.gray300,
    borderRadius: 8,
    paddingHorizontal: 4,
    paddingVertical: 6,
  },
  dateBoxText: {
    fontSize: 9.5,
    color: Colors.gray700,
    fontWeight: "500",
  },
  filterButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    backgroundColor: Colors.mainColour1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  filterButtonText: {
    fontSize: 10,
    color: Colors.white,
    fontWeight: "700",
  },
});
