import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import AppModal from "@/components/ui/AppModal";
import { ParticipantItem } from "./sessionDashboardTypes";

type SuspiciousActivityModalProps = {
  participant: ParticipantItem | null;
  onClose: () => void;
};

export default function SuspiciousActivityModal({ participant, onClose }: SuspiciousActivityModalProps) {
  const proctoring = participant?.proctoring;

  return (
    <AppModal
      visible={!!participant}
      onClose={onClose}
      position="center"
      contentStyle={styles.sheet}
    >
      <View style={styles.header}>
        <Ionicons name="warning" size={16} color="#F59E0B" />
        <AppText style={styles.title}>SUSPICIOUS ACTIVITY</AppText>
      </View>
      <View style={styles.divider} />

      <AppText style={styles.metaLine}>
        Participant: <AppText style={styles.metaValue}>{participant?.name}</AppText>
      </AppText>
      <AppText style={styles.metaLine}>
        Flags: <AppText style={styles.metaValue}>{proctoring?.flags ?? 0}/{proctoring?.maxFlags ?? 3}</AppText>
      </AppText>

      <AppText style={styles.logsLabel}>LOGS:</AppText>
      <ScrollView style={styles.logsList}>
        {(proctoring?.logs ?? []).map((log, idx) => (
          <View key={idx} style={styles.logRow}>
            <AppText style={styles.bullet}>•</AppText>
            <AppText style={styles.logText}>{log}</AppText>
          </View>
        ))}
        {!proctoring?.logs?.length && <AppText style={styles.logText}>No proctoring events logged.</AppText>}
      </ScrollView>

      <Pressable style={styles.closeBtn} onPress={onClose} hitSlop={8}>
        <AppText style={styles.closeText}>Close</AppText>
      </Pressable>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: {
    backgroundColor: "#0B0F19",
    borderRadius: 12,
    padding: 16,
    width: "88%",
    maxHeight: "70%",
  },
  header: { flexDirection: "row", alignItems: "center", gap: 8 },
  title: { fontSize: 13, fontWeight: "800", color: "#F59E0B", letterSpacing: 0.5 },
  divider: { borderTopWidth: 1, borderTopColor: "#374151", borderStyle: "dashed", marginTop: 10, marginBottom: 10 },
  metaLine: { fontSize: 12, color: "#9CA3AF", marginBottom: 4 },
  metaValue: { color: "#F3F4F6", fontWeight: "700" },
  logsLabel: { fontSize: 12, fontWeight: "800", color: "#F3F4F6", marginTop: 12, marginBottom: 8 },
  logsList: { maxHeight: 220 },
  logRow: { flexDirection: "row", gap: 6, marginBottom: 10, paddingRight: 4 },
  bullet: { color: "#9CA3AF", fontSize: 12 },
  logText: { flex: 1, fontSize: 11, color: "#D1D5DB", lineHeight: 16 },
  closeBtn: { marginTop: 8, alignSelf: "flex-end" },
  closeText: { fontSize: 13, color: "#3B82F6", fontWeight: "700" },
});
