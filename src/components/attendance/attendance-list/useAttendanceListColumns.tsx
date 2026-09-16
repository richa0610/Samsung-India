import { StyleSheet } from "react-native";

import { DataTableColumn } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import { StatusPill } from "@/components/ui/StatusPill";
import { Fonts } from "@/theme/fonts";
import { formatDisplayDate } from "@/utils/formatDisplayDate";
import { AttendanceListItem } from "@/api/attendanceList";

export function useAttendanceListColumns(): DataTableColumn<AttendanceListItem>[] {
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
      header: "Status",
      minWidth: 92,
      render: (row) =>
        row.attendanceStatus === "Present" ? (
          <StatusPill label="Present" tone="success" />
        ) : (
          <StatusPill label={row.attendanceStatus} tone="warning" />
        ),
      exportValue: (row) => row.attendanceStatus,
    },
    { key: "conferenceId", header: "Conference ID", minWidth: 130, exportValue: (row) => row.conferenceId ?? "--" },
    { key: "attendanceId", header: "Attendance ID", minWidth: 170, exportValue: (row) => row.attendanceId },
    { key: "participantHoId", header: "HOID", minWidth: 100, exportValue: (row) => row.participantHoId ?? "--" },
    { key: "participantName", header: "Name", minWidth: 150, exportValue: (row) => row.participantName },
    { key: "phone", header: "Phone", minWidth: 110, exportValue: (row) => row.phone ?? "--" },
    {
      key: "reportingManagerOfPromoter",
      header: "Supervisor Name",
      minWidth: 140,
      exportValue: (row) => row.reportingManagerOfPromoter ?? "--",
    },
    { key: "markedAt", header: "Marked At", minWidth: 150, exportValue: (row) => row.markedAt ?? "--" },
    { key: "district", header: "District", minWidth: 110, exportValue: (row) => row.district ?? "--" },
    {
      key: "conferenceDate",
      header: "Date",
      minWidth: 130,
      exportValue: (row) => formatDisplayDate(row.conferenceDate),
      searchValue: (row) => row.conferenceDate ?? "",
    },
    { key: "trainerName", header: "Trainer Name", minWidth: 118, exportValue: (row) => row.trainerName ?? "--" },
    { key: "checkIn", header: "Check-In", minWidth: 90, exportValue: (row) => row.checkIn ?? "-" },
    { key: "checkOut", header: "Check-Out", minWidth: 90, exportValue: (row) => row.checkOut ?? "-" },
    { key: "postTestScore", header: "Post Test Score", minWidth: 130, exportValue: (row) => row.postTestScore ?? "--" },
    {
      key: "postTestScoreSummary",
      header: "Post Test Score Summary",
      minWidth: 220,
      exportValue: (row) => row.postTestScoreSummary ?? "--",
    },
    { key: "updatedBy", header: "Updated By", minWidth: 96, exportValue: (row) => row.updatedBy ?? "--" },
    { key: "updationOn", header: "Updation On", minWidth: 140, exportValue: (row) => row.updationOn ?? "--" },
    { key: "lastUpdates", header: "Timestamp", minWidth: 140, exportValue: (row) => row.lastUpdates ?? "--" },
  ];
}

const styles = StyleSheet.create({
  cellText: { fontSize: Fonts.overline, textAlign: "center" },
});
