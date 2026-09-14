import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

export type MoreMenuItem =
  | "New Training"
  | "Training List"
  | "Pending Training"
  | "View Reports"
  | "New Trainee"
  | "Trainee List"
  | "Pending Trainee"
  | "View Sessions"
  | "Attendance List"
  | "Confirmed Attendance"
  | "Pending Attendance";

const MENU_ITEMS: { label: MoreMenuItem; icon: keyof typeof Ionicons.glyphMap }[] = [
  { label: "New Training", icon: "school-outline" },
  { label: "Training List", icon: "list-outline" },
  { label: "Pending Training", icon: "document-text-outline" },
  { label: "View Reports", icon: "bar-chart-outline" },
  { label: "New Trainee", icon: "person-add-outline" },
  { label: "Trainee List", icon: "people-outline" },
  { label: "Pending Trainee", icon: "clipboard-outline" },
  { label: "View Sessions", icon: "chatbubbles-outline" },
  { label: "Attendance List", icon: "reader-outline" },
  { label: "Confirmed Attendance", icon: "calendar-outline" },
  { label: "Pending Attendance", icon: "hourglass-outline" },
];

type MoreMenuGridProps = {
  onSelect: (label: MoreMenuItem) => void;
};

export default function MoreMenuGrid({ onSelect }: MoreMenuGridProps) {
  return (
    <View style={styles.grid}>
      {MENU_ITEMS.map((item) => (
        <Pressable key={item.label} style={styles.item} onPress={() => onSelect(item.label)} hitSlop={4}>
          <View style={styles.iconWrap}>
            <Ionicons name={item.icon} size={22} color={Colors.mainColour1} />
          </View>
          <AppText style={styles.label} weight={FontWeight.medium}>
            {item.label}
          </AppText>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 20,
  },
  item: {
    width: "25%",
    alignItems: "center",
    gap: 6,
    paddingVertical: 12,
  },
  iconWrap: {
    width: 52,
    height: 52,
    borderRadius: Radius.lg,
    backgroundColor: "#EAF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    fontSize: Fonts.caption,
    textAlign: "center",
    lineHeight: 14,
  },
});
