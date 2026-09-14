import { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

import DashboardBottomNav, { DashboardTab } from "@/components/trainer/dashboard/DashboardBottomNav";
import TrainerMoreMenu from "@/components/trainer/dashboard/TrainerMoreMenu";
import AppText from "@/components/ui/AppText";
import LogoutConfirmModal from "@/components/ui/LogoutConfirmModal";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { useAuth } from "@/hooks/useAuth";
import {
  DocumentsSection,
  LocalAddressSection,
  OfficialInfoSection,
  PersonalDetailsSection,
  ProfileHeaderCard,
  SecuritySection,
  SocialMediaSection,
  useTrainerProfileForm,
} from "@/components/trainer/profile";

export default function TrainerProfileScreen() {
  const router = useRouter();
  const { admin, adminLogout } = useAuth();
  const form = useTrainerProfileForm();
  const [bottomTab, setBottomTab] = useState<DashboardTab>("profile");
  const [moreOpen, setMoreOpen] = useState(false);
  // Same confirm-before-logout flow as the Trainer Dashboard's power button
  // (see useTrainerDashboardScreen) - opening the popup here is separate
  // from actually logging out, which only happens on confirm.
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);

  const requestLogout = () => setConfirmLogoutOpen(true);
  const cancelLogout = () => setConfirmLogoutOpen(false);
  const confirmLogout = () => {
    setConfirmLogoutOpen(false);
    adminLogout();
    router.replace("/trainer_login");
  };

  const handleBottomNavSelect = (tab: DashboardTab) => {
    setBottomTab(tab);
    if (tab === "home") {
      router.replace("/trainer_dashboard");
    } else if (tab === "plan") {
      router.push("/sessions");
    } else if (tab === "more") {
      setMoreOpen(true);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <ScrollView contentContainerStyle={styles.content}>
        <ProfileHeaderCard
          name={admin?.name ?? "Demo Trainer"}
          onLogout={requestLogout}
          photoUrl={form.profile?.profilePicture}
          uploading={form.uploadingPhoto}
          onPickPhoto={form.handlePickPhoto}
        />

        {/* A section's own validation error (bad email/mobile/pincode/etc.)
            surfaces here rather than inline in that section - notice is one
            shared string on the form, not tracked per-section, and the
            failing section could be scrolled out of view by the time the
            error comes back. Previously this was computed but never
            rendered anywhere, so a failed save looked like nothing happened. */}
        {form.notice && (
          <AppText style={styles.notice} color={Colors.danger}>
            {form.notice}
          </AppText>
        )}

        {form.loading ? (
          <View style={styles.centered}>
            <ActivityIndicator color={Colors.mainColour1} />
          </View>
        ) : (
          <>
            <PersonalDetailsSection form={form} />
            <LocalAddressSection form={form} />
            <DocumentsSection form={form} />
            <SocialMediaSection form={form} />
            <OfficialInfoSection form={form} />
            <SecuritySection form={form} />
          </>
        )}
      </ScrollView>

      <DashboardBottomNav activeTab={bottomTab} onSelectTab={handleBottomNavSelect} />

      <TrainerMoreMenu visible={moreOpen} onClose={() => setMoreOpen(false)} />

      <LogoutConfirmModal visible={confirmLogoutOpen} onCancel={cancelLogout} onConfirm={confirmLogout} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { flexGrow: 1, padding: 16, paddingTop: 4, paddingBottom: 16, gap: 4 },
  centered: { paddingVertical: 60, alignItems: "center" },
  notice: { fontSize: Fonts.bodySm, textAlign: "center", marginTop: 4, marginBottom: 4 },
});
