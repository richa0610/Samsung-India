import { useState } from "react";
import { StyleSheet, View, Pressable } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import AppCard from "@/components/ui/AppCard";
import AuthHeader from "@/components/common/AppHeader";
import AppText from "@/components/ui/AppText";
import AppInput from "@/components/ui/AppInput";
import AppButton from "@/components/ui/AppButton";
import RegisterSheet from "@/components/common/RegisterSheet";
import SecurityFooter from "@/components/common/SecurityFooter";
// import RegisterBottomSheet from "@/components/bottom-sheet/RegisterSheet";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { ApiError, loginTrainee } from "@/api/auth";
import { joinSession } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";
import { digitsOnly } from "@/utils/validation";

export default function Starter1() {
  const router = useRouter();
  // Present when the user got here from a scanned session QR
  // (samsungindia://join/<code> -> join screen -> "Continue to Login").
  const { join } = useLocalSearchParams<{ join?: string }>();
  const { setSession } = useAuth();
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const openRegister = () => setIsRegisterOpen(true);
  const closeRegister = () => setIsRegisterOpen(false);

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
        // Came from a scanned session QR - bind this trainee to that session,
        // then land on its details screen.
        try {
          await joinSession(join, session.access_token);
        } catch {
          // Non-fatal: they still reach /session, just without the bind.
        }
        router.replace("/session");
      } else {
        // Trainees land on the live session timeline; the stats/dashboard
        // page is a tab in the bottom nav from there.
        router.replace("/session_detail" as any);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <StatusBar
        style="dark"
      />
      <SafeAreaView style={styles.container}>
        <View style={styles.content}>
          <AppCard style={styles.headert}>
            <AuthHeader />
            <View style={styles.body}>
              <AppInput
                label="Company ID / Phone No"
                placeholder="Enter Company ID or Phone No"
                value={phone}
                onChangeText={(value) => {
                  setPhone(digitsOnly(value).slice(0, 10));
                  if (error) setError(null);
                }}
                keyboardType="number-pad"
                maxLength={10}
              />
              {error && (
                <AppText style={styles.error}>{error}</AppText>
              )}
              <View style={styles.actionsRow}>
                <AppButton
                  title="Continue"
                  onPress={handleContinue}
                  loading={loading}
                  buttonStyle={styles.continueButton}
                />
              </View>
              <Pressable onPress={openRegister}>
                <AppText
                  weight="500"
                  style={styles.register}
                >
                  New User ? Register
                </AppText>
              </Pressable>
            </View>
          </AppCard>
          <View style={styles.securityFooter}>
            <SecurityFooter />
          </View>
          <RegisterSheet
            visible={isRegisterOpen}
            onClose={closeRegister}
            joinCode={join}
          />
          {/* <RegisterBottomSheet
          ref={bottomSheetRef}
        /> */}
        </View>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#EEF4FF",
  },
  headert: {
    width: "95%",
  },
  body: {
    padding: 20,
  },
  actionsRow: {
    flexDirection: "row",
    gap: 10,
  },
  continueButton: {
    flex: 1,
  },
  register: {
    marginTop: 15,
    textAlign: "center",
    textDecorationLine: "underline",
    fontSize: Fonts.bodySm,
  },
  error: {
    color: Colors.danger,
    fontSize: Fonts.bodySm,
    marginBottom: 12,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  securityFooter: {
    marginTop: 42,
  },
});
