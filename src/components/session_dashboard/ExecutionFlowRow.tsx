import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { ExecutionFlowItem } from "@/api/training";
import { useLiveRuntime } from "@/hooks/useLiveRuntime";
import { formatElapsed, getExecutionStatusPresentation, getModuleVisual } from "./executionFlowUtils";
import { Colors } from "@/theme/colors";

type ExecutionFlowRowProps = {
  item: ExecutionFlowItem;
  hasStarted: boolean;
  onRestart?: (moduleKey: string) => void;
  onViewTopPerformers?: (moduleKey: string) => void;
  onStart?: (moduleKey: string) => void;
  isStarting?: boolean;
  anyStarting?: boolean;
  isRestarting?: boolean;
};

export default function ExecutionFlowRow({
  item,
  hasStarted,
  onRestart,
  onViewTopPerformers,
  onStart,
  isStarting = false,
  anyStarting = false,
  isRestarting = false,
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
          <Ionicons name={visual.icon} size={16} color={Colors.white} />
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
            style={[
              styles.startBtn,
              !startEnabled && styles.startBtnDisabled,
              isStarting && styles.startBtnLoading,
              !isStarting && anyStarting && styles.startBtnDisabled,
            ]}
            onPress={() => startEnabled && !isStarting && !anyStarting && onStart?.(item.moduleKey)}
            disabled={!startEnabled || isStarting || anyStarting}
            accessibilityRole="button"
            accessibilityLabel={`Start ${item.label}`}
          >
            {isStarting ? (
              <>
                <ActivityIndicator size="small" color={Colors.white} style={styles.spinner} />
                <AppText style={styles.startBtnText}>Starting...</AppText>
              </>
            ) : (
              <>
                <Ionicons name="play" size={11} color={Colors.white} />
                <AppText style={styles.startBtnText}>Start</AppText>
              </>
            )}
          </Pressable>
        )}
      </View>

      {hasStarted && effectiveStatus === "Completed" && (
        <Pressable
          style={[
            styles.actionBtn,
            (!item.canRestart || isRestarting || anyStarting) && styles.actionBtnDisabled,
          ]}
          onPress={() => item.canRestart && !isRestarting && !anyStarting && onRestart?.(item.moduleKey)}
          disabled={!item.canRestart || isRestarting || anyStarting}
          accessibilityRole="button"
          accessibilityLabel={`Restart ${item.label}`}
        >
          {isRestarting ? (
            <>
              <ActivityIndicator size="small" color={Colors.gray600} style={styles.spinner} />
              <AppText style={styles.actionText}>Restarting...</AppText>
            </>
          ) : (
            <>
              <Ionicons name="refresh" size={12} color={item.canRestart ? Colors.gray600 : Colors.gray400} />
              <AppText style={[styles.actionText, !item.canRestart && styles.actionTextDisabled]}>Restart</AppText>
            </>
          )}
        </Pressable>
      )}

      {hasStarted && effectiveStatus === "Running" && (
        <View style={styles.actionRow}>
          <Pressable style={styles.actionBtnOutline} onPress={() => onViewTopPerformers?.(item.moduleKey)}>
            <Ionicons name="stats-chart" size={12} color={Colors.blueAccent} />
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
    backgroundColor: Colors.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    padding: 10,
    gap: 8,
  },
  rowMain: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconWrap: { width: 36, height: 36, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  textCol: { flex: 1, gap: 2 },
  title: { fontSize: 12.5, fontWeight: "700", color: Colors.black },
  subtitle: { fontSize: 9.5, fontWeight: "600", color: Colors.gray400, letterSpacing: 0.3 },
  statusPill: { alignItems: "center", paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10, gap: 2 },
  statusText: { fontSize: 9.5, fontWeight: "700" },
  elapsedText: { fontSize: 9.5, fontWeight: "600" },
  startBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.success,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  startBtnDisabled: { backgroundColor: Colors.gray300 },
  startBtnLoading: { backgroundColor: "#15803D", paddingHorizontal: 8 },
  startBtnText: { fontSize: 10, fontWeight: "700", color: Colors.white },
  spinner: { transform: [{ scale: 0.7 }], marginHorizontal: -2 },
  actionBtn: {
    flexDirection: "row",
    alignSelf: "flex-start",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderColor: Colors.gray300,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  actionText: { fontSize: 10, fontWeight: "600", color: Colors.gray600 },
  actionBtnDisabled: { borderColor: Colors.gray200, opacity: 0.6 },
  actionTextDisabled: { color: Colors.gray400 },
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
  actionTextBlue: { fontSize: 10, fontWeight: "600", color: Colors.blueAccent },
  liveDot: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.danger,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  liveDotIndicator: { width: 5, height: 5, borderRadius: 3, backgroundColor: Colors.white },
  liveDotText: { fontSize: 10, fontWeight: "700", color: Colors.white },
});
