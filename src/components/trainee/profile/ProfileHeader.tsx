import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Image, Pressable, StyleSheet, View } from "react-native";

import Calendar from "@/assets/images/svg/calender2.svg";
import AppText from "@/components/ui/AppText";
import { Trainee } from "@/api/auth";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { createShadow } from "@/theme/shadows";
import { traineeAvatar } from "@/utils/traineeAvatar";

type ProfileHeaderProps = {
  trainee: Trainee | null;
  uploading: boolean;
  sessionPillLabel: string;
  onPickPhoto: () => void;
  onLogout: () => void;
};

export default function ProfileHeader({ trainee, uploading, sessionPillLabel, onPickPhoto, onLogout }: ProfileHeaderProps) {
  const { token } = useAuth();
  return (
    <View style={styles.header}>
      <View style={styles.headerTopRow}>
        <View style={styles.profileMetaRow}>
          <Pressable
            style={styles.avatarWrap}
            onPress={onPickPhoto}
            disabled={uploading}
            accessibilityRole="button"
            accessibilityLabel="Change profile picture"
          >
            <Image source={traineeAvatar(trainee, token)} style={styles.avatar} />
            <View style={styles.onlineDot} />
            {uploading && (
              <View style={styles.uploadingOverlay}>
                <ActivityIndicator size="small" color={Colors.white} />
              </View>
            )}
          </Pressable>

          <View style={styles.userTextColumn}>
            <AppText style={styles.userName} color={Colors.white} weight={FontWeight.bold}>
              {trainee?.name || "Tushar Prajapati"}
            </AppText>
            <AppText style={styles.userRole} color={Colors.white}>
              {trainee?.designation || "SEC"}
            </AppText>
          </View>
        </View>

        <Pressable style={styles.powerButton} onPress={onLogout} accessibilityRole="button" accessibilityLabel="Logout">
          <Ionicons name="power" size={24} color="#0066FF" />
        </Pressable>
      </View>

      <View style={styles.sessionPill}>
        <Calendar width={13} height={13} color="#0066FF" />
        <AppText style={styles.sessionPillText} color="#0066FF" weight={FontWeight.bold}>
          {sessionPillLabel}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: "#0066FF",
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 22,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerTopRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  profileMetaRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  avatarWrap: { position: "relative" },
  avatar: { width: 60, height: 60, borderRadius: 30, backgroundColor: "#DCEBFE" },
  onlineDot: {
    position: "absolute",
    bottom: 2,
    right: 2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: "#22C55E",
    borderWidth: 2,
    borderColor: "#0066FF",
  },
  uploadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 30,
    backgroundColor: "rgba(0, 0, 0, 0.4)",
    alignItems: "center",
    justifyContent: "center",
  },
  userTextColumn: { gap: 2 },
  userName: { fontSize: 18, letterSpacing: 0.2 },
  userRole: { fontSize: 13, opacity: 0.95 },
  powerButton: {
    width: 41,
    height: 40,
    borderRadius: 10,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow({ x: 0, y: 2, blur: 6, opacity: 0.08, elevation: 2 }),
  },
  sessionPill: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 16,
    backgroundColor: Colors.white,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 16,
  },
  sessionPillText: { fontSize: 11, letterSpacing: 0.3 },
});
