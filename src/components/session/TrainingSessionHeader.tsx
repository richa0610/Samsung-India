import { Ionicons } from "@expo/vector-icons";
import {
  Image,
  ImageSourcePropType,
  Pressable,
  StyleSheet,
  View,
} from "react-native";

import CalendarIcon from "@/assets/images/svg/calender2.svg";
import AppText from "@/components/ui/AppText";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { FontWeight } from "@/theme/typography";
import { traineeAvatar } from "@/utils";

export type TrainingSessionHeaderProps = {
  onBack?: () => void;
  onLogout?: () => void;
  onHistoryPress?: () => void;
  userName?: string;
  gender?: string | null;
  profilePhoto?: string | null;
  isOnline?: boolean;
  confirmationStatus?: string;
  sessionType?: string;
  title?: string;
  date?: string;
  location?: string;
};

export default function TrainingSessionHeader({
  onBack,
  onLogout,
  userName = "Trainee",
  gender,
  profilePhoto,
  confirmationStatus = "Not Confirmed",
  sessionType = "Training",
  title = "Training Session",
  date = "--",
  location = "--",
}: TrainingSessionHeaderProps) {
  const { token } = useAuth();
  const avatar: ImageSourcePropType = traineeAvatar({ gender, profilePhoto }, token);

  const isConfirmed =
    confirmationStatus.toLowerCase().includes("confirmed") &&
    !confirmationStatus.toLowerCase().includes("not");

  return (
    <View style={styles.header}>
      {/* Top Profile & Actions Row */}
      <View style={styles.topRow}>
        {onBack && (
          <Pressable
            onPress={onBack}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Back"
            style={styles.backButton}
          >
            <Ionicons name="chevron-back" size={22} color={Colors.white} />
          </Pressable>
        )}

        <View style={styles.profileSection}>
          {/* Avatar with Online Status Dot */}
          <View style={styles.avatarContainer}>
            <Image
              source={avatar}
              style={[
                styles.avatar,
                profilePhoto ? styles.avatarPhoto : undefined,
              ]}
            />
          </View>

          {/* User Details */}
          <View style={styles.userMeta}>
            <AppText
              variant="body"
              color={Colors.white}
              weight={FontWeight.medium}
            >
              {userName}
            </AppText>

            <View style={styles.statusRow}>
              <View
                style={[
                  styles.statusIndicator,
                  {
                    backgroundColor: isConfirmed
                      ? Colors.statusGreen
                      : Colors.statusYellow,
                  },
                ]}
              />
              <AppText
                variant="tiny"
                color={Colors.white}
                style={styles.statusText}
              >
                {confirmationStatus}
              </AppText>
            </View>
          </View>
        </View>

        {/* Header Action Buttons */}
        <View>
          {onLogout && (
            <Pressable
              style={styles.actionBtn}
              onPress={onLogout}
              accessibilityRole="button"
              accessibilityLabel="Logout"
            >
              <Ionicons name="power" size={25} color={Colors.headerBlue} />
            </Pressable>
          )}
        </View>
      </View>

      {/* Session Type Pill */}
      <View style={styles.sessionPill}>
        <CalendarIcon width={13} height={13} color={Colors.headerBlue} />
        <AppText
          variant="overline"
          color={Colors.headerBlue}
          weight={FontWeight.bold}
        >
          {sessionType}
        </AppText>
      </View>

      {/* Large Session Title */}
      <AppText
        variant="h2"
        color={Colors.white}
        weight={FontWeight.bold}
        style={styles.sessionTitle}
      >
        {title}
      </AppText>

      {/* Date & Location Meta Row */}
      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <CalendarIcon width={14} height={14} color={Colors.white} />
          <AppText
            variant="caption"
            color={Colors.white}
            style={styles.metaText}
          >
            {date}
          </AppText>
        </View>

        <View style={styles.verticalDivider} />

        <View style={styles.metaItem}>
          <Ionicons name="location-outline" size={15} color={Colors.white} />
          <AppText
            variant="caption"
            color={Colors.white}
            style={styles.metaText}
          >
            {location}
          </AppText>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: Colors.headerBlue,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 22,
    borderBottomLeftRadius: Radius.header,
    borderBottomRightRadius: Radius.header,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  backButton: {
    marginRight: 8,
  },
  profileSection: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  avatarContainer: {
    position: "relative",
  },
  avatar: {
    width: 81,
    height: 60,
  },
  avatarPhoto: {
    borderRadius: 24,
  },
  userMeta: {
    gap: 1,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  statusIndicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    opacity: 0.95,
  },
  actionBtn: {
    width: 41,
    height: 40,
    borderRadius: 8,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  sessionPill: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginTop: 16,
    backgroundColor: Colors.white,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: Radius.pill,
  },
  sessionTitle: {
    marginTop: 10,
    letterSpacing: 0.3,
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 12,
    gap: 12,
  },
  metaItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  metaText: {
    opacity: 0.95,
  },
  verticalDivider: {
    width: 1,
    height: 14,
    backgroundColor: Colors.white,
    opacity: 0.6,
  },
});
