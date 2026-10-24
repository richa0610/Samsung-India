import { Ionicons } from "@expo/vector-icons";
import { ImageStyle, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { Image } from "expo-image";

import AppText from "@/components/ui/AppText";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { initialsOf } from "@/utils/initials";
import { traineeAvatar } from "@/utils/traineeAvatar";

export type AvatarPerson = {
  name?: string | null;
  gender?: string | null;
  profilePhoto?: string | null;
};

type TraineeAvatarProps = {
  person: AvatarPerson | null | undefined;
  /** The picture's size and shape. Initials take the same size, always as a circle. */
  style: StyleProp<ImageStyle>;
};

// Used when the style gives no numeric size (e.g. a percentage).
const FALLBACK_SIZE = 60;

/**
 * A trainee's avatar on every trainee screen: their photo, else the male / female picture
 * (utils/traineeAvatar), else their initials ("PS") - or a plain person icon with no name.
 */
export default function TraineeAvatar({ person, style }: TraineeAvatarProps) {
  const { token } = useAuth();
  const source = traineeAvatar(person, token);
  if (source) {
    return <Image source={source} style={style} contentFit="cover" />;
  }

  const { width, height } = StyleSheet.flatten(style) ?? {};
  const size = Math.min(sizeOr(width), sizeOr(height));
  const initials = initialsOf(person?.name);
  return (
    <View
      testID="trainee-avatar-initials"
      style={[styles.initials, style as StyleProp<ViewStyle>, { width: size, height: size, borderRadius: size / 2 }]}
    >
      {initials ? (
        <AppText weight={FontWeight.bold} color={Colors.brandBlue} style={{ fontSize: Math.round(size * 0.38) }}>
          {initials}
        </AppText>
      ) : (
        <Ionicons name="person" size={Math.round(size * 0.5)} color={Colors.brandBlue} />
      )}
    </View>
  );
}

function sizeOr(value: unknown): number {
  return typeof value === "number" && value > 0 ? value : FALLBACK_SIZE;
}

const styles = StyleSheet.create({
  initials: { alignItems: "center", justifyContent: "center", backgroundColor: "#DCEBFE" },
});
