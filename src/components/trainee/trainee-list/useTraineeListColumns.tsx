import { StyleSheet } from "react-native";

import { DataTableColumn } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import { StatusPill, StatusTone } from "@/components/ui/StatusPill";
import { Fonts } from "@/theme/fonts";
import { TraineeListItem } from "@/api/trainee";
import { APPROVAL_STATUS_PRESENTATION } from "./formatting";

export function useTraineeListColumns(): DataTableColumn<TraineeListItem>[] {
  return [
    {
      key: "slNo",
      header: "Sl No.",
      minWidth: 36,
      sortable: false,
      render: (_row, index) => <AppText style={styles.cellText}>{index + 1}</AppText>,
      exportValue: (_row, index) => String(index + 1),
    },
    {
      key: "status",
      header: "Status",
      minWidth: 70,
      render: (row) => {
        const presentation = APPROVAL_STATUS_PRESENTATION[row.approvalStatus] ?? {
          label: row.approvalStatus,
          tone: "neutral" as StatusTone,
        };
        return <StatusPill label={presentation.label} tone={presentation.tone} />;
      },
      exportValue: (row) => APPROVAL_STATUS_PRESENTATION[row.approvalStatus]?.label ?? row.approvalStatus,
    },
    { key: "traineeUid", header: "Trainee Uid", minWidth: 100, exportValue: (row) => row.traineeUid },
    { key: "name", header: "Name", minWidth: 100, exportValue: (row) => row.fullName },
    { key: "phone", header: "Phone", minWidth: 90, exportValue: (row) => row.primaryPhone ?? "--" },
    { key: "trainerName", header: "Trainer Name", minWidth: 95, exportValue: (row) => row.trainerName || "--" },
    { key: "supervisorName", header: "Supervisor Name", minWidth: 105, exportValue: (row) => row.supervisorName || "--" },
    { key: "district", header: "District", minWidth: 80, exportValue: (row) => row.district ?? "--" },
    { key: "updatedBy", header: "Updated By", minWidth: 80, exportValue: (row) => row.updatedBy ?? "--" },
    { key: "updationOn", header: "Updation On", minWidth: 95, exportValue: (row) => row.updationOn ?? "--" },
    { key: "timestamp", header: "Timestamp", minWidth: 95, exportValue: (row) => row.timestamp ?? "--" },
  ];
}

const styles = StyleSheet.create({
  cellText: { fontSize: Fonts.overline, textAlign: "center" },
});
