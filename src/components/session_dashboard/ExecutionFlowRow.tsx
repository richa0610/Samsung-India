import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { ExecutionFlowItem } from "@/api/training";
import { useLiveRuntime } from "@/hooks/useLiveRuntime";
import { formatElapsed, getExecutionStatusPresentation, getModuleVisual } from "./executionFlowUtils";

type ExecutionFlowRowProps = {
  item: ExecutionFlowItem;
  hasStarted: boolean;
  onRestart?: (moduleKey: string) => void;
  onViewTopPerformers?: (moduleKey: string) => void;
  onStart?: (moduleKey: string) => void;
};

export default function ExecutionFlowRow({
  item,
  hasStarted,
  onRestart,
  onViewTopPerformers,
  onStart,
}: ExecutionFlowRowProps) {
  // Ticks every second while the module is Running; frozen once it ends.
  const seconds = useLiveRuntime(item.startedAt, item.endedAt);
  const effectiveStatus = hasStarted ? item.status : "Pending";
  const visual = getModuleVisual(item.moduleKey);
  const status = getExecutionStatusPresentation(effectiveStatus);
  const elapsed = hasStarted && effectiveStatus !== "Pending" ? formatElapsed(seconds) : null;
  // The Start button is on every not-yet-run row, but only tappable once
  // this module is next in line (backend `canStart`).
  const showStart = hasStarted && effectiveStatus === "Pending";
  const startEnabled = showStart && item.canStart;

  return (
    <View style={styles.row}>
      <View style={styles.rowMain}>
        <View style={[styles.iconWrap, { backgroundColor: visual.bg }]}>
          <Ionicons name={visual.icon} size={16} color="#FFFFFF" />
        </View>
        <View style={styles.textCol}>
          <AppText style={styles.title}>{item.label}</AppText>
          <AppText style={styles.subtitle}>
            {visual.categoryLabel}
            {item.assignedMinutes != null ? ` | Assigned: ${item.assignedMinutes}m` : ""}
          </AppText>
        </View>
        <View style={[styles.statusPill, { backgroundColor: status.bg }]}>
          <AppText style={[styles.statusText, { color: status.color }]}>{status.label}</AppText>
          {elapsed && <AppText style={[styles.elapsedText, { color: status.color }]}>{elapsed}</AppText>}
        </View>
        {showStart && (
          <Pressable
            style={[styles.startBtn, !startEnabled && styles.startBtnDisabled]}
            onPress={() => startEnabled && onStart?.(item.moduleKey)}
            disabled={!startEnabled}
            accessibilityRole="button"
            accessibilityLabel={`Start ${item.label}`}
          >
            <Ionicons name="play" size={11} color="#FFFFFF" />
            <AppText style={styles.startBtnText}>Start</AppText>
          </Pressable>
        )}
      </View>

      {hasStarted && effectiveStatus === "Completed" && (
        <Pressable
          style={[styles.actionBtn, !item.canRestart && styles.actionBtnDisabled]}
          onPress={() => item.canRestart && onRestart?.(item.moduleKey)}
          disabled={!item.canRestart}
          accessibilityRole="button"
          accessibilityLabel={`Restart ${item.label}`}
        >
          <Ionicons name="refresh" size={12} color={item.canRestart ? "#4B5563" : "#9CA3AF"} />
          <AppText style={[styles.actionText, !item.canRestart && styles.actionTextDisabled]}>Restart</AppText>
        </Pressable>
      )}

      {hasStarted && effectiveStatus === "Running" && (
        <View style={styles.actionRow}>
          <Pressable style={styles.actionBtnOutline} onPress={() => onViewTopPerformers?.(item.moduleKey)}>
            <Ionicons name="stats-chart" size={12} color="#2563EB" />
            <AppText style={styles.actionTextBlue}>Top Performers</AppText>
          </Pressable>
          <View style={styles.liveDot}>
            <View style={styles.liveDotIndicator} />
            <AppText style={styles.liveDotText}>Running</AppText>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#EAECF0",
    padding: 10,
    gap: 8,
  },
  rowMain: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconWrap: { width: 36, height: 36, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  textCol: { flex: 1, gap: 2 },
  title: { fontSize: 12.5, fontWeight: "700", color: "#111827" },
  subtitle: { fontSize: 9.5, fontWeight: "600", color: "#9CA3AF", letterSpacing: 0.3 },
  statusPill: { alignItems: "center", paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10, gap: 2 },
  statusText: { fontSize: 9.5, fontWeight: "700" },
  elapsedText: { fontSize: 9.5, fontWeight: "600" },
  startBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#16A34A",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  startBtnDisabled: { backgroundColor: "#D1D5DB" },
  startBtnText: { fontSize: 10, fontWeight: "700", color: "#FFFFFF" },
  actionBtn: {
    flexDirection: "row",
    alignSelf: "flex-start",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  actionText: { fontSize: 10, fontWeight: "600", color: "#4B5563" },
  actionBtnDisabled: { borderColor: "#E5E7EB", opacity: 0.6 },
  actionTextDisabled: { color: "#9CA3AF" },
  actionRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  actionBtnOutline: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderColor: "#BFDBFE",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  actionTextBlue: { fontSize: 10, fontWeight: "600", color: "#2563EB" },
  liveDot: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#DC2626",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  liveDotIndicator: { width: 5, height: 5, borderRadius: 3, backgroundColor: "#FFFFFF" },
  liveDotText: { fontSize: 10, fontWeight: "700", color: "#FFFFFF" },
});
