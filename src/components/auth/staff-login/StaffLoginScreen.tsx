import { Ionicons } from "@expo/vector-icons";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
  useWindowDimensions,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Defs, LinearGradient, Rect, Stop } from "react-native-svg";

import BrandWordmark from "@/components/auth/login/BrandWordmark";
import TrainerIcon from "@/components/auth/login/TrainerIcon";
import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { STAFF_LOGIN_TEXT } from "@/constants/strings";
import { useTrainerLogin } from "@/hooks/useTrainerLogin";
import { Colors } from "@/theme/colors";
import { createShadow } from "@/theme/shadows";

const cardShadow = createShadow({ x: 0, y: 6, blur: 18, color: Colors.authButtonStart, opacity: 0.08, elevation: 4 });
const backShadow = createShadow({ x: 0, y: 2, blur: 8, color: Colors.authButtonStart, opacity: 0.12, elevation: 3 });

/** The hero text keeps to the left, clear of the background's scene on the right. */
const HERO_TEXT_WIDTH = 0.52;

/** Each role's full-screen background: its scene (top right) and the soft waves. */
const BACKGROUNDS = {
  trainer: require("@/assets/bg/trainer_bg.jpg"),
  admin: require("@/assets/bg/admin_bg.jpg"),
} as const;

type Props = {
  /** "admin" when reached through Login as -> Admin: same sign-in, admin wording. */
  portal: "trainer" | "admin";
  /** Why the user was sent here (e.g. "session_expired"), shown as a notice. */
  reason?: string;
};

function SubmitButton({ title, loading, onPress }: { title: string; loading: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      disabled={loading}
      style={({ pressed }) => [styles.submit, pressed && styles.submitPressed]}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ busy: loading, disabled: loading }}
    >
      <Svg style={StyleSheet.absoluteFill} pointerEvents="none">
        <Defs>
          <LinearGradient id="staffSubmit" x1="0" y1="0" x2="1" y2="0">
            <Stop offset="0" stopColor={Colors.authButtonStart} />
            <Stop offset="1" stopColor={Colors.authButtonEnd} />
          </LinearGradient>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#staffSubmit)" />
      </Svg>
      {loading ? (
        <ActivityIndicator color={Colors.white} />
      ) : (
        <>
          <AppText color={Colors.white} style={styles.submitText}>
            {title}
          </AppText>
          <Ionicons name="arrow-forward" size={18} color={Colors.white} />
        </>
      )}
    </Pressable>
  );
}

/** Trainer / admin sign-in: the role's background scene, the brand and headline, and the sign-in
 *  card. Both roles use the same sign-in (the server's role decides where they land); only the
 *  wording differs. Text from STAFF_LOGIN_TEXT, colours from the theme. */
export default function StaffLoginScreen({ portal, reason }: Props) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const text = STAFF_LOGIN_TEXT[portal];
  const { username, setUsername, password, setPassword, notice, loading, handleLogin } = useTrainerLogin(reason);

  const goBack = () => (router.canGoBack() ? router.back() : router.replace("/"));
  const showForgotPassword = () => Alert.alert(STAFF_LOGIN_TEXT.forgotTitle, STAFF_LOGIN_TEXT.forgotMessage);

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <Image
        source={BACKGROUNDS[portal]}
        style={StyleSheet.absoluteFill}
        contentFit="cover"
        contentPosition="top"
        accessible={false}
        testID="staff-login-background"
      />
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + 28 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={[styles.hero, { paddingTop: insets.top + 8 }]}>
            <Pressable
              onPress={goBack}
              hitSlop={8}
              style={[styles.back, backShadow]}
              accessibilityRole="button"
              accessibilityLabel={STAFF_LOGIN_TEXT.back}
            >
              <Ionicons name="arrow-back" size={20} color={Colors.authBackArrow} />
            </Pressable>

            <View style={styles.wordmark}>
              <BrandWordmark color={Colors.authBrandDeep} />
            </View>

            <AppText color={Colors.authBrandDeep} style={styles.tag}>
              {text.tag}
            </AppText>
            <View style={styles.tagUnderline} />

            <View style={[styles.heroText, { width: width * HERO_TEXT_WIDTH }]}>
              <AppText variant="hero" color={Colors.authHeadline} weight="900" size={20}>
                {text.headline}
              </AppText>
              <AppText variant="hero" color={Colors.authHeadlineAccent} size={20} weight="900">
                {text.headlineAccent}
              </AppText>
              <AppText color={Colors.authBodyText} style={styles.heroBody} size={13}>
                {text.body}
              </AppText>
            </View>
          </View>

          <View style={[styles.card, cardShadow]}>
            <View style={styles.cardHeader}>
              <View
                style={[
                  styles.iconTile,
                  { backgroundColor: portal === "admin" ? Colors.roleAdminTile : Colors.authIconTile },
                ]}
              >
                {portal === "admin" ? (
                  <Ionicons name="settings-outline" size={28} color={Colors.roleAdminIcon} />
                ) : (
                  <TrainerIcon size={28} color={Colors.authIcon} />
                )}
              </View>
              <View style={styles.cardHeaderText}>
                <AppText color={Colors.authHeadline} style={styles.cardTitle}>
                  {text.cardTitle}
                </AppText>
                <AppText color={Colors.authCardSubtitle} style={styles.cardSubtitle}>
                  {text.cardSubtitle}
                </AppText>
              </View>
            </View>

            <View style={styles.fields}>
              <AppInput
                label={text.idLabel}
                placeholder={text.idPlaceholder}
                icon="business-outline"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                returnKeyType="next"
                maxLength={10}
                placeholderTextColor={Colors.authPlaceholder}
                labelStyle={styles.label}
                style={styles.input}
                containerStyle={styles.field}
              />
              <AppInput
                label={STAFF_LOGIN_TEXT.passwordLabel}
                placeholder={STAFF_LOGIN_TEXT.passwordPlaceholder}
                icon="lock-closed-outline"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                returnKeyType="go"
                onSubmitEditing={handleLogin}
                maxLength={15}
                placeholderTextColor={Colors.authPlaceholder}
                labelStyle={styles.label}
                style={styles.input}
                containerStyle={styles.passwordField}
              />
            </View>

            <Pressable onPress={showForgotPassword} hitSlop={8} style={styles.forgot} accessibilityRole="button">
              <AppText color={Colors.authLink} style={styles.forgotText}>
                {STAFF_LOGIN_TEXT.forgot}
              </AppText>
            </Pressable>

            {notice && (
              <AppText variant="caption" color={Colors.mainColour1} align="center" style={styles.notice}>
                {notice}
              </AppText>
            )}

            <SubmitButton title={text.submit} loading={loading} onPress={handleLogin} />

            <View style={styles.secure}>
              <View style={styles.secureTile}>
                <Ionicons name="shield-outline" size={18} color={Colors.authSecureIcon} />
              </View>
              <View style={styles.secureText}>
                <AppText color={Colors.authSecureTitle} style={styles.secureTitle}>
                  {STAFF_LOGIN_TEXT.secureTitle}
                </AppText>
                <AppText color={Colors.authSecureText} style={styles.secureBody}>
                  {STAFF_LOGIN_TEXT.secureBody}
                </AppText>
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.authPageTop },
  flex: { flex: 1 },
  scroll: { flexGrow: 1 },
  hero: { paddingHorizontal: 20 },
  back: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  wordmark: { marginTop: 10 },
  tag: { fontSize: 13, lineHeight: 17, fontWeight: "600", marginTop: 20 },
  tagUnderline: { width: 24, height: 2.5, borderRadius: 2, backgroundColor: Colors.authTagUnderline, marginTop: 7 },
  heroText: { marginTop: 14 },
  heroBody: { fontSize: 13, lineHeight: 17, marginTop: 6 },
  card: {
    marginTop: 19,
    marginHorizontal: 15,
    backgroundColor: Colors.white,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.authCardBorder,
    paddingTop: 14,
    paddingHorizontal: 17,
    paddingBottom: 22,
  },
  cardHeader: { flexDirection: "row", alignItems: "center" },
  iconTile: { width: 52, height: 52, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  cardHeaderText: { flex: 1, marginLeft: 16 },
  cardTitle: { fontSize: 17, lineHeight: 22, fontWeight: "700" },
  cardSubtitle: { fontSize: 13, lineHeight: 17, marginTop: 3 },
  fields: { marginTop: 24 },
  label: { fontSize: 13, lineHeight: 17, fontWeight: "900", color: Colors.authLabel, marginBottom: 6 },
  input: { height: 44, borderRadius: 6, borderColor: Colors.authInputBorder, fontSize: 14 },
  field: { marginBottom: 18 },
  passwordField: { marginBottom: 0 },
  forgot: { alignSelf: "flex-end", marginTop: 8 },
  forgotText: { fontSize: 13, lineHeight: 17, fontWeight: "500" },
  notice: { marginTop: 12 },
  submit: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: 46,
    borderRadius: 6,
    overflow: "hidden",
    marginTop: 22,
  },
  submitPressed: { opacity: 0.9 },
  submitText: { fontSize: 15, lineHeight: 20, fontWeight: "600" },
  secure: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.authSecureBg,
    borderRadius: 8,
    paddingVertical: 9,
    paddingHorizontal: 10,
    marginTop: 22,
  },
  secureTile: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: Colors.authSecureTile,
    alignItems: "center",
    justifyContent: "center",
  },
  secureText: { flex: 1, marginLeft: 15 },
  secureTitle: { fontSize: 13, lineHeight: 17, fontWeight: "500" },
  secureBody: { fontSize: 12, lineHeight: 16, marginTop: 1 },
});
