import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, Share } from "react-native";

import { ApiError } from "@/api/client";
import {
  SessionDashboard,
  UploadFile,
  broadcastLiveQuestion,
  checkTrainingSchedule,
  endTraining,
  fetchJoinLink,
  fetchSessionDashboard,
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
import { checkLocationPermission, getCurrentCoordinates } from "@/services/locationService";
import { formatDisplayDate } from "@/utils/formatDisplayDate";
import { formatGeneratedTimestamp } from "./formatting";
import { TrainerCheckInPhoto } from "./TrainerCheckInModal";

export type OutsideVenuePrompt = {
  photo: TrainerCheckInPhoto;
  distanceMeters: number;
  radius: number;
  trainerCoords: { latitude: number; longitude: number } | null;
  // True once this venue's location has already been corrected once
  // (OUTSIDE_VENUE_LOCKED) - the modal drops the "update the venue" option
  // and shows a hard block instead, since the one-time correction is used up.
  locked: boolean;
};

export type ScheduleOverridePrompt = {
  scheduledFor: string | null;
  // True when starting before the scheduled time, false when after - drives
  // "early"/"late" wording in the prompt.
  early: boolean;
  // Only set for the rare post-photo fallback (the schedule window was
  // crossed mid-flow, after the check-in photo was already taken) - absent
  // for the normal case, where this prompt appears right after "Start
  // Session" and the camera hasn't opened yet. See handleSubmitScheduleOverride.
  photo?: TrainerCheckInPhoto;
  trainerCoords?: { latitude: number; longitude: number } | null;
  venueOverride?: { latitude: number; longitude: number };
};

export function useSessionDashboardScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ conferenceUid?: string; from?: string }>();
  const conferenceUid = params.conferenceUid || "CONF25456581";
  const { admin, adminToken } = useAuth();
  const isAdmin = admin?.role === "admin" || params.from === "admin";

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
  const [scheduleOverride, setScheduleOverride] = useState<ScheduleOverridePrompt | null>(null);
  // Reason collected from the pre-camera schedule-override prompt (see
  // handleStartSession) - carried through every later start attempt (photo
  // capture, and any venue-location retry) so it's only ever asked once.
  const [pendingScheduleReason, setPendingScheduleReason] = useState<string | undefined>(undefined);
  const [showCheckOutModal, setShowCheckOutModal] = useState(false);
  const [endingSession, setEndingSession] = useState(false);
  // Confirm-before-end for the active module's own End button - opening the
  // popup is separate from actually stopping it, which only happens on
  // confirm.
  const [confirmEndModuleOpen, setConfirmEndModuleOpen] = useState(false);
  // Which module (if any) is blocking "End Session" from opening the
  // check-out flow - non-null shows the "modules still pending" popup.
  const [pendingModuleLabel, setPendingModuleLabel] = useState<string | null>(null);
  const [startedForUid, setStartedForUid] = useState(conferenceUid);
  const { requestLocationWithRationale } = useLocationPermission();

  if (startedForUid !== conferenceUid) {
    setStartedForUid(conferenceUid);
    setHasStarted(false);
  }

  // Pre-warm the location cache silently on mount so tapping "Start Session" resolves instantly (<50ms)
  useEffect(() => {
    checkLocationPermission()
      .then((status) => {
        if (status === "granted") {
          getCurrentCoordinates(1000).catch(() => {});
        }
      })
      .catch(() => {});
  }, []);

  // Background refreshes (the 5s poll and every Live Quiz nudge - one per trainee answer) are
  // coalesced: while one is on its way, further ones only mark "refresh again once it's back", so a
  // burst of nudges costs at most one request in flight plus one follow-up, never a pile of them.
  // User actions (start/stop/restart module) pass mode="action", which never skips or gets coalesced,
  // incrementing requestId so any in-flight background poll cannot overwrite the fresh state.
  const inFlight = useRef(false);
  const refreshAgain = useRef(false);
  const requestId = useRef(0);
  // A finished session's dashboard no longer changes by itself: it isn't polled (pull to refresh
  // and actions still reload it).
  const finished = useRef(false);
  // The follow-up refresh calls the latest `loadData` through this ref (kept current below).
  const loadDataRef = useRef<(mode?: "load" | "refresh" | "silent" | "action") => Promise<void>>(async () => {});

  const showDashboard = useCallback((res: SessionDashboard) => {
    setData(res);
    setGeneratedAt(new Date());
    finished.current = res.conferenceStatus === "Completed" || res.conferenceStatus === "Cancelled";
  }, []);

  // A Live Quiz button's reply is the dashboard as of that press - newer than any background
  // refresh still on its way, so it supersedes them (their replies are dropped) rather than being
  // overwritten a moment later, which would flip e.g. Stop Timer back to its old label.
  const showActionResult = useCallback(
    (res: SessionDashboard) => {
      ++requestId.current;
      inFlight.current = false;
      showDashboard(res);
    },
    [showDashboard],
  );

  const loadData = useCallback(
    async (mode: "load" | "refresh" | "silent" | "action" = "load") => {
      if (!adminToken) return;
      if (mode === "silent" && inFlight.current) {
        refreshAgain.current = true;
        return;
      }
      const id = ++requestId.current;
      inFlight.current = true;
      if (mode === "refresh") setRefreshing(true);
      else if (mode === "load") setLoading(true);

      try {
        const res = await fetchSessionDashboard(adminToken, conferenceUid);
        if (id === requestId.current) showDashboard(res);
      } catch {
        // Fallback / gracefully keep state
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoading(false);
        if (id === requestId.current) {
          inFlight.current = false;
          if (refreshAgain.current) {
            refreshAgain.current = false;
            loadDataRef.current("silent");
          }
        }
      }
    },
    [adminToken, conferenceUid, showDashboard],
  );
  useEffect(() => {
    loadDataRef.current = loadData;
  }, [loadData]);

  useFocusEffect(
    useCallback(() => {
      loadData();
      const interval = setInterval(() => {
        if (!finished.current) loadData("silent");
      }, 5000);
      return () => clearInterval(interval);
    }, [loadData]),
  );

  // Live Quiz room: every broadcast/answer nudge triggers a silent refetch so
  // the Live Studio card's questions / response counts / timer stay current
  // without waiting for the 5s poll.
  useLiveQuizChannel(conferenceUid, adminToken, () => loadData("silent"));

  const [broadcastingQuestionId, setBroadcastingQuestionId] = useState<number | null>(null);
  const [stoppingTimer, setStoppingTimer] = useState(false);
  const [showingLeaderboard, setShowingLeaderboard] = useState(false);
  const [showingLobby, setShowingLobby] = useState(false);

  const handleBroadcastQuestion = async (questionId: number) => {
    if (broadcastingQuestionId != null || !adminToken) return;
    setBroadcastingQuestionId(questionId);
    try {
      showActionResult(await broadcastLiveQuestion(adminToken, conferenceUid, questionId));
    } catch (err) {
      Alert.alert(
        "Broadcast Failed",
        err instanceof ApiError ? err.message : "Couldn't broadcast the question. Please try again.",
      );
    } finally {
      setBroadcastingQuestionId(null);
    }
  };
  // Stop Timer / Play Timer - pauses (or resumes) the question for the trainer and every trainee.
  // Sends the button the trainer sees, so the server never blindly toggles from a stale screen.
  const handleStopLiveTimer = async () => {
    if (stoppingTimer || !adminToken) return;
    const pause = data?.liveStudio?.timerRemainingMs == null;
    setStoppingTimer(true);
    try {
      showActionResult(await stopLiveTimer(adminToken, conferenceUid, pause));
    } catch (err) {
      Alert.alert(
        pause ? "Couldn't stop the timer" : "Couldn't restart the timer",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
      await loadData("action"); // show where the quiz really is now
    } finally {
      setStoppingTimer(false);
    }
  };
  const handleShowLiveLeaderboard = async () => {
    if (showingLeaderboard || !adminToken) return;
    setShowingLeaderboard(true);
    try {
      showActionResult(await showLiveLeaderboard(adminToken, conferenceUid));
    } catch {
      // Fallback / gracefully keep state.
    } finally {
      setShowingLeaderboard(false);
    }
  };
  const handleShowLiveLobby = async () => {
    if (showingLobby || !adminToken) return;
    setShowingLobby(true);
    try {
      showActionResult(await showLiveLobby(adminToken, conferenceUid));
    } catch {
      // Fallback / gracefully keep state.
    } finally {
      setShowingLobby(false);
    }
  };

  const handleCopyLink = async () => {
    if (!adminToken) return;
    try {
      // Same signed deep link the QR encodes - opens the app on the join screen
      // (samsungindia:// scheme, see app.json). Tapping it in a chat app
      // on an Android device with the app installed opens it directly.
      const link = await fetchJoinLink(adminToken, conferenceUid);
      await Share.share({ message: `Join the training session: ${link}` });
    } catch (err) {
      if (err instanceof ApiError) Alert.alert("Couldn't share", err.message);
    }
  };

  // Location is required to start a session - regardless of whether this
  // training has geofencing enforcement on. Fetched BEFORE the camera opens
  // (not after the photo, like before) and the flow stops here entirely if
  // it can't be obtained - no trainer photo capture, no session start,
  // without a live GPS fix. `useLocationPermission` already alerts on
  // blocked/unavailable; "denied"/cancelled need their own message since
  // that hook only sets internal error state for those, no visible alert.
  //
  // Schedule is checked next, still before the camera opens: if this start
  // is off-schedule, the trainer gives a reason right here, up front - the
  // camera only opens once that's resolved (or wasn't needed). The venue
  // geofence, by contrast, is only ever checked after the photo (see
  // runStartSession) since confirming location is naturally part of
  // submitting the actual start.
  const handleStartSession = async () => {
    setRequestingStartLocation(true);
    const { coords, status } = await requestLocationWithRationale();

    if (!coords) {
      setRequestingStartLocation(false);
      if (status === "denied") {
        Alert.alert(
          "Location required",
          "We couldn't get your live location. Location is required to start this session - please try again.",
        );
      }
      return;
    }

    setStartCoords(coords);

    if (!adminToken) {
      setRequestingStartLocation(false);
      return;
    }
    try {
      await checkTrainingSchedule(adminToken, conferenceUid);
      setRequestingStartLocation(false);
      setShowCheckInModal(true);
    } catch (err) {
      setRequestingStartLocation(false);
      const body = err instanceof ApiError ? (err.body as { code?: string } | null) : null;
      if (err instanceof ApiError && err.status === 409 && body?.code === "SCHEDULE_OVERRIDE") {
        const info = err.body as { scheduledFor?: string | null; early?: boolean };
        setScheduleOverride({ scheduledFor: info.scheduledFor ?? null, early: info.early ?? false });
        return;
      }
      Alert.alert(
        "Couldn't start the session",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    }
  };

  const runStartSession = async (
    photo: TrainerCheckInPhoto,
    trainerCoords: { latitude: number; longitude: number } | null,
    venueOverride?: { latitude: number; longitude: number },
    overrideReason?: string,
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
        overrideReason,
      );
      // Only flip to the "started" view once the backend actually confirms
      // it - e.g. an unapproved session gets rejected with a 403, and the
      // dashboard shouldn't show as live when nothing actually started.
      setOutsideVenue(null);
      setScheduleOverride(null);
      setPendingScheduleReason(undefined);
      setHasStarted(true);
      loadData("action");
    } catch (err) {
      const body = err instanceof ApiError ? (err.body as { code?: string } | null) : null;
      // OUTSIDE_VENUE offers the one-time "update the venue location?"
      // correction; OUTSIDE_VENUE_LOCKED is the same distance check but the
      // venue's location was already corrected once, so the modal shows a
      // hard block instead (see OutsideVenueModal). Both carry distance info
      // when raised from the actual radius check - the defensive case where
      // a locked venue rejects a resubmitted correction doesn't, and falls
      // through to the generic alert below.
      if (
        err instanceof ApiError &&
        err.status === 409 &&
        (body?.code === "OUTSIDE_VENUE" || body?.code === "OUTSIDE_VENUE_LOCKED") &&
        !venueOverride
      ) {
        const info = err.body as { distanceMeters?: number; radius?: number };
        if (info.distanceMeters != null && info.radius != null) {
          setOutsideVenue({
            photo,
            distanceMeters: info.distanceMeters,
            radius: info.radius,
            trainerCoords,
            locked: body?.code === "OUTSIDE_VENUE_LOCKED",
          });
          return;
        }
      }
      // Rare fallback: the schedule check already runs up front in
      // handleStartSession, before the camera even opens, so this normally
      // never fires - only if the off-schedule window was crossed mid-flow
      // (e.g. the trainer sat on the camera screen past the grace period).
      // Carries the photo/coords/venueOverride already in hand so
      // handleSubmitScheduleOverride can resubmit immediately instead of
      // re-opening the camera.
      if (err instanceof ApiError && err.status === 409 && body?.code === "SCHEDULE_OVERRIDE" && !overrideReason) {
        const info = err.body as { scheduledFor?: string | null; early?: boolean };
        setScheduleOverride({
          photo,
          trainerCoords,
          venueOverride,
          scheduledFor: info.scheduledFor ?? null,
          early: info.early ?? false,
        });
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
    // (handleStartSession) - reuse it rather than asking again. Same for the
    // schedule-override reason, if this start needed one.
    await runStartSession(photo, startCoords, undefined, pendingScheduleReason);
  };

  // "Yes, update the venue location" from the OUTSIDE_VENUE prompt: re-runs
  // start with the chosen coordinates, which the backend writes onto the
  // venue + this conference and then starts. Carries the schedule reason
  // through too - nothing was actually persisted on the request that hit
  // the geofence block, so it has to be resent on every retry.
  const handleUpdateVenueLocation = async (latitude: number, longitude: number) => {
    if (!outsideVenue) return;
    await runStartSession(
      outsideVenue.photo,
      outsideVenue.trainerCoords,
      { latitude, longitude },
      pendingScheduleReason,
    );
  };

  // "No" - the session does not start (they must be at the venue to start).
  const dismissOutsideVenue = () => setOutsideVenue(null);

  // The trainer typed a reason for starting earlier or later than planned.
  //  - Normal case (no photo attached to the prompt): this fired right after
  //    "Start Session", before the camera opened - stash the reason and open
  //    the camera now; it'll be sent along once the photo's taken.
  //  - Fallback case (photo attached): the window was crossed mid-flow after
  //    the photo was already captured - resubmit the real start immediately.
  const handleSubmitScheduleOverride = async (reason: string) => {
    if (!scheduleOverride) return;
    if (scheduleOverride.photo) {
      await runStartSession(
        scheduleOverride.photo,
        scheduleOverride.trainerCoords ?? null,
        scheduleOverride.venueOverride,
        reason,
      );
    } else {
      setPendingScheduleReason(reason);
      setScheduleOverride(null);
      setShowCheckInModal(true);
    }
  };

  const dismissScheduleOverride = () => setScheduleOverride(null);

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

  const [startingModuleKey, setStartingModuleKey] = useState<string | null>(null);
  const [restartingModuleKey, setRestartingModuleKey] = useState<string | null>(null);

  const handleStartModule = async (moduleKey: string) => {
    if (startingModuleKey != null || !adminToken) return;
    setStartingModuleKey(moduleKey);
    try {
      await startModule(adminToken, conferenceUid, moduleKey);
      // Optimistically flip the module to Running so the UI immediately
      // reflects the active module without flickering back to "Start".
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          activeModuleId: moduleKey,
          executionFlow: (prev.executionFlow || []).map((item) => {
            if (item.moduleKey === moduleKey) {
              return {
                ...item,
                status: "Running",
                startedAt: item.startedAt || new Date().toISOString(),
                canStart: false,
                canRestart: false,
              };
            }
            return {
              ...item,
              canStart: false,
            };
          }),
        };
      });
      await loadData("action");
    } catch (err) {
      Alert.alert(
        "Couldn't start the module",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
      await loadData("action");
    } finally {
      setStartingModuleKey(null);
    }
  };

  const handleStopActiveModule = () => setConfirmEndModuleOpen(true);
  const cancelStopActiveModule = () => setConfirmEndModuleOpen(false);

  const confirmStopActiveModule = async () => {
    setConfirmEndModuleOpen(false);
    if (!adminToken) return;
    const activeKey = data?.activeModuleId;
    try {
      await stopActiveModule(adminToken, conferenceUid);
      if (activeKey) {
        setData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            activeModuleId: null,
            executionFlow: (prev.executionFlow || []).map((item) => {
              if (item.moduleKey === activeKey) {
                return {
                  ...item,
                  status: "Completed",
                  endedAt: item.endedAt || new Date().toISOString(),
                  canStart: false,
                  canRestart: true,
                };
              }
              return item;
            }),
          };
        });
      }
      await loadData("action");
    } catch (err) {
      Alert.alert(
        "Couldn't end the module",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
      await loadData("action");
    }
  };

  const handleRestartModule = async (moduleKey: string) => {
    if (restartingModuleKey != null || !adminToken) return;
    setRestartingModuleKey(moduleKey);
    try {
      await restartModule(adminToken, conferenceUid, moduleKey);
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          activeModuleId: moduleKey,
          executionFlow: (prev.executionFlow || []).map((item) => {
            if (item.moduleKey === moduleKey) {
              return {
                ...item,
                status: "Running",
                startedAt: new Date().toISOString(),
                endedAt: null,
                elapsedSeconds: 0,
                canStart: false,
                canRestart: false,
              };
            }
            return {
              ...item,
              canStart: false,
            };
          }),
        };
      });
      await loadData("action");
    } catch (err) {
      Alert.alert(
        "Couldn't restart the module",
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
      await loadData("action");
    } finally {
      setRestartingModuleKey(null);
    }
  };

  // "End Session" opens the Security Check-Out flow (face photo + signed
  // attendance sheet). Closing it without submitting leaves the session
  // running - it only ends once the backend confirms the check-out.
  // Blocked while any configured module hasn't reached "Completed" yet -
  // covers both one still Running and any still Pending (never started).
  const handleEndSession = () => {
    const unfinished = data?.executionFlow?.find((m) => m.status !== "Completed");
    if (unfinished) {
      setPendingModuleLabel(unfinished.label);
      return;
    }
    setShowCheckOutModal(true);
  };
  const dismissPendingModuleNotice = () => setPendingModuleLabel(null);

  const handleConfirmEndSession = async (photo: UploadFile, attendanceSheet: UploadFile, totalPax: number) => {
    if (!adminToken) return;
    setEndingSession(true);
    try {
      await endTraining(adminToken, conferenceUid, photo, attendanceSheet, totalPax);
      setShowCheckOutModal(false);
      if (isAdmin) {
        router.replace("/admin_training_list");
      } else {
        router.replace("/trainer_dashboard");
      }
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
    } else if (tab === "today") {
      router.push({ pathname: "/sessions", params: { tab: "today" } });
    } else if (tab === "profile") {
      router.push("/trainer_profile");
    } else if (tab === "more") {
      setMoreOpen(true);
    }
  };

  const handleBack = () => {
    if (router.canGoBack()) {
      router.back();
    } else if (isAdmin) {
      router.replace("/admin_training_list");
    } else {
      router.replace("/sessions");
    }
  };

  const handleReport = () => {
    router.push({
      pathname: "/session_report",
      params: { conferenceUid, from: isAdmin ? "admin" : undefined },
    });
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
    liveQuizControls: {
      onBroadcast: handleBroadcastQuestion,
      onStopTimer: handleStopLiveTimer,
      onLeaderboard: handleShowLiveLeaderboard,
      onLobby: handleShowLiveLobby,
      broadcastingQuestionId,
      stoppingTimer,
      showingLeaderboard,
      showingLobby,
    },
    handleBottomNavSelect,
    isAdmin,
    handleBack,
    handleReport,
    isSessionClosed,
    showSessionData,
    isLive,
    isApproved,
    notYetDue,
    startsOnLabel,
  };
}
