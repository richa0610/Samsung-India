import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { Image } from "expo-image";

import AppText from "@/components/ui/AppText";
import MediaImage from "@/components/ui/MediaImage";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Shadows } from "@/theme/shadows";

type AdminDashboardHeaderProps = {
  adminName?: string;
  companyId?: string | null;
  avatarUrl?: string | null;
  /** Tapping the avatar - the admin picks a new profile photo. */
  onOpenProfile?: () => void;
  uploadingPhoto?: boolean;
  onLogout: () => void;
};

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good Morning";
  if (hour < 17) return "Good Afternoon";
  return "Good Evening";
}

export default function AdminDashboardHeader({
  adminName,
  companyId,
  avatarUrl,
  onOpenProfile,
  uploadingPhoto = false,
  onLogout,
}: AdminDashboardHeaderProps) {
  return (
    <ScreenBanner backgroundColor={Colors.mainColour1} style={styles.banner}>
      <View style={styles.decorLarge} pointerEvents="none" />
      <View style={styles.decorSmall} pointerEvents="none" />
      <View style={styles.topRow}>
        <View style={styles.avatarWithId}>
          <Pressable
            style={styles.avatarWrapper}
            onPress={onOpenProfile}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel="Change profile photo"
          >
            {avatarUrl ? (
              <MediaImage
                path={avatarUrl}
                style={styles.avatarImage}
                contentFit="cover"
                fallback={
                  <Image
                    source={require("@/assets/images/Icons/face_icon.png")}
                    style={styles.avatarImage}
                    contentFit="cover"
                  />
                }
              />
            ) : (
              <Image
                source={require("@/assets/images/Icons/face_icon.png")}
                style={styles.avatarImage}
                contentFit="cover"
              />
            )}
            {uploadingPhoto && (
              <View style={styles.uploadOverlay}>
                <ActivityIndicator color={Colors.white} />
              </View>
            )}
            <View style={styles.cameraBadge}>
              <Ionicons name="camera" size={11} color={Colors.mainColour1} />
            </View>
            <View style={styles.avatarOnlineBadge} />
          </Pressable>

          <View style={styles.companyIdContainer}>
            <AppText style={styles.companyIdLabel} color={Colors.white}>
              Company ID
            </AppText>
            <AppText
              style={styles.companyIdValue}
              color={Colors.white}
              weight={FontWeight.bold}
            >
              {companyId ?? "OFF26005"}
            </AppText>
          </View>
        </View>

        <Pressable
          style={styles.powerButton}
          onPress={onLogout}
          hitSlop={8}
          accessibilityRole="button"
          accessibilityLabel="Logout"
        >
          <Ionicons name="power" size={25} color={Colors.mainColour1} />
        </Pressable>
      </View>

      <View style={styles.welcomeSection}>
        <AppText style={styles.welcomeGreeting} color={Colors.white}>
          {greeting()},
        </AppText>
        <AppText
          style={styles.welcomeName}
          color={Colors.white}
          weight={FontWeight.bold}
        >
          {adminName ?? "Admin"}
        </AppText>
        <View style={styles.rolePill}>
          <Ionicons name="shield-checkmark" size={12} color={Colors.white} />
          <AppText style={styles.rolePillText} color={Colors.white} weight={FontWeight.bold}>
            Administrator
          </AppText>
        </View>
      </View>
    </ScreenBanner>
  );
}

const styles = StyleSheet.create({
  banner: {
    marginHorizontal: 16,
    marginTop: 10,
    marginBottom: 4,
    paddingHorizontal: 14,
    paddingTop: 20,
    paddingBottom: 18,
    borderRadius: 24,
    overflow: "hidden",
    ...Shadows.raised,
  },
  decorLarge: {
    position: "absolute",
    width: 170,
    height: 170,
    borderRadius: 85,
    backgroundColor: "rgba(255,255,255,0.10)",
    top: -60,
    right: -40,
  },
  decorSmall: {
    position: "absolute",
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: "rgba(255,255,255,0.08)",
    bottom: -30,
    right: 70,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  avatarWithId: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  avatarWrapper: {
    position: "relative",
    width: 60,
    height: 60,
  },
  avatarImage: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#DCEBFE",
    borderWidth: 2.5,
    borderColor: "rgba(255,255,255,0.85)",
  },
  uploadOverlay: {
    ...StyleSheet.absoluteFill,
    borderRadius: 30,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
  },
  cameraBadge: {
    position: "absolute",
    bottom: 0,
    left: 0,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...Shadows.card,
  },
  avatarOnlineBadge: {
    position: "absolute",
    bottom: 2,
    right: 2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: "#22C55E",
    borderWidth: 2,
    borderColor: Colors.mainColour1,
  },
  rolePill: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 5,
    marginTop: 8,
    backgroundColor: "rgba(255,255,255,0.18)",
    borderRadius: 9999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  rolePillText: { fontSize: 10, letterSpacing: 0.4 },
  companyIdContainer: {
    gap: 1,
  },
  companyIdLabel: {
    fontSize: 12,
  },
  companyIdValue: {
    fontSize: 14,
    letterSpacing: 0.3,
  },
  powerButton: {
    width: 41,
    height: 40,
    borderRadius: 10,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...Shadows.card,
  },
  welcomeSection: {
    marginTop: 14,
  },
  welcomeGreeting: {
    fontSize: 12,
  },
  welcomeName: {
    fontSize: 20,
  },
});
