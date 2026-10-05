import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useState } from "react";
import { StatusBar } from "expo-status-bar";
import { Pressable, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Path } from "react-native-svg";

import AppText from "@/components/ui/AppText";
import { BRAND, LOGIN_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";

import BrandWordmark from "./login/BrandWordmark";
import LoginHero from "./login/LoginHero";
import LoginOptionButton from "./login/LoginOptionButton";
import LoginRoleSheet, { StaffRole } from "./login/LoginRoleSheet";

const FOOTER_WAVE_HEIGHT = 120;

/** The app's first screen: participants join by QR or Company ID / phone; trainers and admins tap
 *  "Login here" and pick their role in the "Login as" sheet (both sign in on the same screen, worded
 *  for that role - the server's role decides where they land). All wording comes from LOGIN_TEXT /
 *  BRAND, all colours from the theme. */
export default function LoginLandingScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const [roleSheetOpen, setRoleSheetOpen] = useState(false);

  const openStaffLogin = (role: StaffRole) => {
    setRoleSheetOpen(false);
    router.push(role === "admin" ? { pathname: "/trainer_login", params: { portal: "admin" } } : "/trainer_login");
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.scroll} bounces={false} showsVerticalScrollIndicator={false}>
        <LoginHero />

        <View style={styles.body}>
          <AppText variant="h2" color={Colors.textHeading} align="center" style={styles.title}>
            {LOGIN_TEXT.title}
          </AppText>
          <AppText variant="bodySmall" color={Colors.textSupporting} align="center" style={styles.subtitle}>
            {LOGIN_TEXT.subtitle}
          </AppText>

          <View style={styles.options}>
            <LoginOptionButton icon="scan-outline" label={LOGIN_TEXT.viaQr} onPress={() => router.push("/scan")} />
            <LoginOptionButton
              icon="person-outline"
              label={LOGIN_TEXT.viaUsername}
              onPress={() => router.push("/participant_login")}
            />
          </View>

          <View style={styles.dividerRow}>
            <View style={styles.dividerLine} />
            <AppText variant="caption" color={Colors.textSupporting}>
              {LOGIN_TEXT.divider}
            </AppText>
            <View style={styles.dividerLine} />
          </View>

          <Pressable
            style={styles.staffRow}
            onPress={() => setRoleSheetOpen(true)}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`${LOGIN_TEXT.staffPrompt} ${LOGIN_TEXT.staffLink}`}
          >
            <AppText variant="label" color={Colors.textSupporting} style={styles.staffPrompt}>
              {LOGIN_TEXT.staffPrompt}
            </AppText>
            <AppText variant="label" color={Colors.mainColour1} style={styles.staffLink}>
              {LOGIN_TEXT.staffLink}
            </AppText>
            <Ionicons name="chevron-forward" size={15} color={Colors.mainColour1} />
          </Pressable>
        </View>

        <View style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}>
          <Svg
            width={width}
            height={FOOTER_WAVE_HEIGHT}
            style={styles.footerWave}
            pointerEvents="none"
          >
            <Path
              d={`M0 ${FOOTER_WAVE_HEIGHT * 0.25} C ${width * 0.25} ${FOOTER_WAVE_HEIGHT * 0.6}, ${width * 0.55} ${FOOTER_WAVE_HEIGHT * 0.15}, ${width} ${FOOTER_WAVE_HEIGHT * 0.55} L ${width} ${FOOTER_WAVE_HEIGHT} L 0 ${FOOTER_WAVE_HEIGHT} Z`}
              fill={Colors.brandTintSoft}
            />
          </Svg>
          <BrandWordmark color={Colors.brandWordmark} size="small" align="center" />
          <AppText variant="caption" color={Colors.textSupporting} style={styles.tagline}>
            {BRAND.tagline.join("  |  ")}
          </AppText>
        </View>
      </ScrollView>

      <LoginRoleSheet visible={roleSheetOpen} onClose={() => setRoleSheetOpen(false)} onChoose={openStaffLogin} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.white },
  scroll: { flexGrow: 1 },
  body: { paddingHorizontal: 24, paddingTop: 22, alignItems: "center" },
  title: { fontWeight: "700" },
  subtitle: { marginTop: 8, maxWidth: 300 },
  options: { flexDirection: "row", gap: 12, marginTop: 30, alignSelf: "stretch" },
  dividerRow: { flexDirection: "row", alignItems: "center", gap: 14, marginTop: 28, alignSelf: "stretch" },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.surfaceBorder },
  staffRow: { flexDirection: "row", alignItems: "center", marginTop: 10, gap: 4 },
  staffPrompt: { fontWeight: "400" },
  staffLink: { marginLeft: 8, fontWeight: "600" },
  footer: { marginTop: "auto", paddingTop: 40, alignItems: "center", overflow: "hidden" },
  footerWave: { position: "absolute", left: 0, bottom: 0 },
  tagline: { marginTop: 8 },
});
