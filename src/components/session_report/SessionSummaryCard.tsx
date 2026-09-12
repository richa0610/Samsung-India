import { StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import SessionSummaryField from "./SessionSummaryField";
import { SessionReportSummary } from "./sessionReportTypes";

type SessionSummaryCardProps = {
  summary: SessionReportSummary;
};

export default function SessionSummaryCard({ summary }: SessionSummaryCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.titleBar}>
        <View style={styles.titleAccent} />
        <AppText style={styles.title} weight={FontWeight.semiBold}>SESSION SUMMARY</AppText>
      </View>

      <View style={styles.grid}>
        <SessionSummaryField icon="document-text-outline" label="Conference ID" value={summary.conferenceId} />
        <SessionSummaryField icon="person-outline" label="Session Name" value={summary.sessionName} />
        <SessionSummaryField icon="calendar-outline" label="Date" value={summary.date} />
        <SessionSummaryField icon="location-outline" label="State" value={summary.state} />
        <SessionSummaryField icon="time-outline" label="Schedule" value={summary.schedule} />
        <SessionSummaryField icon="hourglass-outline" label="Duration" value={summary.duration} />
      </View>

      <SessionSummaryField icon="link-outline" label="Venue/Link" value={summary.venueLink} fullWidth />

      <View style={styles.noteBox}>
        <AppText style={styles.noteText} color={Colors.gray600}>
          Note: All times are shown in (Asia/Kolkata) India Standard Time (IST).
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xl,
    borderWidth: 1,
    borderColor: Colors.gray200,
    marginHorizontal: 14,
    padding: 12,
    ...Shadows.card,
  },
  titleBar: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 },
  titleAccent: { width: 4, height: 14, borderRadius: 2, backgroundColor: Colors.mainColour1 },
  title: { fontSize: Fonts.bodySm, letterSpacing: 0.3 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  noteBox: {
    marginTop: 10,
    borderLeftWidth: 3,
    borderLeftColor: Colors.mainColour1,
    backgroundColor: "#F0F6FF",
    borderRadius: Radius.md,
    padding: 10,
  },
  noteText: { fontSize: Fonts.overline },
});
