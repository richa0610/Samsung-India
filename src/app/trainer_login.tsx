import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";

import AppCard from "@/components/ui/AppCard";
import AppText from "@/components/ui/AppText";
import AppInput from "@/components/ui/AppInput";
import AppButton from "@/components/ui/AppButton";
import AuthHeader from "@/components/common/AppHeader";
import SecurityFooter from "@/components/common/SecurityFooter";
import { Colors } from "@/theme/colors";
import { useTrainerLogin } from "@/hooks/useTrainerLogin";

export default function TrainerLoginScreen() {
  const router = useRouter();
  const { reason } = useLocalSearchParams<{ reason?: string }>();

  const {
    username,
    setUsername,
    password,
    setPassword,
    notice,
    loading,
    handleLogin,
  } = useTrainerLogin(reason);

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container}>
        <KeyboardAvoidingView
          style={styles.keyboardView}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <ScrollView
            style={styles.scrollView}
            contentContainerStyle={styles.content}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <Pressable
              style={styles.backButton}
              onPress={() => router.back()}
              hitSlop={8}
            >
              <Ionicons name="arrow-back" size={20} color={Colors.mainColour1} />
            </Pressable>

            <AppCard style={styles.card}>
              <AuthHeader title="Welcome Back" subtitle="Authenticate to access your session" />

              <View style={styles.body}>
                <AppInput
                  label="Company ID / Phone No"
                  placeholder="Enter Company ID or Phone No"
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                  returnKeyType="next"
                  maxLength={10}
                />
                <AppInput
                  label="Password"
                  placeholder="Enter Password"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  returnKeyType="go"
                  onSubmitEditing={handleLogin}
                  maxLength={15}
                />

                {notice && (
                  <AppText variant="caption" color={Colors.mainColour1} align="center" style={styles.notice}>
                    {notice}
                  </AppText>
                )}

                <AppButton title="Continue" onPress={handleLogin} loading={loading} />
              </View>
            </AppCard>
          </ScrollView>

          <View style={styles.securityFooter}>
            <SecurityFooter />
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#EEF4FF" },
  keyboardView: { flex: 1 },
  scrollView: { flex: 1 },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  backButton: {
    alignSelf: "flex-start",
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  card: { width: "100%" },
  body: { padding: 20, gap: 4 },
  notice: {
    marginBottom: 4,
  },
  securityFooter: { paddingVertical: 16 },
});
