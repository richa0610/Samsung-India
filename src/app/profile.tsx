import { StatusBar } from "expo-status-bar";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import EditProfileSheet from "@/components/common/EditProfileSheet";
import TraineeBottomNavigation from "@/components/session/TraineeBottomNavigation";
import { DetailsCard, ProfileHeader, SecurityBanner, useProfile } from "@/components/trainee/profile";

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const {
    trainee,
    uploading,
    editVisible,
    setEditVisible,
    handleLogout,
    handlePickPhoto,
    handleTabSelect,
    personalDetails,
    organizationDetails,
    sessionPillLabel,
  } = useProfile();

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={[styles.statusBarBackground, { height: insets.top }]} />
      <StatusBar style="light" animated />

      <ProfileHeader
        trainee={trainee}
        uploading={uploading}
        sessionPillLabel={sessionPillLabel}
        onPickPhoto={handlePickPhoto}
        onLogout={handleLogout}
      />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <DetailsCard tag="PERSONAL DETAILS" items={personalDetails} onEdit={() => setEditVisible(true)} />
        <DetailsCard tag="ORGANIZATION DETAILS" items={organizationDetails} onEdit={() => setEditVisible(true)} />
        <SecurityBanner />
      </ScrollView>

      <EditProfileSheet visible={editVisible} onClose={() => setEditVisible(false)} />

      <TraineeBottomNavigation activeTab="profile" onSelectTab={handleTabSelect} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F0F4FC",
  },
  statusBarBackground: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: "#0066FF",
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 24,
    gap: 14,
  },
});
