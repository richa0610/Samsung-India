import { Pressable, StyleSheet } from "react-native";

import ActionIcon from "@/assets/images/svg/action.svg";
import { DataTableColumn } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { formatDisplayDate } from "@/utils/formatDisplayDate";
import { TrainingAgendaItem } from "@/api/training";

export function buildTrainingListColumns(
  onEdit: (row: TrainingAgendaItem) => void,
  statusColumn: DataTableColumn<TrainingAgendaItem>
): DataTableColumn<TrainingAgendaItem>[] {
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
      key: "action",
      header: "Action",
      minWidth: 48,
      sortable: false,
      render: (row) => (
        <Pressable style={styles.actionButton} onPress={() => onEdit(row)} hitSlop={4}>
          <ActionIcon width={15} height={15} />
        </Pressable>
      ),
      exportValue: () => "",
    },
    {
      key: "currentReport",
      header: "Current Report",
      minWidth: 150,
      sortable: false,
      render: (row) => (
        <Pressable style={styles.reportButton} onPress={() => onEdit(row)} hitSlop={4}>
          <AppText style={styles.reportButtonText} color={Colors.white} weight={FontWeight.semiBold}>Conference Report</AppText>
        </Pressable>
      ),
      exportValue: () => "Conference Report",
    },
    statusColumn,
    { key: "trainingsId", header: "Trainings ID", minWidth: 118, exportValue: (row) => row.conferenceUid },
    { key: "totalPax", header: "Total Pax (Trainer)", minWidth: 100, exportValue: (row) => String(row.traineeCount ?? 0) },
    { key: "trainerName", header: "Trainer Name", minWidth: 118, exportValue: (row) => row.trainerName ?? "--" },
    { key: "hoid", header: "HOID", minWidth: 96, exportValue: (row) => row.hoid ?? "--" },
    {
      key: "date",
      header: "Date",
      minWidth: 128,
      exportValue: (row) => formatDisplayDate(row.conferenceDate),
      searchValue: (row) => row.conferenceDate ?? "",
    },
    { key: "time", header: "Time", minWidth: 76, exportValue: (row) => row.conferenceTime ?? "--" },
    { key: "trainingType", header: "Training Type", minWidth: 130, exportValue: (row) => row.trainingType ?? "--" },
    { key: "venueName", header: "Venue Name", minWidth: 110, exportValue: (row) => row.venueName ?? "--" },
    { key: "state", header: "State", minWidth: 100, exportValue: (row) => row.state ?? "--" },
    { key: "district", header: "District", minWidth: 100, exportValue: (row) => row.district ?? "--" },
    { key: "trainingHub", header: "Training Hub", minWidth: 110, exportValue: (row) => row.trainingHub ?? "--" },
    { key: "updatedBy", header: "Updated By", minWidth: 96, exportValue: (row) => row.updatedBy ?? "--" },
    { key: "updationOn", header: "Updation On", minWidth: 140, exportValue: (row) => row.updationOn ?? "--" },
    { key: "timestamp", header: "Timestamp", minWidth: 140, exportValue: (row) => row.timestamp ?? "--" },
  ];
}

const styles = StyleSheet.create({
  cellText: { fontSize: Fonts.bodySm },
  actionButton: {
    width: 26,
    height: 26,
    borderRadius: Radius.md,
    backgroundColor: Colors.success,
    alignItems: "center",
    justifyContent: "center",
  },
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
