import { SafeAreaView } from "react-native-safe-area-context";
import { StyleSheet } from "react-native";

import { SessionDashboardHeader } from "@/components/session_dashboard";
import {
  DashboardScrollContent,
  OutsideVenueModal,
  ScheduleOverrideModal,
  
  SessionQRModal,
  TrainerCheckInModal,
  TrainerCheckOutModal,
  useSessionDashboardScreen,
} from "@/components/session_dashboard/dashboard-screen";
import DashboardBottomNav from "@/components/trainer/dashboard/DashboardBottomNav";
import TrainerMoreMenu from "@/components/trainer/dashboard/TrainerMoreMenu";
import ConfirmModal from "@/components/ui/ConfirmModal";

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
    scheduleOverride,
    handleSubmitScheduleOverride,
    dismissScheduleOverride,
    showCheckOutModal,
    setShowCheckOutModal,
    endingSession,
    handleConfirmEndSession,
    handleMarkAttendance,
    handleUnlockExam,
    handleStartModule,
    startingModuleKey,
    handleStopActiveModule,
    confirmEndModuleOpen,
    cancelStopActiveModule,
    confirmStopActiveModule,
    handleRestartModule,
    restartingModuleKey,
    handleEndSession,
    pendingModuleLabel,
    dismissPendingModuleNotice,
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
        startingModuleKey={startingModuleKey}
        onStopActiveModule={handleStopActiveModule}
        onRestartModule={handleRestartModule}
        restartingModuleKey={restartingModuleKey}
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

      <ScheduleOverrideModal
        prompt={scheduleOverride}
        onCancel={dismissScheduleOverride}
        onSubmit={handleSubmitScheduleOverride}
      />

      <TrainerCheckOutModal
        visible={showCheckOutModal}
        submitting={endingSession}
        onClose={() => setShowCheckOutModal(false)}
        onConfirm={handleConfirmEndSession}
      />

      <ConfirmModal
        visible={confirmEndModuleOpen}
        icon="stop-circle-outline"
        tone="danger"
        title="End Module?"
        message="Do you want to end this module?"
        onCancel={cancelStopActiveModule}
        onConfirm={confirmStopActiveModule}
      />

      <ConfirmModal
        visible={pendingModuleLabel != null}
        icon="alert-circle-outline"
        tone="warning"
        title="Modules Still Pending"
        message={`"${pendingModuleLabel}" hasn't finished yet. Please end/complete every module before ending the session.`}
        singleAction
        confirmText="Got it"
        onCancel={dismissPendingModuleNotice}
        onConfirm={dismissPendingModuleNotice}
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
