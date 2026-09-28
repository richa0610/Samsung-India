import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";

import CalendarIcon from "@/assets/images/svg/calender.svg";
import { TrainingAgendaItem } from "@/api/training";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";
import { formatSessionTime, getSessionStatusInfo } from "./dashboardUtils";

type RecentSessionsCardProps = {
  sessions: TrainingAgendaItem[];
  onViewAll: () => void;
  onSelectSession: (conferenceUid: string) => void;
};

export default function RecentSessionsCard({
  sessions,
  onViewAll,
  onSelectSession,
}: RecentSessionsCardProps) {
  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <AppText style={styles.title}>Recent Sessions</AppText>
        <Pressable style={styles.viewAllPill} onPress={onViewAll} hitSlop={6}>
          <AppText style={styles.viewAllText}>View All</AppText>
        </Pressable>
      </View>

      {sessions.length === 0 ? (
        <AppText style={styles.emptyText}>No sessions yet</AppText>
      ) : (
        <View style={styles.list}>
          {sessions.map((session, index) => {
          const statusInfo = getSessionStatusInfo(session.conferenceStatus);
          const isLive = statusInfo.label === "Live";
          const iconColor = isLive ? Colors.red : Colors.statusGreen;
          const iconBg = isLive ? Colors.dangerBg : Colors.successBgSoft;

          return (
            <View key={session.conferenceUid}>
              {index > 0 && <View style={styles.divider} />}
              <Pressable
                style={styles.itemRow}
                onPress={() => onSelectSession(session.conferenceUid)}
              >
                <View style={styles.itemContent}>
                  <View
                    style={[styles.calendarBox, { backgroundColor: iconBg }]}
                  >
                    <CalendarIcon
                      width={14}
                      height={14}
                      color={iconColor}
                      stroke={iconColor}
                    />
                  </View>

                  <View style={styles.infoWrapper}>
                    <AppText style={styles.sessionTitle} numberOfLines={1}>
                      {session.title || "Training Session"}
                    </AppText>
                    <AppText style={styles.sessionDateTime}>
                      {formatSessionTime(
                        session.conferenceDate,
                        session.conferenceTime,
                      )}
                    </AppText>
                  </View>
                </View>

                {/* Status badge */}
                <View style={styles.statusBadgeRow}>
                  <View
                    style={[
                      styles.statusBadge,
                      { backgroundColor: statusInfo.bg },
                    ]}
                  >
                    <AppText
                      style={[
                        styles.statusBadgeText,
                        { color: statusInfo.color },
                      ]}
                    >
                      {statusInfo.label}
                    </AppText>
                  </View>
                </View>
              </Pressable>
            </View>
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 14,
    borderWidth: 1.2,
    borderColor: Colors.borderLight,
    padding: 8,
    ...Shadows.card,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  title: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.black,
  },
  viewAllPill: {
    borderWidth: 1,
    borderColor: Colors.gray300,
    borderRadius: 5,
    paddingHorizontal: 5,
    paddingVertical: 1.5,
    backgroundColor: Colors.white,
  },
  viewAllText: {
    fontSize: 8,
    color: Colors.gray600,
    fontWeight: "500",
  },
  list: {
    gap: 5,
  },
  emptyText: {
    fontSize: 10,
    color: Colors.gray500,
    paddingVertical: 8,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.gray100,
    marginVertical: 4,
  },
  itemRow: {
    paddingVertical: 2,
  },
  itemContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  calendarBox: {
    width: 30,
    height: 30,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  infoWrapper: {
    flex: 1,
  },
  sessionTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: Colors.black,
  },
  sessionDateTime: {
    fontSize: 9,
    color: Colors.gray500,
    marginTop: 1,
  },
  statusBadgeRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 4,
    paddingVertical: 1.5,
    borderRadius: 3,
  },
  statusBadgeText: {
    fontSize: 7.5,
    fontWeight: "600",
  },
});
