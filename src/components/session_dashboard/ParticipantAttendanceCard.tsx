import { useMemo, useState } from "react";
import { Alert, Animated, Pressable, StyleSheet, TextInput, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import MarkAttendanceReasonModal, { PendingMark } from "./MarkAttendanceReasonModal";
import ParticipantRow from "./ParticipantRow";
import {
  HEADER_BORDER_WIDTH,
  ParticipantColumn,
  ROW_SIDE_PADDING,
  columnWidths,
  frozenDetailsCell,
  participantCell,
} from "./participantColumns";
import { ParticipantItem } from "./sessionDashboardTypes";
import SuspiciousActivityModal from "./SuspiciousActivityModal";
import UnlockExamModal from "./UnlockExamModal";

const HEADING_VERTICAL_PADDING = 10;
const HEADING_RADIUS = 10;

const HEADINGS: { column: ParticipantColumn; label: string }[] = [
  { column: "details", label: "PARTICIPANT\nDETAILS" },
  { column: "stage", label: "STAGE" },
  { column: "status", label: "STATUS" },
  { column: "inOut", label: "IN-OUT" },
  { column: "score", label: "SCORE" },
  { column: "controls", label: "CONTROLS" },
];

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
  // The table area's width: the base column widths on a phone, stretched to fill a wider screen.
  const [tableArea, setTableArea] = useState(0);
  const widths = useMemo(() => columnWidths(tableArea), [tableArea]);
  // The sideways scroll position, followed on the native thread. The details column is shifted by
  // it (never left of 0, e.g. in an iOS bounce), so that column stays frozen on screen.
  const [scrollX] = useState(() => new Animated.Value(0));
  const frozenOffset = useMemo(
    () => scrollX.interpolate({ inputRange: [0, 1], outputRange: [0, 1], extrapolateLeft: "clamp" }),
    [scrollX],
  );
  const onTableScroll = useMemo(
    () => Animated.event([{ nativeEvent: { contentOffset: { x: scrollX } } }], { useNativeDriver: true }),
    [scrollX],
  );

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

  // A trainee can be unlocked only so many times in a training: past that, explain instead of
  // asking for a reason (the server refuses it either way).
  const requestUnlock = (item: ParticipantItem) => {
    const lock = item.proctoring;
    if (lock && lock.unlocksUsed >= lock.maxUnlocks) {
      Alert.alert(
        "Unlock limit reached",
        `${item.name} has already been unlocked ${lock.maxUnlocks} times in this training. ` +
          `Only ${lock.maxUnlocks} unlocks are allowed per trainee, so they stay locked.`,
      );
      return;
    }
    setUnlockTarget(item);
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
          <Ionicons name="people" size={18} color={Colors.black} />
          <AppText style={styles.title}>PARTICIPANT MASTER LIST</AppText>
        </View>
        <Pressable style={styles.refreshBtn} onPress={onRefresh} hitSlop={6}>
          <Ionicons name="reload" size={11} color={Colors.gray700} />
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

      {/* Header and rows scroll sideways together; every cell gets a fixed width from the same
          `widths`, so each column lines up whatever is in it. The Participant Details column stays
          frozen on the left while the others scroll under it. */}
      <Animated.ScrollView
        horizontal
        style={styles.table}
        showsHorizontalScrollIndicator
        accessibilityHint="Scroll sideways to see every column"
        onLayout={(event) => setTableArea(event.nativeEvent.layout.width)}
        onScroll={onTableScroll}
        scrollEventThrottle={16}
      >
        <View>
          <View style={styles.thRow}>
            {HEADINGS.map(({ column, label }) =>
              column === "details" ? (
                <Animated.View
                  key={column}
                  style={[
                    participantCell,
                    frozenDetailsCell,
                    styles.frozenHeading,
                    { width: widths[column], transform: [{ translateX: frozenOffset }] },
                  ]}
                >
                  <AppText style={[styles.thText, styles.thTextLeft]}>{label}</AppText>
                </Animated.View>
              ) : (
                <View key={column} style={[participantCell, { width: widths[column] }]}>
                  <AppText style={styles.thText}>{label}</AppText>
                </View>
              ),
            )}
          </View>

          {filtered.map((item, idx) => {
            // The mapper only attaches `proctoring` when the backend row is
            // locked, so its presence is the lock.
            const isLocked = !!item.proctoring;
            return (
              <ParticipantRow
                key={item.id}
                item={item}
                widths={widths}
                frozenOffset={frozenOffset}
                alt={idx % 2 === 1}
                isLocked={isLocked}
                canEdit={canEdit}
                onCheck={() => setMarkTarget({ participant: item, status: "Present" })}
                onReject={() => setMarkTarget({ participant: item, status: "Absent" })}
                onShowSuspicious={() => setSuspicious(item)}
                onUnlock={() => requestUnlock(item)}
              />
            );
          })}
        </View>
      </Animated.ScrollView>

      {/* Outside the sideways scroll, so it stays centred on screen. */}
      {filtered.length === 0 && (
        <AppText style={styles.empty}>
          {participants.length === 0 ? "No one has joined yet." : "No match."}
        </AppText>
      )}

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
    borderColor: Colors.borderLight,
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
  title: { fontSize: 11.5, fontWeight: "800", color: Colors.black, letterSpacing: 0.3 },
  refreshBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.gray50,
    borderWidth: 1,
    borderColor: Colors.gray300,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  refreshText: { fontSize: 9, color: Colors.gray700, fontWeight: "600" },
  filterRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  filterLabel: { fontSize: 8.5, color: Colors.gray600 },
  searchBox: { flexDirection: "row", alignItems: "center", gap: 6 },
  searchInput: {
    borderWidth: 1,
    borderColor: Colors.gray300,
    borderRadius: 6,
    width: 110,
    height: 24,
    fontSize: 9,
    paddingHorizontal: 8,
    paddingVertical: 0,
  },
  table: { borderRadius: 8 },
  thRow: {
    flexDirection: "row",
    backgroundColor: Colors.gray50,
    alignItems: "center",
    borderWidth: HEADER_BORDER_WIDTH,
    borderColor: Colors.gray200,
    paddingVertical: HEADING_VERTICAL_PADDING,
    // The border is inside the row's width, so it comes off the padding: same cell widths as a data row.
    paddingHorizontal: ROW_SIDE_PADDING - HEADER_BORDER_WIDTH,
    borderRadius: HEADING_RADIUS,
  },
  thText: { fontSize: 9, fontWeight: "700", color: Colors.gray700, textAlign: "center", lineHeight: 10.5 },
  thTextLeft: { textAlign: "left" },
  // The frozen heading cell: the bar's full height in the bar's colour, its left corners following
  // the bar's rounded border, so the headings scrolling under it stay hidden.
  frozenHeading: {
    alignSelf: "stretch",
    marginVertical: -HEADING_VERTICAL_PADDING,
    paddingVertical: HEADING_VERTICAL_PADDING,
    backgroundColor: Colors.gray50,
    borderTopLeftRadius: HEADING_RADIUS - HEADER_BORDER_WIDTH,
    borderBottomLeftRadius: HEADING_RADIUS - HEADER_BORDER_WIDTH,
  },
  empty: { fontSize: 10, color: Colors.gray500, textAlign: "center", paddingVertical: 18 },
  paginationInfo: { fontSize: 8, color: Colors.gray500, marginTop: 8 },
});
