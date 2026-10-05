import { Ionicons } from "@expo/vector-icons";
import { Image } from "expo-image";
import { useLocalSearchParams, useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ApiError, loginTrainee } from "@/api/auth";
import { joinSession } from "@/api/session";
import RegisterSheet from "@/components/common/RegisterSheet";
import AppText from "@/components/ui/AppText";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { Spacing } from "@/theme/spacing";
import { FontWeight } from "@/theme/typography";

import TraineeHeroSection from "./TraineeHeroSection";
import TraineeLoginCard from "./TraineeLoginCard";

const BACKGROUND_IMAGE = require("@/assets/bg/trainee_bg.jpg");

export default function TraineeLoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { join } = useLocalSearchParams<{ join?: string }>();
  const { setSession } = useAuth();

  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  const handleContinue = async () => {
    const trimmed = phone.trim();
    if (!trimmed) {
      setError("Enter your Company ID or Phone No");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const session = await loginTrainee(trimmed);
      setSession(session);
      if (join) {
        try {
          await joinSession(join, session.access_token);
        } catch {
          // Non-fatal: still lands on /session without direct bind
        }
        router.replace("/session");
      } else {
        router.replace("/session_detail" as any);
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />

      {/* Full-Screen Background Image with 3D Cap and Soft Waves */}
      <Image
        source={BACKGROUND_IMAGE}
        style={StyleSheet.absoluteFill}
        contentFit="cover"
        contentPosition="top"
        accessible={false}
      />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing.xl }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          bounces={false}
        >
          {/* Header & Hero Section */}
          <TraineeHeroSection />

          {/* Login Card */}
          <TraineeLoginCard
            phone={phone}
            setPhone={setPhone}
            password={password}
            setPassword={setPassword}
            loading={loading}
            error={error}
            setError={setError}
            onSubmit={handleContinue}
            onRegisterPress={() => setIsRegisterOpen(true)}
          />

          {/* Security Badge Footer */}
          <View style={styles.securityFooter} accessible accessibilityRole="text">
            <View style={styles.shieldTile}>
              <Ionicons name="shield-checkmark" size={18} color={Colors.primary} />
            </View>
            <AppText color={Colors.textSupporting} weight={FontWeight.medium} style={styles.securityText}>
              Your information is secure
            </AppText>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* New User Registration Modal */}
      <RegisterSheet
        visible={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        joinCode={join}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.white,
  },
  flex: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
  },
  securityFooter: {
    alignItems: "center",
    justifyContent: "center",
    marginTop: Spacing.xl,
    paddingBottom: Spacing.sm,
  },
  shieldTile: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: Colors.blue50,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Spacing.xxs,
  },
  securityText: {
    fontSize: 12,
  },
});
