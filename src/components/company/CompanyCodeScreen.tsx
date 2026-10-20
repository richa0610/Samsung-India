import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  LayoutChangeEvent,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
  useWindowDimensions,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import BrandWordmark from "@/components/auth/login/BrandWordmark";
import LoginFooter from "@/components/auth/login/LoginFooter";
import { HeroBackground } from "@/components/auth/login/LoginHero";
import AppText from "@/components/ui/AppText";
import { COMPANY_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";
import { FontWeight } from "@/theme/typography";

import CompanyCodeForm from "./CompanyCodeForm";

const cardShadow = createShadow({ x: 0, y: 10, blur: 24, color: Colors.authButtonStart, opacity: 0.12, elevation: 6 });

type CompanyCodeScreenProps = {
  /** Called once the code is confirmed and saved. */
  onDone: () => void;
  /** A back arrow - only when there is a company to go back to (changing it). */
  onCancel?: () => void;
};

/**
 * The first step on a phone that has no company yet (or is changing it): its own page, before the
 * participant / staff sign-in options - the brand banner, then one card that asks for the company
 * code. Sign-in only follows once the server confirms the code (useCompanyCodeForm).
 */
export default function CompanyCodeScreen({ onDone, onCancel }: CompanyCodeScreenProps) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const [bannerHeight, setBannerHeight] = useState(0);
  // The banner is as tall as its content; its background is drawn to match.
  const onBannerLayout = (event: LayoutChangeEvent) => setBannerHeight(Math.round(event.nativeEvent.layout.height));

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          bounces={false}
          showsVerticalScrollIndicator={false}
        >
          <View onLayout={onBannerLayout} style={[styles.banner, { paddingTop: insets.top + 20 }]}>
            {bannerHeight > 0 && <HeroBackground width={width} height={bannerHeight} />}
            <View style={styles.bannerTop}>
              {onCancel && (
                <Pressable
                  onPress={onCancel}
                  hitSlop={8}
                  style={styles.back}
                  accessibilityRole="button"
                  accessibilityLabel={COMPANY_TEXT.back}
                >
                  <Ionicons name="arrow-back" size={20} color={Colors.onHero} />
                </Pressable>
              )}
              <BrandWordmark color={Colors.onHero} />
            </View>

            <View style={styles.emblem}>
              <Ionicons name="business" size={30} color={Colors.onHero} />
            </View>
            <AppText variant="h2" color={Colors.onHero} weight={FontWeight.bold} style={styles.welcome}>
              {COMPANY_TEXT.welcome}
            </AppText>
            <AppText variant="bodySmall" color={Colors.onHero} style={styles.welcomeBody}>
              {COMPANY_TEXT.welcomeBody}
            </AppText>
          </View>

          <View style={[styles.card, cardShadow]}>
            <View style={styles.cardHeader}>
              <View style={styles.iconTile}>
                <Ionicons name="key-outline" size={24} color={Colors.authIcon} />
              </View>
              <View style={styles.cardHeaderText}>
                <AppText color={Colors.authHeadline} style={styles.cardTitle}>
                  {COMPANY_TEXT.cardTitle}
                </AppText>
                <AppText color={Colors.authCardSubtitle} style={styles.cardSubtitle}>
                  {COMPANY_TEXT.cardSubtitle}
                </AppText>
              </View>
            </View>
            <CompanyCodeForm intro={false} onDone={onDone} />
          </View>

          <View style={styles.help}>
            <Ionicons name="help-circle-outline" size={16} color={Colors.loginSubtext} />
            <AppText variant="bodySmall" color={Colors.loginSubtext} style={styles.helpText}>
              {COMPANY_TEXT.help}
            </AppText>
          </View>

          <LoginFooter />
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.white },
  flex: { flex: 1 },
  scroll: { flexGrow: 1 },
  // Bottom padding leaves room for the banner's curved fade, which the card overlaps.
  banner: { paddingHorizontal: 24, paddingBottom: 76 },
  bannerTop: { flexDirection: "row", alignItems: "center", gap: 14 },
  back: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.16)",
  },
  emblem: {
    width: 60,
    height: 60,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 28,
    backgroundColor: "rgba(255,255,255,0.16)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.28)",
  },
  welcome: { marginTop: 18 },
  welcomeBody: { marginTop: 8, maxWidth: 320, opacity: 0.92 },
  card: {
    marginTop: -44,
    marginHorizontal: 18,
    backgroundColor: Colors.white,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.authCardBorder,
    paddingTop: 18,
    paddingHorizontal: 18,
    paddingBottom: 22,
  },
  cardHeader: { flexDirection: "row", alignItems: "center" },
  iconTile: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.authIconTile,
  },
  cardHeaderText: { flex: 1, marginLeft: 14 },
  cardTitle: { fontSize: 17, lineHeight: 22, fontWeight: "700" },
  cardSubtitle: { fontSize: 13, lineHeight: 17, marginTop: 3 },
  help: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, marginTop: 18, paddingHorizontal: 24 },
  helpText: { flexShrink: 1 },
});
