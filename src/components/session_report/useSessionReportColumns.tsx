import { StyleSheet } from "react-native";

import AppText from "@/components/ui/AppText";
import { DataTableColumn } from "@/components/ui/DataTable";
import { Fonts } from "@/theme/fonts";
import { SessionReportParticipant } from "@/api/training";

export function useSessionReportColumns(): DataTableColumn<SessionReportParticipant>[] {
  return [
    {
      key: "slNo",
      header: "S.No",
      minWidth: 34,
      sortable: false,
      render: (_row, index) => <AppText style={styles.cellText}>{index + 1}</AppText>,
      exportValue: (_row, index) => String(index + 1),
    },
    {
      key: "name",
      header: "Name",
      minWidth: 108,
      exportValue: (row) => row.name,
      render: (row) => (
        <AppText style={styles.cellText} numberOfLines={3}>
          {row.name}
        </AppText>
      ),
    },
    { key: "userId", header: "User ID", minWidth: 76, exportValue: (row) => row.userId },
    { key: "role", header: "Role", minWidth: 66, exportValue: (row) => row.role },
    {
      key: "checkIn",
      header: "Check In",
      minWidth: 60,
      exportValue: (row) => row.checkIn ?? "--",
      render: (row) => <AppText style={styles.cellText}>{row.checkIn ?? "--"}</AppText>,
    },
    {
      key: "checkOut",
      header: "Check Out",
      minWidth: 62,
      exportValue: (row) => row.checkOut ?? "--",
      render: (row) => <AppText style={styles.cellText}>{row.checkOut ?? "--"}</AppText>,
    },
    {
      key: "score",
      header: "Score",
      minWidth: 46,
      exportValue: (row) => row.score ?? "--",
      render: (row) => <AppText style={styles.cellText}>{row.score ?? "--"}</AppText>,
    },
  ];
}

const styles = StyleSheet.create({
  cellText: { fontSize: Fonts.overline, textAlign: "center" },
});
