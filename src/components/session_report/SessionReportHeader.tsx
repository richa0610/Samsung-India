import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import AppText from "@/components/ui/AppText";
import ScreenBanner from "@/components/ui/ScreenBanner";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type SessionReportHeaderProps = {
  onBack: () => void;
};

export default function SessionReportHeader({ onBack }: SessionReportHeaderProps) {
  const insets = useSafeAreaInsets();

  return (
    <ScreenBanner
      backgroundColor={Colors.mainColour1}
      statusBarStyle="light"
      style={[styles.banner, { paddingTop: insets.top + 4 }]}
    >
      <View style={styles.row}>
        <Pressable
          style={styles.backCircleBtn}
          onPress={onBack}
          hitSlop={8}
          accessibilityRole="button"
          accessibilityLabel="Back"
        >
          <Ionicons name="chevron-back" size={20} color={Colors.white} />
        </Pressable>
        <View style={styles.titleWrapper}>
          <AppText style={styles.title} color={Colors.white} weight={FontWeight.semiBold}>
            SESSION REPORT
          </AppText>
          <AppText style={styles.subtitle} color={Colors.white}>
            Detailed overview of all training sessions
          </AppText>
        </View>
      </View>
    </ScreenBanner>
  );
}

const styles = StyleSheet.create({
  banner: { paddingBottom: 60 },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  backCircleBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.2,
    borderColor: "rgba(255, 255, 255, 0.4)",
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  titleWrapper: { gap: 0 },
  title: { fontSize: Fonts.h3, letterSpacing: 0.3 },
  subtitle: { fontSize: Fonts.overline, opacity: 0.9 },
});
