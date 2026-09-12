import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import LinkIcon from "@/assets/images/svg/session/link.svg";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type SessionDashboardHeaderProps = {
  conferenceUid: string;
  timestamp?: string;
  isClosed?: boolean;
  hasStarted?: boolean;
  isLive?: boolean;
  isApproved?: boolean;
  // True while the scheduled date is still in the future - the trainer can't
  // start the session before then.
  notYetDue?: boolean;
  startsOnLabel?: string;
  // The Session Report is only meaningful once the session has ended.
  reportEnabled?: boolean;
  loading?: boolean;
  // True while fetching the trainer's live location, required before the
  // check-in camera opens - disables the button so it can't be tapped twice.
  startingSession?: boolean;
  onBack: () => void;
  onCopyLink: () => void;
  onShowQR: () => void;
  onRefresh: () => void;
  onReport: () => void;
  onStartSession: () => void;
  onEndSession: () => void;
};

export default function SessionDashboardHeader({
  conferenceUid,
  timestamp = "Generated: 29 July 2026, 11:09 AM",
  isClosed = false,
  hasStarted = true,
  isLive = false,
  isApproved = true,
  notYetDue = false,
  startsOnLabel,
  reportEnabled = true,
  loading = false,
  startingSession = false,
  onBack,
  onCopyLink,
  onShowQR,
  onRefresh,
  onReport,
  onStartSession,
  onEndSession,
}: SessionDashboardHeaderProps) {
  const insets = useSafeAreaInsets();
  const topPadding = insets.top > 0 ? insets.top + 2 : 6;

  return (
    <>
      <StatusBar style="dark" />
      <View style={[styles.container, { paddingTop: topPadding }]}>
        {/* Top Header Row */}
        <View style={styles.topRow}>
          <View style={styles.leftContent}>
            {/* Back Circular Button */}
            <Pressable
              style={styles.backCircleBtn}
              onPress={onBack}
              hitSlop={8}
              accessibilityRole="button"
              accessibilityLabel="Back"
            >
              <Ionicons name="arrow-back" size={17} color={Colors.white} />
            </Pressable>

            {/* Title, Badge & Subtitle */}
            <View style={styles.titleWrapper}>
              <AppText style={styles.title}>SESSION DASHBOARD</AppText>
              <View style={styles.uidBadge}>
                <AppText style={styles.uidText}>
                  {conferenceUid ? conferenceUid.toUpperCase() : "CONF2627273"}
                </AppText>
              </View>
              <AppText style={styles.subtitle}>{timestamp}</AppText>
            </View>
          </View>

          {/* Right Top Buttons: Copy Link & Show QR */}
          <View style={styles.rightButtons}>
            <Pressable
              style={styles.headerSquareBtn}
              onPress={onCopyLink}
              hitSlop={6}
              accessibilityRole="button"
              accessibilityLabel="Copy Link"
            >
              <LinkIcon width={16} height={16} />
              <AppText style={styles.squareBtnText}>Copy Link</AppText>
            </Pressable>

            {isLive && (
              <Pressable
                style={styles.headerSquareBtn}
                onPress={onShowQR}
                hitSlop={6}
                accessibilityRole="button"
                accessibilityLabel="Show QR"
              >
                <Ionicons name="qr-code-outline" size={16} color={Colors.white} />
                <AppText style={styles.squareBtnText}>Show QR</AppText>
              </Pressable>
            )}
          </View>
        </View>

        {/* Bottom Action Bar */}
        <View style={styles.bottomActionBar}>
          {/* Left Side: Refresh Button + Report Button */}
          <View style={styles.bottomLeftActions}>
            <Pressable
              style={styles.refreshBtn}
              onPress={onRefresh}
              hitSlop={6}
              accessibilityRole="button"
              accessibilityLabel="Refresh"
            >
              <Ionicons name="reload" size={15} color="#0066FF" />
            </Pressable>

            <Pressable
              style={[styles.reportBtn, !reportEnabled && styles.reportBtnDisabled]}
              onPress={onReport}
              disabled={!reportEnabled}
              accessibilityRole="button"
              accessibilityLabel="Report"
              accessibilityState={{ disabled: !reportEnabled }}
            >
              <Ionicons
                name={reportEnabled ? "document-text-outline" : "lock-closed"}
                size={14}
                color={reportEnabled ? "#374151" : "#9CA3AF"}
              />
              <AppText style={[styles.reportBtnText, !reportEnabled && styles.reportBtnTextDisabled]}>
                Report
              </AppText>
            </Pressable>
          </View>

          {/* Right Side: Start/End Session Button / Session Closed indicator */}
          {loading ? (
            <View style={[styles.endSessionBtn, styles.sessionLoadingBtn]}>
              <AppText style={[styles.endSessionBtnText, styles.sessionLoadingBtnText]}>Loading...</AppText>
            </View>
          ) : isClosed ? (
            <View style={[styles.endSessionBtn, styles.sessionClosedBtn]}>
              <AppText style={styles.endSessionBtnText}>Session Closed</AppText>
            </View>
          ) : !hasStarted && !isApproved ? (
            <View style={[styles.endSessionBtn, styles.sessionPendingBtn]}>
              <Ionicons name="time-outline" size={12} color="#92400E" />
              <AppText style={[styles.endSessionBtnText, styles.sessionPendingBtnText]}>Awaiting Approval</AppText>
            </View>
          ) : !hasStarted && notYetDue ? (
            <View style={[styles.endSessionBtn, styles.sessionScheduledBtn]}>
              <Ionicons name="lock-closed" size={12} color="#475569" />
              <AppText style={[styles.endSessionBtnText, styles.sessionScheduledBtnText]}>
                {startsOnLabel ? `Starts ${startsOnLabel}` : "Not started"}
              </AppText>
            </View>
          ) : !hasStarted ? (
            <Pressable
              style={[styles.endSessionBtn, styles.startSessionBtn]}
              onPress={onStartSession}
              disabled={startingSession}
              accessibilityRole="button"
              accessibilityLabel="Start Session"
            >
              {startingSession ? (
                <ActivityIndicator size="small" color={Colors.white} />
              ) : (
                <Ionicons name="play" size={12} color={Colors.white} />
              )}
              <AppText style={styles.endSessionBtnText}>
                {startingSession ? "Getting Location…" : "Start Session"}
              </AppText>
            </Pressable>
          ) : (
            <Pressable
              style={styles.endSessionBtn}
              onPress={onEndSession}
              accessibilityRole="button"
              accessibilityLabel="End Session"
            >
              <View style={styles.whiteStopIcon}>
                <Ionicons name="square" size={11} color={Colors.white} />
              </View>
              <AppText style={styles.endSessionBtnText}>End Session</AppText>
            </Pressable>
          )}
        </View>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#0066FF",
    marginHorizontal: 14,
    paddingHorizontal: 12,
    paddingBottom: 10,
    borderRadius: 20,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  leftContent: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    flex: 1,
  },
  backCircleBtn: {
    width: 30,
    height: 30,
    borderRadius: 15,
    borderWidth: 1.2,
    borderColor: "rgba(255, 255, 255, 0.4)",
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  titleWrapper: {
    gap: 2,
    flex: 1,
  },
  title: {
    fontSize: 13.5,
    fontWeight: "800",
    color: Colors.white,
    letterSpacing: 0.3,
  },
  uidBadge: {
    backgroundColor: "rgba(255, 255, 255, 0.22)",
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
    alignSelf: "flex-start",
    marginTop: 1,
  },
  uidText: {
    fontSize: 9,
    fontWeight: "700",
    color: Colors.white,
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 8.5,
    color: "rgba(255, 255, 255, 0.9)",
    fontWeight: "500",
    marginTop: 1,
  },
  rightButtons: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginLeft: 6,
  },
  headerSquareBtn: {
    width: 44,
    height: 40,
    backgroundColor: "rgba(255, 255, 255, 0.12)",
    borderWidth: 1.2,
    borderColor: "rgba(255, 255, 255, 0.45)",
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
    gap: 1,
  },
  squareBtnText: {
    fontSize: 7,
    color: Colors.white,
    fontWeight: "600",
  },
  bottomActionBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 4,
    marginTop: 10,
    ...Shadows.card,
  },
  bottomLeftActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  refreshBtn: {
    width: 32,
    height: 28,
    borderRadius: 8,
    backgroundColor: "#EFF6FF",
    alignItems: "center",
    justifyContent: "center",
  },
  reportBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderWidth: 1.2,
    borderColor: "#D1D5DB",
    backgroundColor: Colors.white,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  reportBtnDisabled: {
    backgroundColor: "#F3F4F6",
    borderColor: "#E5E7EB",
    opacity: 0.7,
  },
  reportBtnText: {
    fontSize: 12,
    color: "#374151",
    fontWeight: "700",
  },
  reportBtnTextDisabled: {
    color: "#9CA3AF",
  },
  endSessionBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: "#DC2626",
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  sessionClosedBtn: {
    backgroundColor: "#111827",
  },
  startSessionBtn: {
    backgroundColor: Colors.success,
  },
  sessionPendingBtn: {
    backgroundColor: "#FEF3C7",
  },
  sessionPendingBtnText: {
    color: "#92400E",
  },
  sessionScheduledBtn: {
    backgroundColor: "#E2E8F0",
  },
  sessionScheduledBtnText: {
    color: "#475569",
  },
  sessionLoadingBtn: {
    backgroundColor: "#E5E7EB",
  },
  sessionLoadingBtnText: {
    color: "#6B7280",
  },
  whiteStopIcon: {
    alignItems: "center",
    justifyContent: "center",
  },
  endSessionBtnText: {
    fontSize: 12,
    color: Colors.white,
    fontWeight: "700",
  },
});
