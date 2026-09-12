import { Pressable, StyleSheet } from "react-native";

import { DataTableColumn } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import { StatusPill } from "@/components/ui/StatusPill";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { formatDisplayDate } from "@/utils/formatDisplayDate";
import { AttendanceListItem } from "@/api/attendanceList";

export function useAttendanceListColumns(
  onViewCandidate: (row: AttendanceListItem) => void
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
    {
      key: "attendanceStatus",
      header: "Attendance",
      minWidth: 92,
      render: (row) =>
        row.attendanceStatus === "Present" ? (
          <StatusPill label="Present" tone="success" />
        ) : (
          <StatusPill label={row.attendanceStatus} tone="warning" />
        ),
      exportValue: (row) => row.attendanceStatus,
    },
    { key: "region", header: "Region", minWidth: 90, exportValue: (row) => row.region ?? "--" },
    { key: "product", header: "Product", minWidth: 140, exportValue: (row) => row.product ?? "--" },
    { key: "session", header: "Session", minWidth: 100, exportValue: (row) => row.session ?? "--" },
    { key: "audienceType", header: "Audience Type", minWidth: 100, exportValue: (row) => row.audienceType ?? "--" },
    {
      key: "conferenceDate",
      header: "Conference Date",
      minWidth: 150,
      exportValue: (row) => formatDisplayDate(row.conferenceDate),
      searchValue: (row) => row.conferenceDate ?? "",
    },
    { key: "trainerName", header: "Trainer", minWidth: 118, exportValue: (row) => row.trainerName ?? "--" },
    { key: "trainerHoId", header: "Trainer HO ID", minWidth: 110, exportValue: (row) => row.trainerHoId ?? "--" },
    { key: "participantHoId", header: "Participant HO ID", minWidth: 120, exportValue: (row) => row.participantHoId ?? "--" },
    { key: "participantName", header: "Participant Name", minWidth: 150, exportValue: (row) => row.participantName },
    {
      key: "trainerTrainingsTotal",
      header: "Trainings (This Trainer)",
      minWidth: 120,
      render: (row) => <AppText style={styles.cellText}>{row.trainerTrainingsTotal}</AppText>,
      exportValue: (row) => String(row.trainerTrainingsTotal),
    },
    {
      key: "trainerTrainingsPresent",
      header: "Attended",
      minWidth: 84,
      render: (row) => <AppText style={styles.cellText}>{row.trainerTrainingsPresent}</AppText>,
      exportValue: (row) => String(row.trainerTrainingsPresent),
    },
    {
      key: "trainerTrainingsPending",
      header: "Pending",
      minWidth: 80,
      render: (row) => <AppText style={styles.cellText}>{row.trainerTrainingsPending}</AppText>,
      exportValue: (row) => String(row.trainerTrainingsPending),
    },
    { key: "phone", header: "Phone No", minWidth: 110, exportValue: (row) => row.phone ?? "--" },
    { key: "state", header: "State", minWidth: 110, exportValue: (row) => row.state ?? "--" },
    { key: "location", header: "Location", minWidth: 120, exportValue: (row) => row.location ?? "--" },
    {
      key: "reportingManagerOfPromoter",
      header: "Reporting Manager of Promoter",
      minWidth: 160,
      exportValue: (row) => row.reportingManagerOfPromoter ?? "--",
    },
    { key: "checkIn", header: "Check-In", minWidth: 90, exportValue: (row) => row.checkIn ?? "-" },
    { key: "checkOut", header: "Check-Out", minWidth: 90, exportValue: (row) => row.checkOut ?? "-" },
    { key: "postTestScore", header: "Post Test Score", minWidth: 130, exportValue: (row) => row.postTestScore ?? "--" },
    {
      key: "postTestScoreSummary",
      header: "Post Test Score Summary",
      minWidth: 220,
      exportValue: (row) => row.postTestScoreSummary ?? "--",
    },
    { key: "sessionTypeMethod", header: "Session Type Method", minWidth: 130, exportValue: (row) => row.sessionTypeMethod ?? "--" },
    { key: "attendanceId", header: "Attendance ID", minWidth: 170, exportValue: (row) => row.attendanceId },
    { key: "conferenceId", header: "Conference ID", minWidth: 130, exportValue: (row) => row.conferenceId ?? "--" },
    { key: "lastUpdates", header: "Last Updates", minWidth: 140, exportValue: (row) => row.lastUpdates ?? "--" },
    {
      key: "report",
      header: "Report",
      minWidth: 150,
      sortable: false,
      render: (row) => (
        <Pressable style={styles.reportButton} onPress={() => onViewCandidate(row)} hitSlop={4}>
          <AppText style={styles.reportButtonText} color={Colors.white} weight={FontWeight.semiBold}>Candidate Report</AppText>
        </Pressable>
      ),
      exportValue: () => "Candidate Report",
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
