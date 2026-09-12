import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, View } from "react-native";

import CalendarIcon from "@/assets/images/svg/calender2.svg";
import ClockIcon from "@/assets/images/svg/clock.svg";
import LocationIcon from "@/assets/images/svg/location.svg";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

export type AccessGrantedDetail = {
  label: string;
  value: string;
  icon: keyof typeof Ionicons.glyphMap;
};

type DetailsCardProps = {
  details: AccessGrantedDetail[];
};

export default function DetailsCard({ details }: DetailsCardProps) {
  return (
    <View style={styles.detailsCard}>
      {details.map((detail, index) => (
        <DetailRow key={detail.label} {...detail} isLast={index === details.length - 1} />
      ))}
    </View>
  );
}

function DetailRow({ label, value, icon, isLast }: AccessGrantedDetail & { isLast: boolean }) {
  return (
    <View style={[styles.detailRow, !isLast && styles.detailBorder]}>
      <View style={styles.detailIcon}>
        {icon === "calendar-outline" || label.toLowerCase().includes("session") || label.toLowerCase().includes("date") ? (
          <CalendarIcon width={20} height={20} color="#1CB07D" />
        ) : icon === "time-outline" || label.toLowerCase().includes("time") || label.toLowerCase().includes("checked") ? (
          <ClockIcon width={20} height={20} color="#1CB07D" />
        ) : icon === "location-outline" || label.toLowerCase().includes("location") ? (
          <LocationIcon width={18} height={22} color="#1CB07D" />
        ) : (
          <Ionicons name={icon} size={22} color={Colors.success} />
        )}
      </View>
      <View style={styles.detailTextColumn}>
        <AppText variant="caption" color={Colors.gray600}>
          {label}
        </AppText>
        <AppText variant="label" color="#111827" weight={FontWeight.semiBold}>
          {value}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  detailsCard: {
    width: "100%",
    flex: 1,
    minHeight: 290,
    backgroundColor: Colors.white,
    borderRadius: 24,
    paddingHorizontal: 18,
    paddingVertical: 14,
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 8, blur: 20, opacity: 0.09, elevation: 5 }),
  },
  detailRow: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    paddingVertical: 8,
  },
  detailBorder: { borderBottomWidth: 1, borderBottomColor: Colors.gray200 },
  detailIcon: {
    width: 42,
    height: 42,
    borderRadius: 10,
    backgroundColor: "#D8F8EB",
    alignItems: "center",
    justifyContent: "center",
  },
  detailTextColumn: {
    flex: 1,
    gap: 2,
  },
});
