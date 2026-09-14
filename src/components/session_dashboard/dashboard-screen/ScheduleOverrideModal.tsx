import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppInput from "@/components/ui/AppInput";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { ScheduleOverridePrompt } from "./useSessionDashboardScreen";

type ScheduleOverrideModalProps = {
  prompt: ScheduleOverridePrompt | null;
  onCancel: () => void;
  onSubmit: (reason: string) => void;
};

function scheduledLabel(iso: string | null): string | null {
  if (!iso) return null;
  const parsed = new Date(iso);
  if (isNaN(parsed.getTime())) return null;
  return parsed.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

export default function ScheduleOverrideModal({ prompt, onCancel, onSubmit }: ScheduleOverrideModalProps) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Reset the field whenever a new prompt opens / it closes (React's
  // "adjust state on prop change" pattern, not an effect).
  const [seenPrompt, setSeenPrompt] = useState(prompt);
  if (prompt !== seenPrompt) {
    setSeenPrompt(prompt);
    setReason("");
    setSubmitting(false);
  }

  const when = scheduledLabel(prompt?.scheduledFor ?? null);
  const earlyOrLate = prompt?.early ? "early" : "late";
  const canSubmit = reason.trim().length > 0 && !submitting;

  const submit = () => {
    if (!canSubmit) return;
    setSubmitting(true);
    onSubmit(reason.trim());
  };

  return (
    <AppModal visible={!!prompt} onClose={onCancel} position="center" contentStyle={styles.sheet}>
      <View style={styles.header}>
        <Ionicons name="time" size={18} color="#F59E0B" />
        <AppText style={styles.title}>Training schedule override</AppText>
      </View>
      <AppText style={styles.body}>
        {when
          ? `This session was scheduled to start at ${when}.`
          : "This isn't this session's scheduled start time."}{" "}
        You&apos;re starting it {earlyOrLate}. Add a reason to proceed — it&apos;s stored on this
        session.
      </AppText>

      <AppInput
        compact
        label={`Reason for starting ${earlyOrLate}`}
        value={reason}
        onChangeText={setReason}
        placeholder="e.g. Venue access delayed, waiting on trainees"
        multiline
      />

      <View style={styles.actionsRow}>
        <Pressable onPress={onCancel} hitSlop={8} disabled={submitting}>
          <AppText style={styles.secondaryText}>Cancel</AppText>
        </Pressable>
        <Pressable onPress={submit} disabled={!canSubmit} hitSlop={8}>
          <AppText style={[styles.primaryText, !canSubmit && styles.disabled]}>
            Override &amp; start
          </AppText>
        </Pressable>
      </View>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: { backgroundColor: "#1F2530", borderRadius: 12, padding: 18, width: "88%" },
  header: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 10 },
  title: { flex: 1, fontSize: 15, fontWeight: "800", color: "#F3F4F6" },
  body: { fontSize: 12, color: "#D1D5DB", lineHeight: 18, marginBottom: 14 },
  actionsRow: { flexDirection: "row", justifyContent: "flex-end", gap: 22, marginTop: 16 },
  secondaryText: { fontSize: 13, color: "#9CA3AF", fontWeight: "600" },
  primaryText: { fontSize: 13, color: "#60A5FA", fontWeight: "800" },
  disabled: { opacity: 0.4 },
});
