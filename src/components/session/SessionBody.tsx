import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, RefreshControl, StyleSheet, View } from "react-native";

import { CurrentSession } from "@/api/session";
import { SessionActivityData } from "@/hooks/useTraineeHome";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/typography";
import SessionNotification from "./SessionNotification";
import SessionTimeline from "./SessionTimeline";
import WaitingCard from "./WaitingCard";

type SessionBodyProps = {
  loading: boolean;
  session: CurrentSession | null;
  notAssigned: boolean;
  notStarted: boolean;
  ejected: boolean;
  sessionClosed: boolean;
  error: string | null;
  activities: SessionActivityData[];
  refreshing: boolean;
  loadSession: (mode?: "load" | "refresh") => void;
  onMarkAttendance: () => void;
  onEnterLiveQuiz: () => void;
  onEnterPostTest: () => void;
  onEnterSurvey: () => void;
  onCheckInLocation: (moduleKey: SessionActivityData["key"]) => void;
};

export default function SessionBody({
  loading,
  session,
  notAssigned,
  notStarted,
  ejected,
  sessionClosed,
  error,
  activities,
  refreshing,
  loadSession,
  onMarkAttendance,
  onEnterLiveQuiz,
  onEnterPostTest,
  onEnterSurvey,
  onCheckInLocation,
}: SessionBodyProps) {
  if (loading && !session) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={Colors.headerBlue} size="large" />
      </View>
    );
  }

  if (notAssigned) {
    return (
      <View style={styles.centered}>
        <WaitingCard title="No Session Assigned" subtitle="No session is assigned yet" />
      </View>
    );
  }

  if (ejected) {
    return (
      <View style={styles.centered}>
        <WaitingCard
          title="Marked Absent"
          subtitle="The trainer has marked you absent for this session. You can't take part unless they mark you present again."
        />
        <Pressable
          style={styles.retryButton}
          onPress={() => loadSession("refresh")}
          accessibilityRole="button"
          accessibilityLabel="Refresh attendance status"
        >
          <AppText variant="label" color={Colors.white}>
            Refresh Status
          </AppText>
        </Pressable>
      </View>
    );
  }

  if (sessionClosed) {
    return (
      <View style={styles.centered}>
        <WaitingCard
          title="Session Ended"
          subtitle="This session has ended. Your next session will show up here when it starts."
          icon="checkmark-done-circle"
        />
        <Pressable
          style={styles.retryButton}
          onPress={() => loadSession("refresh")}
          accessibilityRole="button"
          accessibilityLabel="Refresh session status"
        >
          <AppText variant="label" color={Colors.white}>
            Refresh
          </AppText>
        </Pressable>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <AppText variant="body" color={Colors.gray600} align="center">
          {error}
        </AppText>
        <Pressable
          style={styles.retryButton}
          onPress={() => loadSession()}
          accessibilityRole="button"
          accessibilityLabel="Retry loading session"
        >
          <AppText variant="label" color={Colors.white}>
            Retry
          </AppText>
        </Pressable>
      </View>
    );
  }

  return (
    <>
      {notStarted && (
        <View style={styles.notStartedBanner}>
          <Ionicons name="hourglass-outline" size={16} color={Colors.headerBlue} />
          <AppText variant="caption" color={Colors.headerBlue} weight={FontWeight.medium}>
            Waiting for the trainer to start the session
          </AppText>
        </View>
      )}

      <SessionTimeline
        activities={activities}
        dimmed={notStarted}
        onMarkAttendance={onMarkAttendance}
        onEnterQuiz={onEnterLiveQuiz}
        onEnterPostTest={onEnterPostTest}
        onEnterSurvey={onEnterSurvey}
        onCheckInLocation={onCheckInLocation}
        footerComponent={<SessionNotification />}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => loadSession("refresh")}
            colors={[Colors.headerBlue]}
            tintColor={Colors.headerBlue}
          />
        }
      />
    </>
  );
}

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingHorizontal: 24,
  },
  retryButton: {
    backgroundColor: Colors.headerBlue,
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 8,
  },
  notStartedBanner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: Colors.waitingBlueBg,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
});
