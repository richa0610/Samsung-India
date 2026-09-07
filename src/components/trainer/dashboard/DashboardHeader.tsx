import { Ionicons } from "@expo/vector-icons";
import { Image, Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { Shadows } from "@/theme/shadows";

type DashboardHeaderProps = {
  name: string;
  companyId: string;
  avatarUri?: string | null;
  onOpenProfile: () => void;
  onLogout: () => void;
};

export default function DashboardHeader({
  name,
  companyId,
  avatarUri,
  onOpenProfile,
  onLogout,
}: DashboardHeaderProps) {
  return (
    <ScreenBanner backgroundColor={Colors.mainColour1} style={styles.banner}>
      <View style={styles.topRow}>
        <View style={styles.avatarWithId}>
          <Pressable
            style={styles.avatarWrapper}
            onPress={onOpenProfile}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel="Account settings"
          >
            <Image
              source={
                avatarUri
                  ? { uri: avatarUri }
                  : require("@/assets/images/Icons/face_icon.png")
              }
              style={styles.avatarImage}
              resizeMode="cover"
            />
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
              {companyId}
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
          Welcome Back,
        </AppText>
        <AppText
          style={styles.welcomeName}
          color={Colors.white}
          weight={FontWeight.medium}
        >
          {name}
        </AppText>
      </View>
    </ScreenBanner>
  );
}

const styles = StyleSheet.create({
  banner: {
    margin: 10,
    paddingHorizontal: 14,
    paddingTop: 20,
    paddingBottom: 18,
    borderRadius: 20,
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
    width: 64,
    height: 64,
  },
  avatarOnlineBadge: {
    position: "absolute",
    bottom: 0,
    right: 0,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: "#22C55E",
    borderWidth: 2.5,
    borderColor: Colors.mainColour1,
  },
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
