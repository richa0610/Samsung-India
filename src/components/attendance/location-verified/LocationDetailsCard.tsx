import { ReactNode } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import CalendarIcon from "@/assets/images/svg/calender2.svg";
import ClockIcon from "@/assets/images/svg/clock.svg";
import LocationIcon from "@/assets/images/svg/location.svg";
import AppText from "@/components/ui/AppText";
import { Breakpoints } from "@/theme/breakpoints";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";
import { LocationVerifiedInfo } from "./types";

type LocationDetailsCardProps = {
  info: LocationVerifiedInfo;
  onContinue: () => void;
};

export default function LocationDetailsCard({ info, onContinue }: LocationDetailsCardProps) {
  const rows: { label: string; value: string; renderIcon: () => ReactNode }[] = [
    { label: "Session", value: info.sessionTitle, renderIcon: () => <CalendarIcon width={22} height={22} color="#1CB07D" /> },
    { label: "Session Time", value: info.sessionTime, renderIcon: () => <ClockIcon width={22} height={22} color="#1CB07D" /> },
    { label: "Date", value: info.date, renderIcon: () => <CalendarIcon width={22} height={22} color="#1CB07D" /> },
    { label: "Venue", value: info.location, renderIcon: () => <LocationIcon width={20} height={24} color="#1CB07D" /> },
    // Only shown once the on-device reverse-geocode resolves - the trainee's
    // own detected position, not the venue's configured address.
    ...(info.liveLocation
      ? [{ label: "Your Location", value: info.liveLocation, renderIcon: () => <LocationIcon width={20} height={24} color="#1CB07D" /> }]
      : []),
  ];

  return (
    <View style={styles.content}>
      <View style={styles.detailsCard}>
        {rows.map((row, index) => (
          <View key={row.label} style={[styles.detailRow, index !== rows.length - 1 && styles.detailBorder]}>
            <View style={styles.detailIcon}>{row.renderIcon()}</View>
            <View style={styles.detailTextColumn}>
              <AppText style={styles.detailLabel} color={Colors.gray600} weight={FontWeight.regular}>
                {row.label}
              </AppText>
              <AppText style={styles.detailValue} color="#111827" weight={FontWeight.medium}>
                {row.value}
              </AppText>
            </View>
          </View>
        ))}
      </View>

      <Pressable style={styles.continueButton} onPress={onContinue} accessibilityRole="button" accessibilityLabel="Great, Continue">
        <AppText style={styles.continueButtonText} color={Colors.white} weight={FontWeight.medium}>
          Great, Continue
        </AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  content: {
    width: "100%",
    maxWidth: Breakpoints.mobileMaxWidth,
    alignSelf: "center",
    paddingHorizontal: 20,
    marginTop: -210,
    flex: 1,
    justifyContent: "space-between",
    paddingBottom: 24,
  },
  detailsCard: {
    width: "100%",
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 27,
    paddingHorizontal: 20,
    paddingVertical: 14,
    justifyContent: "space-between",
    ...createShadow({ x: 0, y: 8, blur: 20, opacity: 0.09, elevation: 5 }),
  },
  detailRow: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    paddingVertical: 10,
  },
  detailBorder: {
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray200,
  },
  detailIcon: {
    width: 44,
    height: 44,
    borderRadius: 11,
    backgroundColor: "#D8F8EB",
    alignItems: "center",
    justifyContent: "center",
  },
  detailTextColumn: {
    flex: 1,
    gap: 3,
  },
  detailLabel: {
    fontSize: 11.5,
  },
  detailValue: {
    fontSize: 14,
  },
  continueButton: {
    width: "100%",
    height: 52,
    marginTop: 22,
    borderRadius: 12,
    backgroundColor: "#00A86B",
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 4, blur: 10, opacity: 0.12, elevation: 3 }),
  },
  continueButtonText: {
    fontSize: 18,
  },
});
