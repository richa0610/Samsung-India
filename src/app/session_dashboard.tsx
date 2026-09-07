import { SafeAreaView } from "react-native-safe-area-context";
import { StyleSheet } from "react-native";

import { SessionDashboardHeader } from "@/components/session_dashboard";
import {
  DashboardScrollContent,
  OutsideVenueModal,
  SessionQRModal,
  TrainerCheckInModal,
  TrainerCheckOutModal,
  useSessionDashboardScreen,
} from "@/components/session_dashboard/dashboard-screen";
import DashboardBottomNav from "@/components/trainer/dashboard/DashboardBottomNav";
import TrainerMoreMenu from "@/components/trainer/dashboard/TrainerMoreMenu";

export default function SessionDashboardScreen() {
  const {
    router,
    conferenceUid,
    data,
    generatedAt,
    loading,
    refreshing,
    showQR,
    setShowQR,
    showCheckInModal,
    setShowCheckInModal,
    bottomTab,
    moreOpen,
    setMoreOpen,
    loadData,
    handleCopyLink,
    handleStartSession,
    requestingStartLocation,
    handleConfirmStartSession,
    outsideVenue,
    handleUpdateVenueLocation,
    dismissOutsideVenue,
    showCheckOutModal,
    setShowCheckOutModal,
    endingSession,
    handleConfirmEndSession,
    handleMarkAttendance,
    handleUnlockExam,
    handleStartModule,
    handleStopActiveModule,
    handleRestartModule,
    handleEndSession,
    liveQuizControls,
    handleBottomNavSelect,
    isSessionClosed,
    showSessionData,
    isLive,
    isApproved,
    notYetDue,
    startsOnLabel,
  } = useSessionDashboardScreen();

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <SessionDashboardHeader
        conferenceUid={conferenceUid}
        isClosed={isSessionClosed}
        hasStarted={showSessionData}
        isLive={isLive}
        isApproved={isApproved}
        notYetDue={notYetDue}
        startsOnLabel={startsOnLabel}
        reportEnabled={isSessionClosed}
        loading={loading}
        timestamp={generatedAt}
        onBack={() => router.back()}
        onCopyLink={handleCopyLink}
        onShowQR={() => setShowQR(true)}
        onRefresh={() => loadData("refresh")}
        onReport={() => router.push({ pathname: "/session_report", params: { conferenceUid } })}
        onStartSession={handleStartSession}
        startingSession={requestingStartLocation}
        onEndSession={handleEndSession}
      />

      <DashboardScrollContent
        data={data}
        isSessionClosed={isSessionClosed}
        showSessionData={showSessionData}
        refreshing={refreshing}
        onRefresh={() => loadData("refresh")}
        onStartModule={handleStartModule}
        onStopActiveModule={handleStopActiveModule}
        onRestartModule={handleRestartModule}
        onMarkAttendance={handleMarkAttendance}
        onUnlockExam={handleUnlockExam}
        liveQuizControls={liveQuizControls}
      />

      <DashboardBottomNav activeTab={bottomTab} onSelectTab={handleBottomNavSelect} />

      <TrainerMoreMenu visible={moreOpen} onClose={() => setMoreOpen(false)} />

      <SessionQRModal visible={showQR} onClose={() => setShowQR(false)} conferenceUid={conferenceUid} />

      <TrainerCheckInModal
        visible={showCheckInModal}
        onClose={() => setShowCheckInModal(false)}
        onConfirm={handleConfirmStartSession}
      />

      <OutsideVenueModal
        prompt={outsideVenue}
        onCancel={dismissOutsideVenue}
        onSave={handleUpdateVenueLocation}
      />

      <TrainerCheckOutModal
        visible={showCheckOutModal}
        submitting={endingSession}
        onClose={() => setShowCheckOutModal(false)}
        onConfirm={handleConfirmEndSession}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F3F7FA",
  },
});
