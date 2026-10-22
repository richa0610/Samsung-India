import { Animated, Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import ParticipantDetailsCell from "./ParticipantDetailsCell";
import ParticipantStageCell from "./ParticipantStageCell";
import { ColumnWidths, ROW_SIDE_PADDING, frozenDetailsCell, participantCell } from "./participantColumns";
import { ParticipantItem } from "./sessionDashboardTypes";

type ParticipantRowProps = {
  item: ParticipantItem;
  /** Each column's width - the same numbers the heading row uses, so the columns line up. */
  widths: ColumnWidths;
  /** How far the table has scrolled sideways: the details cell moves by it, so it stays put. */
  frozenOffset: Animated.AnimatedInterpolation<number>;
  alt: boolean;
  isLocked: boolean;
  // Present/Absent can only be changed while the session is running.
  canEdit: boolean;
  onCheck: () => void;
  onReject: () => void;
  onShowSuspicious: () => void;
  onUnlock: () => void;
};

const ROW_VERTICAL_PADDING = 6;

// The pill shows the short form (P / A / NM); screen readers get the full word.
const STATUS_DISPLAY: Record<
  ParticipantItem["status"],
  { label: string; name: string; bg: string; border: string; text: string }
> = {
  PRESENT: { label: "P", name: "Present", bg: Colors.successBgSoft, border: "#A7F3D0", text: Colors.statusGreen },
  NOT_MARKED: { label: "NM", name: "Not marked", bg: "#FFFBEB", border: "#FDE68A", text: "#D97706" },
  ABSENT: { label: "A", name: "Absent", bg: Colors.dangerBgSoft, border: "#FECACA", text: Colors.red },
};

export default function ParticipantRow({
  item,
  widths,
  frozenOffset,
  alt,
  isLocked,
  canEdit,
  onCheck,
  onReject,
  onShowSuspicious,
  onUnlock,
}: ParticipantRowProps) {
  const status = STATUS_DISPLAY[item.status];
  const unlocksUsedUp = !!item.proctoring && item.proctoring.unlocksUsed >= item.proctoring.maxUnlocks;

  return (
    <View style={[styles.row, alt && styles.rowAlt]}>
      {/* Frozen: left-aligned, above the other cells, filling the row's height in the row's colour,
          and moved along with the sideways scroll so it stays on screen. */}
      <Animated.View
        style={[
          participantCell,
          frozenDetailsCell,
          styles.frozenFill,
          {
            width: widths.details,
            backgroundColor: alt ? Colors.gray50 : Colors.white,
            transform: [{ translateX: frozenOffset }],
          },
        ]}
      >
        <ParticipantDetailsCell item={item} />
      </Animated.View>

      <View style={[participantCell, { width: widths.stage }]}>
        <ParticipantStageCell stage={item.stage} modules={item.stageModules} />
      </View>

      <View style={[participantCell, { width: widths.status }]}>
        <View
          style={[styles.statusPill, { backgroundColor: status.bg, borderColor: status.border }]}
          accessible
          accessibilityLabel={status.name}
        >
          <AppText style={[styles.statusPillText, { color: status.text }]}>{status.label}</AppText>
        </View>
      </View>

      <View style={[participantCell, styles.stacked, { width: widths.inOut }]}>
        {/* One line each: a narrow column shrinks the time a little rather than breaking it. */}
        <AppText style={styles.inText} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.8}>
          {item.inTime}
        </AppText>
        <AppText style={styles.outText} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.8}>
          {item.outTime}
        </AppText>
      </View>

      <View style={[participantCell, { width: widths.score }]}>
        {item.score ? (
          <View
            style={[styles.scorePill, item.scorePassed === false ? styles.scoreFail : styles.scorePass]}
            accessible
            accessibilityLabel={`Score ${item.score}${item.scorePassed === false ? ", below the pass mark" : ", passed"}`}
          >
            <AppText style={styles.scoreText}>{item.score}</AppText>
          </View>
        ) : (
          <AppText style={styles.noScore} accessibilityLabel="No score yet">
            -
          </AppText>
        )}
      </View>

      <View style={[participantCell, styles.controls, { width: widths.controls }]}>
        {isLocked && (
          <Pressable style={styles.lockedPill} onPress={onShowSuspicious} hitSlop={3}>
            <Ionicons name="lock-closed" size={11} color={Colors.red} />
            <AppText style={styles.lockedPillText}>
              LOCKED ({item.proctoring!.flags}/{item.proctoring!.maxFlags})
            </AppText>
          </Pressable>
        )}
        <View style={styles.controlsRow}>
          {isLocked && (
            // Still pressable once the unlocks are used up - the card then explains why it can't.
            <Pressable
              onPress={onUnlock}
              hitSlop={2}
              style={[styles.iconBtn, styles.iconBtnWarning, unlocksUsedUp && styles.iconBtnDisabled]}
              accessibilityRole="button"
              accessibilityLabel={
                unlocksUsedUp
                  ? `Unlock ${item.name}: no unlocks left`
                  : `Unlock ${item.name}, ${item.proctoring!.unlocksUsed} of ${item.proctoring!.maxUnlocks} unlocks used`
              }
            >
              <Ionicons name="lock-closed" size={10} color={unlocksUsedUp ? Colors.gray400 : "#B45309"} />
            </Pressable>
          )}
          <Pressable
            onPress={onCheck}
            disabled={!canEdit}
            hitSlop={2}
            style={[styles.iconBtn, styles.iconBtnSuccess, !canEdit && styles.iconBtnDisabled]}
          >
            <Ionicons name="checkmark" size={11} color={canEdit ? Colors.statusGreen : Colors.gray400} />
          </Pressable>
          <Pressable
            onPress={onReject}
            disabled={!canEdit}
            hitSlop={2}
            style={[styles.iconBtn, styles.iconBtnDanger, !canEdit && styles.iconBtnDisabled]}
          >
            <Ionicons name="close" size={11} color={canEdit ? Colors.red : Colors.gray400} />
          </Pressable>
          {/* How many times the trainer has unlocked them, of the most allowed (user, 2026-10-22). */}
          {!!item.unlocks?.used && (
            <View
              style={styles.unlockCount}
              accessible
              accessibilityLabel={`Unlocked ${item.unlocks.used} of ${item.unlocks.max} times`}
            >
              <Ionicons name="lock-open" size={9} color="#B45309" />
              <AppText style={styles.unlockCountText}>
                {item.unlocks.used}/{item.unlocks.max}
              </AppText>
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: ROW_VERTICAL_PADDING,
    paddingHorizontal: ROW_SIDE_PADDING,
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray100,
  },
  rowAlt: { backgroundColor: Colors.gray50 },
  // The frozen cell covers the row's full height (padding included), so content scrolling
  // underneath never peeks out above or below it.
  frozenFill: { alignSelf: "stretch", marginVertical: -ROW_VERTICAL_PADDING, paddingVertical: ROW_VERTICAL_PADDING },
  statusPill: { borderWidth: 1, borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1.5 },
  statusPillText: { fontSize: 8.5, fontWeight: "700" },
  stacked: { gap: 1 },
  inText: { fontSize: 8.5, color: Colors.statusGreen, fontWeight: "600" },
  outText: { fontSize: 8.5, color: Colors.red, fontWeight: "600" },
  // Solid green (passed) or red (below the pass mark), white figures - like the web list.
  scorePill: { borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1.5 },
  scorePass: { backgroundColor: Colors.statusGreen },
  scoreFail: { backgroundColor: Colors.red },
  scoreText: { fontSize: 8.5, fontWeight: "700", color: Colors.white },
  noScore: { fontSize: 8.5, color: Colors.gray500 },
  controls: { gap: 3 },
  // Wraps rather than overflowing when a locked row's three buttons don't fit side by side.
  controlsRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "center", gap: 1 },
  lockedPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    borderWidth: 1,
    borderColor: "#FECACA",
    backgroundColor: Colors.dangerBgSoft,
    borderRadius: 5,
    paddingHorizontal: 1,
    paddingVertical: 2,
  },
  lockedPillText: { fontSize: 8, fontWeight: "800", color: Colors.red },
  iconBtn: {
    width: 17,
    height: 17,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.gray200,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.white,
  },
  iconBtnSuccess: { backgroundColor: Colors.successBgSoft, borderColor: "#A7F3D0" },
  iconBtnDanger: { backgroundColor: Colors.dangerBgSoft, borderColor: "#FECACA" },
  iconBtnWarning: { backgroundColor: "#FEF3C7", borderColor: "#FDE68A" },
  iconBtnDisabled: { backgroundColor: Colors.gray100, borderColor: Colors.gray200, opacity: 0.6 },
  unlockCount: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    height: 17,
    borderWidth: 1,
    borderColor: "#FDE68A",
    backgroundColor: "#FEF3C7",
    borderRadius: 4,
    paddingHorizontal: 3,
  },
  unlockCountText: { fontSize: 8, fontWeight: "700", color: "#B45309" },
});
