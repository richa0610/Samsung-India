import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { ParticipantItem } from "./sessionDashboardTypes";

type ParticipantRowProps = {
  item: ParticipantItem;
  alt: boolean;
  isLocked: boolean;
  // Present/Absent can only be changed while the session is running.
  canEdit: boolean;
  onCheck: () => void;
  onReject: () => void;
  onShowSuspicious: () => void;
  onUnlock: () => void;
};

const STATUS_COLORS: Record<ParticipantItem["status"], { bg: string; border: string; text: string }> = {
  PRESENT: { bg: "#ECFDF5", border: "#A7F3D0", text: "#10B981" },
  PENDING: { bg: "#FFFBEB", border: "#FDE68A", text: "#D97706" },
  ABSENT: { bg: "#FEF2F2", border: "#FECACA", text: "#EF4444" },
};

export default function ParticipantRow({
  item,
  alt,
  isLocked,
  canEdit,
  onCheck,
  onReject,
  onShowSuspicious,
  onUnlock,
}: ParticipantRowProps) {
  const isAssigned = item.attendeeType === "ASSIGNED";
  const statusColor = STATUS_COLORS[item.status];

  return (
    <View style={[styles.row, alt && styles.rowAlt]}>
      <View style={[styles.detailsCol, { flex: 1.3 }]}>
        <AppText style={styles.name} numberOfLines={1}>{item.name}</AppText>
        <AppText style={styles.empId}>{item.employeeId}</AppText>
        <AppText style={styles.phone}>{item.phone}</AppText>
      </View>

      <View style={[styles.centerCol, { flex: 1.1 }]}>
        <View
          style={[
            styles.typePill,
            {
              backgroundColor: isAssigned ? "#FFFBEB" : Colors.gray50,
              borderColor: isAssigned ? "#FDE68A" : "#D1D5DB",
            },
          ]}
        >
          <AppText
            style={[styles.typePillText, { color: isAssigned ? "#D97706" : "#6B7280" }]}
            numberOfLines={1}
          >
            {item.attendeeType}
          </AppText>
        </View>
      </View>

      <View style={[styles.centerCol, { flex: 0.8 }]}>
        <View style={[styles.statusPill, { backgroundColor: statusColor.bg, borderColor: statusColor.border }]}>
          <AppText style={[styles.statusPillText, { color: statusColor.text }]}>{item.status}</AppText>
        </View>
      </View>

      <View style={[styles.inOutCol, { flex: 1.1 }]}>
        <AppText style={styles.inText}>{item.inTime}</AppText>
        <AppText style={styles.outText}>{item.outTime}</AppText>
      </View>

      <View style={[styles.controlsWrap, { flex: 0.9 }]}>
        {isLocked && (
          <Pressable style={styles.lockedPill} onPress={onShowSuspicious} hitSlop={3}>
            <Ionicons name="lock-closed" size={9} color="#EF4444" />
            <AppText style={styles.lockedPillText}>
              LOCKED ({item.proctoring!.flags}/{item.proctoring!.maxFlags})
            </AppText>
          </Pressable>
        )}
        <View style={styles.controlsRow}>
          {isLocked && (
            <Pressable onPress={onUnlock} hitSlop={2} style={[styles.iconBtn, styles.iconBtnWarning]}>
              <Ionicons name="lock-closed" size={10} color="#B45309" />
            </Pressable>
          )}
          <Pressable
            onPress={onCheck}
            disabled={!canEdit}
            hitSlop={2}
            style={[styles.iconBtn, styles.iconBtnSuccess, !canEdit && styles.iconBtnDisabled]}
          >
            <Ionicons name="checkmark" size={11} color={canEdit ? "#10B981" : "#9CA3AF"} />
          </Pressable>
          <Pressable
            onPress={onReject}
            disabled={!canEdit}
            hitSlop={2}
            style={[styles.iconBtn, styles.iconBtnDanger, !canEdit && styles.iconBtnDisabled]}
          >
            <Ionicons name="close" size={11} color={canEdit ? "#EF4444" : "#9CA3AF"} />
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  rowAlt: { backgroundColor: "#FAFAFA" },
  detailsCol: { gap: 1 },
  name: { fontSize: 8.5, fontWeight: "700", color: "#111827" },
  empId: { fontSize: 7, color: "#0066FF", fontWeight: "600" },
  phone: { fontSize: 7, color: "#6B7280" },
  centerCol: { alignItems: "center", paddingHorizontal: 2 },
  typePill: { borderWidth: 1, borderRadius: 4, paddingHorizontal: 3, paddingVertical: 1.5, maxWidth: "100%" },
  typePillText: { fontSize: 6, fontWeight: "700" },
  statusPill: { borderWidth: 1, borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1.5 },
  statusPillText: { fontSize: 6.5, fontWeight: "700" },
  inOutCol: { alignItems: "center", gap: 1 },
  inText: { fontSize: 6.5, color: "#10B981", fontWeight: "600" },
  outText: { fontSize: 6.5, color: "#EF4444", fontWeight: "600" },
  controlsWrap: { alignItems: "flex-end", gap: 3 },
  controlsRow: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 1 },
  lockedPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    borderWidth: 1,
    borderColor: "#FECACA",
    backgroundColor: "#FEF2F2",
    borderRadius: 5,
    paddingHorizontal: 1,
    paddingVertical: 2,
    marginRight: -1,
  },
  lockedPillText: { fontSize: 6, fontWeight: "800", color: "#EF4444" },
  iconBtn: {
    width: 17,
    height: 17,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
  },
  iconBtnSuccess: { backgroundColor: "#ECFDF5", borderColor: "#A7F3D0" },
  iconBtnDanger: { backgroundColor: "#FEF2F2", borderColor: "#FECACA" },
  iconBtnWarning: { backgroundColor: "#FEF3C7", borderColor: "#FDE68A" },
  iconBtnDisabled: { backgroundColor: "#F3F4F6", borderColor: "#E5E7EB", opacity: 0.6 },
});
