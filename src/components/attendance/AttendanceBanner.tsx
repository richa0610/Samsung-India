import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/typography";

type AttendanceBannerProps = {
  onBack: () => void;
};

export default function AttendanceBanner({ onBack }: AttendanceBannerProps) {
  return (
    <ScreenBanner backgroundColor={Colors.success}>
      <View style={styles.bannerRow}>
        <Pressable onPress={onBack} hitSlop={8}>
          <Ionicons name="arrow-back" size={20} color={Colors.white} />
        </Pressable>
        <AppText style={styles.bannerTitle} color={Colors.white} weight={FontWeight.semiBold}>
          Attendance
        </AppText>
      </View>
    </ScreenBanner>
  );
}

const styles = StyleSheet.create({
  bannerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  bannerTitle: { fontSize: Fonts.h3 },
});
