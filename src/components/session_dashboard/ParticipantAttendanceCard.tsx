import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import MarkAttendanceReasonModal, { PendingMark } from "./MarkAttendanceReasonModal";
import ParticipantRow from "./ParticipantRow";
import { ParticipantItem } from "./sessionDashboardTypes";
import SuspiciousActivityModal from "./SuspiciousActivityModal";
import UnlockExamModal from "./UnlockExamModal";

type ParticipantAttendanceCardProps = {
  participants: ParticipantItem[];
  onRefresh?: () => void;
  // Present/Absent can only be changed while the session is running.
  canEdit?: boolean;
  onMark?: (id: string, status: "Present" | "Absent", reason: string) => void;
  onUnlock?: (id: string, reason: string) => void;
};

export default function ParticipantAttendanceCard({
  participants,
  onRefresh,
  canEdit = false,
  onMark,
  onUnlock,
}: ParticipantAttendanceCardProps) {
  const [search, setSearch] = useState("");
  const [suspicious, setSuspicious] = useState<ParticipantItem | null>(null);
  const [unlockTarget, setUnlockTarget] = useState<ParticipantItem | null>(null);
  const [markTarget, setMarkTarget] = useState<PendingMark | null>(null);

  const handleConfirmMark = (reason: string) => {
    if (markTarget) onMark?.(markTarget.participant.id, markTarget.status, reason);
    setMarkTarget(null);
  };

  const handleConfirmUnlock = (reason: string) => {
    // The backend flips the lock and the parent refetches, so the LOCKED pill
    // clears on the next render - no local optimistic state needed.
    if (unlockTarget) onUnlock?.(unlockTarget.id, reason);
    setUnlockTarget(null);
  };

  const q = search.trim().toLowerCase();
  const filtered = q
    ? participants.filter(
        (p) =>
          p.name.toLowerCase().includes(q) || p.employeeId.toLowerCase().includes(q) || p.phone.includes(q),
      )
    : participants;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Ionicons name="people" size={18} color="#111827" />
          <AppText style={styles.title}>PARTICIPANT MASTER LIST</AppText>
        </View>
        <Pressable style={styles.refreshBtn} onPress={onRefresh} hitSlop={6}>
          <Ionicons name="reload" size={11} color="#374151" />
          <AppText style={styles.refreshText}>Refresh Data</AppText>
        </Pressable>
      </View>

      <View style={styles.filterRow}>
        <AppText style={styles.filterLabel}>{participants.length} joined</AppText>
        <View style={styles.searchBox}>
          <AppText style={styles.filterLabel}>Search:</AppText>
          <TextInput style={styles.searchInput} value={search} onChangeText={setSearch} />
        </View>
      </View>

      <View style={styles.table}>
        <View style={styles.thRow}>
          <AppText style={[styles.thText, { flex: 1.3 }]}>PARTICIPANT{"\n"}DETAILS</AppText>
          <AppText style={[styles.thText, { flex: 1.1 }]}>AUDIENCE{"\n"}TYPE</AppText>
          <AppText style={[styles.thText, { flex: 0.8 }]}>STATUS</AppText>
          <AppText style={[styles.thText, { flex: 1.1 }]}>IN-OUT</AppText>
          <AppText style={[styles.thText, { flex: 0.9 }]}>CONTROLS</AppText>
        </View>

        {filtered.length === 0 ? (
          <AppText style={styles.empty}>
            {participants.length === 0 ? "No one has joined yet." : "No match."}
          </AppText>
        ) : (
          filtered.map((item, idx) => {
            // The mapper only attaches `proctoring` when the backend row is
            // locked, so its presence is the lock.
            const isLocked = !!item.proctoring;
            return (
              <ParticipantRow
                key={item.id}
                item={item}
                alt={idx % 2 === 1}
                isLocked={isLocked}
                canEdit={canEdit}
                onCheck={() => setMarkTarget({ participant: item, status: "Present" })}
                onReject={() => setMarkTarget({ participant: item, status: "Absent" })}
                onShowSuspicious={() => setSuspicious(item)}
                onUnlock={() => setUnlockTarget(item)}
              />
            );
          })
        )}
      </View>

      {filtered.length > 0 && (
        <AppText style={styles.paginationInfo}>
          Showing {filtered.length} of {participants.length}
        </AppText>
      )}

      <SuspiciousActivityModal participant={suspicious} onClose={() => setSuspicious(null)} />
      <UnlockExamModal
        participant={unlockTarget}
        onCancel={() => setUnlockTarget(null)}
        onConfirm={handleConfirmUnlock}
      />
      <MarkAttendanceReasonModal
        pending={markTarget}
        onCancel={() => setMarkTarget(null)}
        onConfirm={handleConfirmMark}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.2,
    borderColor: "#EAECF0",
    padding: 12,
    marginHorizontal: 14,
    marginTop: 10,
    marginBottom: 20,
    ...Shadows.card,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  title: { fontSize: 11.5, fontWeight: "800", color: "#111827", letterSpacing: 0.3 },
  refreshBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.gray50,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  refreshText: { fontSize: 9, color: "#374151", fontWeight: "600" },
  filterRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  filterLabel: { fontSize: 8.5, color: "#4B5563" },
  searchBox: { flexDirection: "row", alignItems: "center", gap: 6 },
  searchInput: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 6,
    width: 110,
    height: 24,
    fontSize: 9,
    paddingHorizontal: 8,
    paddingVertical: 0,
  },
  table: { borderRadius: 8, overflow: "hidden" },
  thRow: {
    flexDirection: "row",
    backgroundColor: "#FAFAFB",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  thText: { fontSize: 8, fontWeight: "700", color: "#374151", textAlign: "center", lineHeight: 10.5 },
  empty: { fontSize: 10, color: "#6B7280", textAlign: "center", paddingVertical: 18 },
  paginationInfo: { fontSize: 8, color: "#6B7280", marginTop: 8 },
});
