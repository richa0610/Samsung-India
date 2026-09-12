import { StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import DashboardBottomNav from "@/components/trainer/dashboard/DashboardBottomNav";
import TrainerMoreMenu from "@/components/trainer/dashboard/TrainerMoreMenu";
import { SessionsHeader, SessionsListContent, useSessionsScreen } from "@/components/sessions";

export default function SessionsScreen() {
  const {
    activeTab,
    setActiveTab,
    setSearchQuery,
    filters,
    handleFiltersChange,
    locationOptions,
    sessionTypeOptions,
    dateRangeSubtitle,
    loading,
    refreshing,
    loadSessions,
    filteredSessions,
    handleLaunchSession,
    handleReportSession,
    bottomTab,
    moreOpen,
    setMoreOpen,
    handleBottomNavSelect,
  } = useSessionsScreen();

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <SessionsHeader
        dateRangeText={dateRangeSubtitle}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onSearchChange={setSearchQuery}
        filters={filters}
        onFiltersChange={handleFiltersChange}
        locationOptions={locationOptions}
        sessionTypeOptions={sessionTypeOptions}
      />

      <SessionsListContent
        loading={loading}
        refreshing={refreshing}
        onRefresh={() => loadSessions("refresh")}
        filteredSessions={filteredSessions}
        activeTab={activeTab}
        onLaunch={handleLaunchSession}
        onReport={handleReportSession}
      />

      <DashboardBottomNav activeTab={bottomTab} onSelectTab={handleBottomNavSelect} />

      <TrainerMoreMenu visible={moreOpen} onClose={() => setMoreOpen(false)} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F3F7FA",
  },
});
