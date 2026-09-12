import { StatusBar } from "expo-status-bar";
import { StyleSheet, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import {
  RecentSessionsModal,
  SessionBody,
  TraineeBottomNavigation,
  TrainingSessionHeader,
} from "@/components/session";
import { useTraineeHome } from "@/hooks/useTraineeHome";
import { Colors } from "@/theme/colors";
import { formatDisplayDate } from "@/utils/formatDisplayDate";

export default function SessionDetailScreen() {
  const insets = useSafeAreaInsets();
  const {
    trainee,
    token,
    session,
    activities,
    loading,
    refreshing,
    error,
    notAssigned,
    notStarted,
    ejected,
    sessionClosed,
    activeTab,
    historyVisible,
    setHistoryVisible,
    loadSession,
    handleMarkAttendance,
    handleCheckInToModule,
    handleEnterLiveQuiz,
    handleEnterPostTest,
    handleEnterSurvey,
    handleLogout,
    handleTabSelect,
  } = useTraineeHome();

  return (
    <>
      <SafeAreaView style={styles.container} edges={["top"]}>
        <View style={[styles.statusBarBackground, { height: insets.top }]} />
        <StatusBar style="dark" animated />

        <TrainingSessionHeader
          onLogout={handleLogout}
          onHistoryPress={() => setHistoryVisible(true)}
          userName={trainee?.name ?? "Trainee"}
          gender={trainee?.gender}
          profilePhoto={trainee?.profilePhoto}
          isOnline={true}
          confirmationStatus={session?.confirmationStatus ?? "Not Confirmed"}
          sessionType={session?.sessionType ?? "Training"}
          title={session?.title ?? "Training Session"}
          date={session?.date ? formatDisplayDate(session.date) : "--"}
          location={session?.location ?? "--"}
        />

        <View style={styles.body}>
          <SessionBody
            loading={loading}
            session={session}
            notAssigned={notAssigned}
            notStarted={notStarted}
            ejected={ejected}
            sessionClosed={sessionClosed}
            error={error}
            activities={activities}
            refreshing={refreshing}
            loadSession={loadSession}
            onMarkAttendance={handleMarkAttendance}
            onCheckInLocation={handleCheckInToModule}
            onEnterLiveQuiz={handleEnterLiveQuiz}
            onEnterPostTest={handleEnterPostTest}
            onEnterSurvey={handleEnterSurvey}
          />
        </View>

        <TraineeBottomNavigation activeTab={activeTab} onSelectTab={handleTabSelect} />
      </SafeAreaView>

      <RecentSessionsModal visible={historyVisible} onClose={() => setHistoryVisible(false)} token={token} />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  statusBarBackground: {
    position: "absolute",
    left: 0,
    right: 0,
    top: 0,
    backgroundColor: Colors.headerBlue,
  },
  body: {
    flex: 1,
    minHeight: 0,
    backgroundColor: Colors.background,
  },
});
