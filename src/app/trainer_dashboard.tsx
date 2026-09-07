import { StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import DashboardBottomNav from "@/components/trainer/dashboard/DashboardBottomNav";
import TrainerDashboardScrollContent from "@/components/trainer/dashboard/TrainerDashboardScrollContent";
import TrainerMoreMenu from "@/components/trainer/dashboard/TrainerMoreMenu";
import { useTrainerDashboardScreen } from "@/components/trainer/dashboard/useTrainerDashboardScreen";
import DateDrop from "@/components/trainer/DateDrop";
import AppModal from "@/components/ui/AppModal";
import ConfirmModal from "@/components/ui/ConfirmModal";
import { Colors } from "@/theme/colors";

export default function TrainerDashboardScreen() {
  const {
    router,
    admin,
    activeTab,
    menuOpen,
    dateDropOpen,
    setDateDropOpen,
    datePreset,
    dateRange,
    refreshing,
    stats,
    recentCompleted,
    loadAgenda,
    applyDateRange,
    confirmLogoutOpen,
    requestLogout,
    cancelLogout,
    confirmLogout,
    handleLaunch,
    closePanels,
    handleBottomNavSelect,
  } = useTrainerDashboardScreen();

  return (
    <>
      <SafeAreaView style={styles.container} edges={["top"]}>
        <TrainerDashboardScrollContent
          adminName={admin?.name ?? ""}
          companyId={admin?.offerId ?? admin?.username ?? ""}
          dateRange={dateRange}
          datePreset={datePreset}
          onApplyDateRange={applyDateRange}
          stats={stats}
          recentCompleted={recentCompleted}
          refreshing={refreshing}
          onRefresh={() => loadAgenda("refresh")}
          onOpenProfile={() => router.push("/trainer_profile")}
          onLogout={requestLogout}
          onSelectSession={handleLaunch}
        />

        <DashboardBottomNav activeTab={activeTab} onSelectTab={handleBottomNavSelect} />
      </SafeAreaView>

      <TrainerMoreMenu visible={menuOpen} onClose={closePanels} />

      <AppModal visible={dateDropOpen} onClose={() => setDateDropOpen(false)} position="top" contentStyle={styles.dateDropPanel} closeOnOverlayPress>
        <DateDrop range={dateRange} preset={datePreset} onApply={applyDateRange} />
      </AppModal>

      <ConfirmModal
        visible={confirmLogoutOpen}
        icon="log-out-outline"
        tone="danger"
        title="Log Out?"
        message="Are you sure you want to go to the login page?"
        onCancel={cancelLogout}
        onConfirm={confirmLogout}
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  dateDropPanel: {
    width: "100%",
    maxHeight: "92%",
    overflow: "hidden",
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
});
