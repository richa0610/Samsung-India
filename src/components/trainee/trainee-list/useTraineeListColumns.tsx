import { Pressable, StyleSheet } from "react-native";

import ActionIcon from "@/assets/images/svg/action.svg";
import { DataTableColumn } from "@/components/ui/DataTable";
import AppText from "@/components/ui/AppText";
import { StatusPill, StatusTone } from "@/components/ui/StatusPill";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { TraineeListItem } from "@/api/trainee";
import { APPROVAL_STATUS_PRESENTATION } from "./formatting";

export function useTraineeListColumns(onEdit: (row: TraineeListItem) => void): DataTableColumn<TraineeListItem>[] {
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
      key: "status",
      header: "Status",
      minWidth: 92,
      render: (row) => {
        const presentation = APPROVAL_STATUS_PRESENTATION[row.approvalStatus] ?? {
          label: row.approvalStatus,
          tone: "neutral" as StatusTone,
        };
        return <StatusPill label={presentation.label} tone={presentation.tone} />;
      },
      exportValue: (row) => APPROVAL_STATUS_PRESENTATION[row.approvalStatus]?.label ?? row.approvalStatus,
    },
    { key: "traineeUid", header: "Trainee Uid", minWidth: 150, exportValue: (row) => row.traineeUid },
    { key: "name", header: "Name", minWidth: 128, exportValue: (row) => row.fullName },
    { key: "phone", header: "Phone", minWidth: 110, exportValue: (row) => row.primaryPhone ?? "--" },
    { key: "trainerName", header: "Trainer Name", minWidth: 118, exportValue: (row) => row.trainerName || "--" },
    { key: "supervisorName", header: "Supervisor Name", minWidth: 130, exportValue: (row) => row.supervisorName || "--" },
    { key: "district", header: "District", minWidth: 110, exportValue: (row) => row.district ?? "--" },
    { key: "updatedBy", header: "Updated By", minWidth: 96, exportValue: (row) => row.updatedBy ?? "--" },
    { key: "updationOn", header: "Updation On", minWidth: 140, exportValue: (row) => row.updationOn ?? "--" },
    { key: "timestamp", header: "Timestamp", minWidth: 140, exportValue: (row) => row.timestamp ?? "--" },
  ];
}

const styles = StyleSheet.create({
  cellText: { fontSize: Fonts.overline, textAlign: "center" },
  actionButton: {
    width: 26,
    height: 26,
    borderRadius: Radius.md,
    backgroundColor: Colors.success,
    alignItems: "center",
    justifyContent: "center",
  },
});
