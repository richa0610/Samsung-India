import { ActivityIndicator, Image, Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { resolveMediaUrl } from "@/utils/media";

type ProfileHeaderCardProps = {
  name: string;
  onLogout: () => void;
  photoUrl?: string | null;
  uploading?: boolean;
  onPickPhoto?: () => void;
};

export function ProfileHeaderCard({ name, onLogout, photoUrl, uploading = false, onPickPhoto }: ProfileHeaderCardProps) {
  const { adminToken } = useAuth();
  const initials = name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const resolvedPhotoUrl = resolveMediaUrl(photoUrl);

  return (
    <AppCard variant="mainColour1" style={styles.card}>
      <Pressable
        style={styles.avatar}
        onPress={onPickPhoto}
        disabled={!onPickPhoto || uploading}
        accessibilityRole="button"
        accessibilityLabel="Change profile picture"
      >
        {resolvedPhotoUrl ? (
          <Image
            source={{ uri: resolvedPhotoUrl, headers: adminToken ? { Authorization: `Bearer ${adminToken}` } : undefined }}
            style={styles.avatarImage}
          />
        ) : (
          <AppText style={styles.avatarText} weight={FontWeight.bold} color={Colors.mainColour1}>
            {initials}
          </AppText>
        )}
        {uploading && (
          <View style={styles.uploadingOverlay}>
            <ActivityIndicator size="small" color={Colors.white} />
          </View>
        )}
      </Pressable>
      <View style={styles.textGroup}>
        <AppText style={styles.welcome} color={Colors.white}>Welcome Back,</AppText>
        <AppText style={styles.name} color={Colors.white} weight={FontWeight.semiBold}>{name}</AppText>
      </View>
      <Pressable style={styles.logoutButton} onPress={onLogout} hitSlop={8}>
        <Ionicons name="power" size={18} color={Colors.white} />
      </Pressable>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { flexDirection: "row", alignItems: "center", gap: 12, padding: 16, marginBottom: 14 },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  avatarImage: { width: 48, height: 48 },
  avatarText: { fontSize: Fonts.body },
  uploadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 24,
    backgroundColor: "rgba(0, 0, 0, 0.4)",
    alignItems: "center",
    justifyContent: "center",
  },
  textGroup: { flex: 1 },
  welcome: { fontSize: Fonts.overline, opacity: 0.85 },
  name: { fontSize: Fonts.h3, marginTop: 2 },
  logoutButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
});
