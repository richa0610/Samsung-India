import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { TrainingAgendaItem } from "@/api/training";
import {
  getSessionStatusConfig,
  parseSessionDate,
} from "./sessionsUtils";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

type SessionCardProps = {
  item: TrainingAgendaItem;
  onLaunch: (conferenceUid: string) => void;
  onReport: (conferenceUid: string) => void;
};

export default function SessionCard({
  item,
  onLaunch,
  onReport,
}: SessionCardProps) {
  const config = getSessionStatusConfig(
    item.conferenceStatus,
    item.approvalStatus
  );

  const { day, month, time } = parseSessionDate(
    item.conferenceDate,
    item.conferenceTime
  );

  const handleAction = () => {
    if (config.buttonType === "launch") {
      onLaunch(item.conferenceUid);
    } else {
      onReport(item.conferenceUid);
    }
  };

  return (
    <View style={[styles.card, { borderColor: config.borderColor }]}>
      {/* Left Date Column */}
      <View style={styles.dateColumn}>
        <AppText style={styles.dayNumber}>{day}</AppText>
        <AppText style={styles.monthText}>{month}</AppText>
        <AppText style={styles.timeText}>{time}</AppText>
      </View>

      {/* Middle Details Column */}
      <View style={styles.detailsColumn}>
        {/* Status Badge + Conf UID Row */}
        <View style={styles.statusRow}>
          <View style={[styles.statusBadge, { backgroundColor: config.badgeBg }]}>
            {config.dotColor && (
              <View
                style={[styles.statusDot, { backgroundColor: config.dotColor }]}
              />
            )}
            <AppText
              style={[
                styles.statusBadgeText,
                { color: config.badgeTextColor },
              ]}
            >
              {config.label}
            </AppText>
          </View>

          <AppText style={styles.confUidText}>
            {item.conferenceUid.toUpperCase()}
          </AppText>
        </View>

        {/* Title */}
        <AppText style={styles.title} numberOfLines={1}>
          {item.title || "Training Session"}
        </AppText>

        {/* Location */}
        <View style={styles.locationRow}>
          <Ionicons name="location" size={13} color="#EF4444" />
          <AppText style={styles.locationText} numberOfLines={1}>
            {item.trainingHub || item.state || "New Delhi"}
          </AppText>
        </View>
      </View>

      {/* Right Action Column: Button + Batch Size */}
      <View style={styles.actionColumn}>
        <Pressable
          style={[styles.actionBtn, { backgroundColor: config.buttonBg }]}
          onPress={handleAction}
          accessibilityRole="button"
          accessibilityLabel={config.buttonText}
        >
          <AppText style={styles.actionBtnText}>{config.buttonText}</AppText>
        </Pressable>

        <AppText style={styles.batchSizeText}>
          Batch Size : {item.batchSize || "25"}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.white,
    borderRadius: 16,
    borderWidth: 1.4,
    paddingVertical: 12,
    paddingHorizontal: 12,
    marginBottom: 10,
    ...Shadows.card,
  },
  dateColumn: {
    width: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRightWidth: 1,
    borderRightColor: "#F3F4F6",
    paddingRight: 8,
  },
  dayNumber: {
    fontSize: 18,
    fontWeight: "800",
    color: "#111827",
    lineHeight: 22,
  },
  monthText: {
    fontSize: 9.5,
    fontWeight: "600",
    color: "#6B7280",
    letterSpacing: 0.3,
  },
  timeText: {
    fontSize: 10.5,
    fontWeight: "700",
    color: "#0066FF",
    marginTop: 2,
  },
  detailsColumn: {
    flex: 1,
    paddingHorizontal: 10,
    justifyContent: "center",
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    flexWrap: "wrap",
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
  },
  statusBadgeText: {
    fontSize: 8.5,
    fontWeight: "700",
    letterSpacing: 0.3,
  },
  confUidText: {
    fontSize: 9,
    fontWeight: "500",
    color: "#9CA3AF",
  },
  title: {
    fontSize: 13.5,
    fontWeight: "700",
    color: "#111827",
    marginTop: 4,
  },
  locationRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    marginTop: 3,
  },
  locationText: {
    fontSize: 11,
    color: "#4B5563",
    fontWeight: "500",
  },
  actionColumn: {
    alignItems: "center",
    justifyContent: "center",
  },
  actionBtn: {
    paddingHorizontal: 16,
    paddingVertical: 7,
    borderRadius: 14,
    minWidth: 80,
    alignItems: "center",
    justifyContent: "center",
  },
  actionBtnText: {
    fontSize: 11.5,
    fontWeight: "800",
    color: Colors.white,
    letterSpacing: 0.5,
  },
  batchSizeText: {
    fontSize: 9,
    color: "#6B7280",
    marginTop: 4,
    fontWeight: "500",
  },
});
