import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Alert, Pressable, StyleSheet, View } from "react-native";
import Svg, { Defs, LinearGradient, Rect, Stop } from "react-native-svg";

import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { STAFF_LOGIN_TEXT } from "@/constants/strings";
import { Colors } from "@/theme/colors";
import { Radius } from "@/theme/radius";
import { createShadow } from "@/theme/shadows";
import { Spacing } from "@/theme/spacing";
import { FontWeight } from "@/theme/typography";
import { digitsOnly } from "@/utils/validation";

const cardShadow = createShadow({
  x: 0,
  y: 6,
  blur: 18,
  color: Colors.authButtonStart,
  opacity: 0.08,
  elevation: 4,
});

type TraineeLoginCardProps = {
  phone: string;
  setPhone: (phone: string) => void;
  password: string;
  setPassword: (password: string) => void;
  loading: boolean;
  error: string | null;
  setError: (error: string | null) => void;
  onSubmit: () => void;
  onRegisterPress: () => void;
};

export default function TraineeLoginCard({
  phone,
  setPhone,
  password,
  setPassword,
  loading,
  error,
  setError,
  onSubmit,
  onRegisterPress,
}: TraineeLoginCardProps) {
  const handleForgotPassword = () => {
    Alert.alert(STAFF_LOGIN_TEXT.forgotTitle, STAFF_LOGIN_TEXT.forgotMessage);
  };

  return (
    <View style={[styles.card, cardShadow]}>
      {/* Title & Subtitle */}
      <View style={styles.cardHeader}>
        <AppText variant="h2" color={Colors.authHeadline} weight={FontWeight.bold} style={styles.title}>
          Trainee Login
        </AppText>
        <AppText color={Colors.authCardSubtitle} style={styles.subtitle}>
          Enter your credentials to continue
        </AppText>
      </View>

      {/* Inputs */}
      <View style={styles.fields}>
        <AppInput
          label="Company ID / Phone No"
          placeholder="Enter Company ID or Phone No"
          icon="business-outline"
          value={phone}
          onChangeText={(value) => {
            setPhone(digitsOnly(value).slice(0, 10));
            if (error) setError(null);
          }}
          keyboardType="number-pad"
          maxLength={10}
          placeholderTextColor={Colors.authPlaceholder}
          labelColor={Colors.authLabel}
          containerStyle={styles.field}
        />

        <AppInput
          label={STAFF_LOGIN_TEXT.passwordLabel}
          placeholder="Enter password"
          icon="lock-closed-outline"
          value={password}
          onChangeText={(value) => {
            setPassword(value);
            if (error) setError(null);
          }}
          secureTextEntry
          returnKeyType="go"
          onSubmitEditing={onSubmit}
          placeholderTextColor={Colors.authPlaceholder}
          labelColor={Colors.authLabel}
          containerStyle={styles.passwordField}
        />
      </View>

      {/* Forgot Password Link */}
      <Pressable
        onPress={handleForgotPassword}
        hitSlop={8}
        style={styles.forgotButton}
        accessibilityRole="button"
        accessibilityLabel={STAFF_LOGIN_TEXT.forgot}
      >
        <AppText color={Colors.primary} weight={FontWeight.medium} style={styles.forgotText}>
          {STAFF_LOGIN_TEXT.forgot}
        </AppText>
      </Pressable>

      {/* Error Message */}
      {error && (
        <AppText color={Colors.danger} style={styles.errorText}>
          {error}
        </AppText>
      )}

      {/* Submit Button with Gradient */}
      <Pressable
        onPress={onSubmit}
        disabled={loading}
        style={({ pressed }) => [styles.submitButton, pressed && styles.submitPressed]}
        accessibilityRole="button"
        accessibilityLabel="Login as Trainee"
        accessibilityState={{ busy: loading, disabled: loading }}
      >
        <Svg style={StyleSheet.absoluteFill} pointerEvents="none">
          <Defs>
            <LinearGradient id="traineeSubmit" x1="0" y1="0" x2="1" y2="0">
              <Stop offset="0" stopColor={Colors.authButtonStart} />
              <Stop offset="1" stopColor={Colors.authButtonEnd} />
            </LinearGradient>
          </Defs>
          <Rect width="100%" height="100%" rx={Radius.xxl} fill="url(#traineeSubmit)" />
        </Svg>
        {loading ? (
          <ActivityIndicator color={Colors.white} />
        ) : (
          <View style={styles.submitContent}>
            <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.submitText}>
              Login as Trainee
            </AppText>
            <Ionicons name="arrow-forward" size={18} color={Colors.white} />
          </View>
        )}
      </Pressable>

      {/* New User Register Row */}
      <View style={styles.registerRow}>
        <View style={styles.dividerLine} />
        <Pressable
          onPress={onRegisterPress}
          hitSlop={8}
          style={styles.registerPressable}
          accessibilityRole="button"
          accessibilityLabel="New User ? Register"
        >
          <AppText color={Colors.gray600} style={styles.registerPrompt}>
            New User ?{" "}
            <AppText color={Colors.primary} weight={FontWeight.semiBold} style={styles.registerLink}>
              Register
            </AppText>
          </AppText>
        </Pressable>
        <View style={styles.dividerLine} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.header,
    borderWidth: 1,
    borderColor: Colors.authCardBorder,
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.xxl,
    marginHorizontal: Spacing.lg,
  },
  cardHeader: {
    marginBottom: Spacing.lg,
  },
  title: {
    fontSize: 20,
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 13,
    marginTop: Spacing.xxs,
  },
  fields: {
    width: "100%",
  },
  field: {
    marginBottom: Spacing.md,
  },
  passwordField: {
    marginBottom: Spacing.xs,
  },
  forgotButton: {
    alignSelf: "flex-end",
    marginBottom: Spacing.lg,
    paddingVertical: Spacing.xxs,
  },
  forgotText: {
    fontSize: 13,
  },
  errorText: {
    fontSize: 13,
    marginBottom: Spacing.md,
  },
  submitButton: {
    height: 50,
    borderRadius: Radius.xxl,
    overflow: "hidden",
    justifyContent: "center",
    alignItems: "center",
  },
  submitPressed: {
    opacity: 0.88,
  },
  submitContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
  },
  submitText: {
    fontSize: 15,
  },
  registerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: Spacing.xl,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.borderLight,
  },
  registerPressable: {
    paddingHorizontal: Spacing.md,
  },
  registerPrompt: {
    fontSize: 13,
  },
  registerLink: {
    textDecorationLine: "underline",
  },
});
