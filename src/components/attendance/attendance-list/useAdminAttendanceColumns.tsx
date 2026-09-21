import { Pressable, StyleSheet } from "react-native";

import { AttendanceListItem } from "@/api/attendanceList";
import AppText from "@/components/ui/AppText";
import { DataTableColumn } from "@/components/ui/DataTable";
import { StatusPill } from "@/components/ui/StatusPill";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { formatDisplayDate } from "@/utils/formatDisplayDate";

const text = (key: string, header: string, minWidth: number, value: (row: AttendanceListItem) => string | null | undefined): DataTableColumn<AttendanceListItem> => ({
  key,
  header,
  minWidth,
  exportValue: (row) => value(row) ?? "",
});

/** The admin's org-wide attendance table (Attendance List / Confirmed / Pending). */
export function useAdminAttendanceColumns(
  onCandidateReport: (row: AttendanceListItem) => void,
): DataTableColumn<AttendanceListItem>[] {
  return [
    {
      key: "slNo",
      header: "Sl No.",
      minWidth: 48,
      sortable: false,
      render: (_row, index) => <AppText style={styles.cellText}>{index + 1}</AppText>,
      exportValue: (_row, index) => String(index + 1),
    },
    text("region", "Region", 80, (row) => row.region),
    text("product", "Product", 140, (row) => row.product),
    text("session", "Session", 140, (row) => row.session),
    text("audienceType", "Audience Type", 120, (row) => row.audienceType),
    {
      key: "conferenceDate",
      header: "Conference Date",
      minWidth: 150,
      exportValue: (row) => formatDisplayDate(row.conferenceDate),
      searchValue: (row) => row.conferenceDate ?? "",
    },
    text("trainerName", "Trainer", 118, (row) => row.trainerName),
    text("trainerHoId", "Trainer HO ID", 118, (row) => row.trainerHoId),
    text("participantHoId", "Participant HO ID", 124, (row) => row.participantHoId),
    text("participantName", "Participant Name", 150, (row) => row.participantName),
    text("phone", "Phone No", 110, (row) => row.phone),
    text("state", "State", 100, (row) => row.state),
    text("location", "Location", 110, (row) => row.location),
    text("reportingManagerOfPromoter", "Reporting Manager of Promoter", 190, (row) => row.reportingManagerOfPromoter),
    {
      key: "attendanceStatus",
      header: "Attendance",
      minWidth: 100,
      render: (row) => (
        <StatusPill label={row.attendanceStatus} tone={row.attendanceStatus === "Present" ? "success" : "warning"} />
      ),
      exportValue: (row) => row.attendanceStatus,
    },
    text("checkIn", "Check-In", 90, (row) => row.checkIn),
    text("checkOut", "Check-Out", 90, (row) => row.checkOut),
    text("postTestScore", "Post Test Score", 120, (row) => row.postTestScore),
    text("postTestScoreSummary", "Post Test Score Summary", 230, (row) => row.postTestScoreSummary),
    text("sessionTypeMethod", "Session Type Method", 160, (row) => row.sessionTypeMethod),
    text("attendanceId", "Attendance ID", 170, (row) => row.attendanceId),
    text("conferenceId", "Conference ID", 130, (row) => row.conferenceId),
    text("lastUpdates", "Last Updates", 150, (row) => row.lastUpdates),
    {
      key: "report",
      header: "Report",
      minWidth: 150,
      sortable: false,
      render: (row) => (
        <Pressable style={styles.reportButton} onPress={() => onCandidateReport(row)} hitSlop={4}>
          <AppText style={styles.reportButtonText} color={Colors.white} weight={FontWeight.semiBold}>
            Candidate Report
          </AppText>
        </Pressable>
      ),
      exportValue: () => "",
    },
  ];
}

const styles = StyleSheet.create({
  cellText: { fontSize: Fonts.overline, textAlign: "center" },
  reportButton: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: Radius.md,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
  },
  reportButtonText: { fontSize: Fonts.overline },
});
