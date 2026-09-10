import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, Share } from "react-native";

import { ApiError } from "@/api/client";
import {
  SessionDashboard,
  UploadFile,
  broadcastLiveQuestion,
  endTraining,
  fetchSessionDashboard,
  finishLiveQuiz,
  markAttendance,
  restartModule,
  showLiveLeaderboard,
  showLiveLobby,
  startModule,
  startTraining,
  stopActiveModule,
  stopLiveTimer,
  unlockProctoring,
} from "@/api/training";
import { DashboardTab } from "@/components/trainer/dashboard/DashboardBottomNav";
import { useAuth } from "@/hooks/useAuth";
import { useLiveQuizChannel } from "@/hooks/useLiveQuizChannel";
import { useLocationPermission } from "@/hooks/useLocationPermission";
import { formatDisplayDate } from "@/utils/formatDisplayDate";
import { formatGeneratedTimestamp } from "./formatting";
import { TrainerCheckInPhoto } from "./TrainerCheckInModal";

export type OutsideVenuePrompt = {
  photo: TrainerCheckInPhoto;
  distanceMeters: number;
  radius: number;
  trainerCoords: { latitude: number; longitude: number } | null;
};

export type LateStartPrompt = {
  photo: TrainerCheckInPhoto;
  trainerCoords: { latitude: number; longitude: number } | null;
  // Carried through when the trainer also corrected the venue location on the
  // way here, so the retried start keeps that fix.
  venueOverride?: { latitude: number; longitude: number };
  scheduledFor: string | null;
};

export function useSessionDashboardScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ conferenceUid?: string }>();
  const conferenceUid = params.conferenceUid || "CONF25456581";
  const { adminToken } = useAuth();

  const [data, setData] = useState<SessionDashboard | null>(null);
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [bottomTab, setBottomTab] = useState<DashboardTab>("plan");
  const [moreOpen, setMoreOpen] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [showCheckInModal, setShowCheckInModal] = useState(false);
  const [startCoords, setStartCoords] = useState<{ latitude: number; longitude: number } | null>(null);
  const [requestingStartLocation, setRequestingStartLocation] = useState(false);
  const [outsideVenue, setOutsideVenue] = useState<OutsideVenuePrompt | null>(null);
  const [lateStart, setLateStart] = useState<LateStartPrompt | null>(null);
  const [showCheckOutModal, setShowCheckOutModal] = useState(false);
  const [endingSession, setEndingSession] = useState(false);
  const [startedForUid, setStartedForUid] = useState(conferenceUid);
  const { requestLocationWithRationale } = useLocationPermission();

  if (startedForUid !== conferenceUid) {
    setStartedForUid(conferenceUid);
    setHasStarted(false);
  }

  const loadData = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      if (mode === "refresh") setRefreshing(true);
      else if (mode === "load") setLoading(true);

      try {
        const res = await fetchSessionDashboard(adminToken, conferenceUid);
        setData(res);
        setGeneratedAt(new Date());
      } catch {
        // Fallback / gracefully keep state
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoading(false);
      }
    },
    [adminToken, conferenceUid],
  );

  useFocusEffect(
    useCallback(() => {
      loadData();
      const interval = setInterval(() => loadData("silent"), 5000);
      return () => clearInterval(interval);
    }, [loadData]),
  );

  // Live Quiz room: every broadcast/answer nudge triggers a silent refetch so
  // the Live Studio card's questions / response counts / timer stay current
  // without waiting for the 5s poll.
  useLiveQuizChannel(conferenceUid, adminToken, () => loadData("silent"));

  const runLiveQuizAction = useCallback(
    async (action: (token: string, uid: string) => Promise<SessionDashboard>) => {
      if (!adminToken) return;
      try {
        setData(await action(adminToken, conferenceUid));
      } catch {
        // Fallback / gracefully keep state.
      }
    },
    [adminToken, conferenceUid],
  );

  const handleBroadcastQuestion = (questionId: number) =>
    runLiveQuizAction((token, uid) => broadcastLiveQuestion(token, uid, questionId));
  const handleStopLiveTimer = () => runLiveQuizAction(stopLiveTimer);
  const handleShowLiveLeaderboard = () => runLiveQuizAction(showLiveLeaderboard);
  const handleShowLiveLobby = () => runLiveQuizAction(showLiveLobby);
  const handleFinishLiveQuiz = () => runLiveQuizAction(finishLiveQuiz);

  const handleCopyLink = async () => {
    try {
      // Same deep link the QR encodes - opens the app on the join screen
      // (samsungindia:// scheme, see app.json). Tapping it in a chat app
      // on an Android device with the app installed opens it directly.
      await Share.share({ message: `Join the training session: samsungindia://join/${conferenceUid}` });
    } catch {
      // Ignored
    }
  };

  // Location is required to start a session - regardless of whether this
  // training has geofencing enforcement on. Fetched BEFORE the camera opens
  // (not after the photo, like before) and the flow stops here entirely if
  // it can't be obtained - no trainer photo capture, no session start,
  // without a live GPS fix. `useLocationPermission` already alerts on
  // blocked/unavailable; "denied"/cancelled need their own message since
  // that hook only sets internal error state for those, no visible alert.
  const handleStartSession = async () => {
    setRequestingStartLocation(true);
    const { coords, status } = await requestLocationWithRationale();
    setRequestingStartLocation(false);

    if (!coords) {
      if (status === "denied") {
        Alert.alert(
          "Location required",
          "We couldn't get your live location. Location is required to start this session - please try again.",
        );
      }
      return;
    }

    setStartCoords(coords);
    setShowCheckInModal(true);
  };

  const runStartSession = async (
    photo: TrainerCheckInPhoto,
    trainerCoords: { latitude: number; longitude: number } | null,
    venueOverride?: { latitude: number; longitude: number },
    lateReason?: string,
  ) => {
    if (!adminToken) return;
    try {
      await startTraining(
        adminToken,
        conferenceUid,
        photo,
        {
          latitude: trainerCoords?.latitude,
          longitude: trainerCoords?.longitude,
          venueLatitude: venueOverride?.latitude,
          venueLongitude: venueOverride?.longitude,
        },
        lateReason,
      );
      // Only flip to the "started" view once the backend actually confirms
      // it - e.g. an unapproved session gets rejected with a 403, and the
      // dashboard shouldn't show as live when nothing actually started.
      setOutsideVenue(null);
      setLateStart(null);
      setHasStarted(true);
      loadData("silent");
    } catch (err) {
      const body = err instanceof ApiError ? (err.body as { code?: string } | null) : null;
      if (err instanceof ApiError && err.status === 409 && body?.code === "OUTSIDE_VENUE" && !venueOverride) {
        const info = err.body as { distanceMeters: number; radius: number };
        setOutsideVenue({
          photo,
          distanceMeters: info.distanceMeters,
          radius: info.radius,
          trainerCoords,
        });
        return;
      }
      // Geofence (if any) already cleared by this point - the backend checks
      // it before the late-start gate - so this is the trainer being late.
      if (err instanceof ApiError && err.status === 409 && body?.code === "LATE_START" && !lateReason) {
        const info = err.body as { scheduledFor?: string | null };
        setLateStart({ photo, trainerCoords, venueOverride, scheduledFor: info.scheduledFor ?? null });
        return;
      }
      Alert.alert(
        "Couldn't start the session",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  const handleConfirmStartSession = async (photo: TrainerCheckInPhoto) => {
    if (!adminToken) return;
    setShowCheckInModal(false);
    // Location was already required and captured before the camera opened
    // (handleStartSession) - reuse it rather than asking again.
    await runStartSession(photo, startCoords);
  };

  // "Yes, update the venue location" from the OUTSIDE_VENUE prompt: re-runs
  // start with the chosen coordinates, which the backend writes onto the
  // venue + this conference and then starts.
  const handleUpdateVenueLocation = async (latitude: number, longitude: number) => {
    if (!outsideVenue) return;
    await runStartSession(outsideVenue.photo, outsideVenue.trainerCoords, { latitude, longitude });
  };

  // "No" - the session does not start (they must be at the venue to start).
  const dismissOutsideVenue = () => setOutsideVenue(null);

  // Late-start override: the trainer typed a reason for starting after the
  // scheduled time - retry the start with it (keeping any venue-location fix
  // made earlier in the flow). The backend logs the reason on the activity log.
  const handleSubmitLateStart = async (reason: string) => {
    if (!lateStart) return;
    await runStartSession(lateStart.photo, lateStart.trainerCoords, lateStart.venueOverride, reason);
  };

  const dismissLateStart = () => setLateStart(null);

  const handleMarkAttendance = async (
    traineeUid: string,
    status: "Present" | "Absent",
    reason: string,
  ) => {
    if (!adminToken) return;
    try {
      // The endpoint returns a fresh dashboard, so we can update in place
      // without waiting for the next poll.
      const fresh = await markAttendance(adminToken, conferenceUid, traineeUid, status, reason);
      setData(fresh);
    } catch (err) {
      Alert.alert(
        "Couldn't update attendance",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  const handleUnlockExam = async (traineeUid: string, reason: string) => {
    if (!adminToken) return;
    try {
      // Returns a fresh dashboard, so the row's LOCKED pill clears at once.
      setData(await unlockProctoring(adminToken, conferenceUid, traineeUid, reason));
    } catch (err) {
      Alert.alert(
        "Couldn't unlock the trainee",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  const handleStartModule = async (moduleKey: string) => {
    if (!adminToken) return;
    try {
      await startModule(adminToken, conferenceUid, moduleKey);
      loadData("silent");
    } catch (err) {
      Alert.alert(
        "Couldn't start the module",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  const handleStopActiveModule = async () => {
    if (!adminToken) return;
    try {
      await stopActiveModule(adminToken, conferenceUid);
      loadData("silent");
    } catch (err) {
      Alert.alert(
        "Couldn't end the module",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  const handleRestartModule = async (moduleKey: string) => {
    if (!adminToken) return;
    try {
      await restartModule(adminToken, conferenceUid, moduleKey);
      loadData("silent");
    } catch (err) {
      Alert.alert(
        "Couldn't restart the module",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  // "End Session" opens the Security Check-Out flow (face photo + signed
  // attendance sheet). Closing it without submitting leaves the session
  // running - it only ends once the backend confirms the check-out.
  const handleEndSession = () => setShowCheckOutModal(true);

  const handleConfirmEndSession = async (photo: UploadFile, attendanceSheet: UploadFile) => {
    if (!adminToken) return;
    setEndingSession(true);
    try {
      await endTraining(adminToken, conferenceUid, photo, attendanceSheet);
      setShowCheckOutModal(false);
      router.replace("/trainer_dashboard");
    } catch (err) {
      Alert.alert(
        "Couldn't end the session",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setEndingSession(false);
    }
  };

  const handleBottomNavSelect = (tab: DashboardTab) => {
    setBottomTab(tab);
    if (tab === "home") {
      router.replace("/trainer_dashboard");
    } else if (tab === "plan") {
      router.push("/sessions");
    } else if (tab === "profile") {
      router.push("/trainer_profile");
    } else if (tab === "more") {
      setMoreOpen(true);
    }
  };

  const isSessionClosed = data?.conferenceStatus === "Completed";
  // The backend is the source of truth for whether the session is live -
  // `hasStarted` is only an optimistic local flag so the UI flips the
  // instant the trainer taps Start (before the next poll lands). Without
  // this, navigating away and back showed "Start Session" / "Scheduled"
  // again even though the session was already Ongoing.
  const backendLive = data?.conferenceStatus === "Ongoing" || data?.conferenceStatus === "Live";
  // The join QR is only meaningful for a session that's actually running -
  // hide "Show QR" until Start Session, and again once it's closed.
  const isLive = !isSessionClosed && (hasStarted || backendLive);
  // A closed session already ran to completion, so its Audience Breakdown /
  // Assessment / Execution Flow etc. should render the same populated view as
  // an in-progress session instead of the "not started yet" empty state.
  const showSessionData = hasStarted || backendLive || isSessionClosed;
  // Gates the header's Start Session button - an unapproved session would
  // just bounce off the backend's 403 (see start_training), so hide the
  // action instead of letting the trainer hit a dead-end "not approved" alert.
  const isApproved = data ? data.approvalStatus === "Approved" : true;

  // A session can't be started before its scheduled date (backend enforces
  // this too). Compare "YYYY-MM-DD" strings against today's LOCAL date.
  const now = new Date();
  const todayISO = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const notYetDue = !!data?.conferenceDate && data.conferenceDate > todayISO;
  const startsOnLabel = data?.conferenceDate ? formatDisplayDate(data.conferenceDate) : undefined;

  return {
    router,
    conferenceUid,
    data,
    generatedAt: generatedAt ? formatGeneratedTimestamp(generatedAt) : undefined,
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
    lateStart,
    handleSubmitLateStart,
    dismissLateStart,
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
    liveQuizControls: {
      onBroadcast: handleBroadcastQuestion,
      onStopTimer: handleStopLiveTimer,
      onLeaderboard: handleShowLiveLeaderboard,
      onLobby: handleShowLiveLobby,
      onFinish: handleFinishLiveQuiz,
    },
    handleBottomNavSelect,
    isSessionClosed,
    showSessionData,
    isLive,
    isApproved,
    notYetDue,
    startsOnLabel,
  };
}
