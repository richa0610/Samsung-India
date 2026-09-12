import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { Alert } from "react-native";

import { verifyLocation } from "@/api/attendance";
import {
  ApiError,
  AttendanceState,
  CurrentSession,
  SessionFlowState,
  SessionModuleKey,
  getCurrentSession,
  getSessionFlowState,
  isAttendanceRecorded,
  setSessionFlowState,
} from "@/api/session";
import { isSessionLocked, resetSessionViolations, setProctoringSettings } from "@/components/proctoring/violations";
import { useAuth } from "@/hooks/useAuth";
import { useLiveQuizChannel } from "@/hooks/useLiveQuizChannel";
import { useLocationPermission } from "@/hooks/useLocationPermission";

export type TraineeTab = "rank" | "dashboard" | "home" | "profile";

export interface SessionActivityData {
  id: string;
  key: SessionModuleKey;
  startTime: string;
  endTime: string;
  duration: string;
  type: string;
  title: string;
  isLive: boolean;
  isCompleted: boolean;
  isMissed: boolean;
  /** True when a Post Test was terminated due to security violation, or the
   *  trainer hasn't marked this trainee present yet. */
  isLocked?: boolean;
  /** Why the module is locked (admission gate) - shown on the card. */
  lockReason?: string | null;
  completedAt: string | null;
  score: string | null;
  ranDuration?: string | null;
  geoFencing?: boolean;
  securityCheckInCompleted?: boolean;
  attendanceState?: AttendanceState;
  /** Non-attendance module on a geofenced training - the trainee must pass a
   *  GPS check-in before "Enter Session" appears. See `locationGateStatus`. */
  locationGateEnabled?: boolean;
  locationGateStatus?: ModuleLocationGateStatus;
}

export type ModuleLocationGateStatus = "idle" | "checking" | "verified";

// Which conference's Live Quiz this trainee has already been pulled into (or
// left). Module scope so it survives `session_detail` remounting - the trainee
// gets auto-routed to the quiz room ONCE, and Leave stays Leave.
let autoEnteredLiveQuiz: string | null = null;

export function useTraineeHome() {
  const router = useRouter();
  // Post Test / Live Quiz / Survey completion is NOT carried in params any
  // more - the backend response is authoritative for those modules. These are
  // just the check-in wizard's client-only steps + the proctoring lock.
  const params = useLocalSearchParams<{
    flow?: SessionFlowState;
    attendance?: string;
    checkIn?: string;
    postTest?: string;
    score?: string;
    violation?: string;
  }>();
  const { trainee, token, logout } = useAuth();

  const [session, setSession] = useState<CurrentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [violationLockedVisible, setViolationLockedVisible] = useState(
    () =>
      params.violation === "locked" || params.postTest === "security_locked",
  );
  const [notAssigned, setNotAssigned] = useState(false);
  const [activeTab, setActiveTab] = useState<TraineeTab>("home");
  // Keyed by `${conferenceUid}:${moduleKey}` so a fresh training always
  // starts every non-attendance module back at "idle" - once per module per
  // session, per the attendance check-in's own behaviour.
  const [moduleLocationStatus, setModuleLocationStatus] = useState<
    Record<string, ModuleLocationGateStatus>
  >({});
  const { requestLocationWithRationale } = useLocationPermission();

  const loadSession = useCallback(
    async (mode: "load" | "refresh" | "silent" = "load") => {
      if (!token) return;
      if (mode === "refresh") setRefreshing(true);
      else if (mode === "load") setLoading(true);
      if (mode !== "silent") setError(null);

      try {
        const data: CurrentSession = await getCurrentSession(token);
        // Sync the company's proctoring on/off + max-warnings settings
        // before the trainee can reach post_test - see violations.ts.
        if (data.liveProctoringEnabled !== undefined && data.proctoringMaxWarnings !== undefined) {
          setProctoringSettings(data.liveProctoringEnabled, data.proctoringMaxWarnings);
        }
        // The backend `/sessions/current` response is the single source of
        // truth for every module's isLive / isCompleted / score / isMissed.
        // A module goes live ONLY when the trainer starts it
        // (conference.activeModuleId === key) and completes ONLY when a real
        // attendance row / assessment result exists. The trainer's actions
        // reach us in real time over the WebSocket (see useLiveQuizChannel
        // below), which triggers a silent refetch. The two client-only
        // overrides below are the only exceptions and each touches a single
        // module - they must never fake the state of the others.

        // (1) The trainee just submitted the Post Test in this navigation.
        // Show it done on the Standard Test card immediately so it doesn't
        // flash "live" for the one render before the backend result is read
        // back (submit_assessment commits before returning, so the next
        // fetch already has it - this just removes the flicker).
        if (params.postTest === "completed") {
          data.modules = data.modules.map((m) =>
            m.key === "STANDARD_TEST"
              ? {
                  ...m,
                  isCompleted: true,
                  isLive: false,
                  score: m.score ?? params.score ?? null,
                  completedAt: m.completedAt ?? "Completed successfully",
                }
              : m,
          );
        }

        // (2) The Post Test's on-device proctoring struck out. The lock is now
        // persisted on the trainee's attendance row (`data.proctoringLocked`),
        // so it survives a reload AND the trainer can clear it from the
        // Participant Master List. Once they do, drop the stale in-memory lock
        // so the trainee can re-enter the test. (`proctoringLocked` undefined
        // = older backend -> fall back to the nav-param-only behaviour.)
        if (data.proctoringLocked === false && data.conferenceUid) {
          resetSessionViolations(data.conferenceUid);
        }
        const postTestLocked =
          data.proctoringLocked === true ||
          (params.postTest === "security_locked" && data.proctoringLocked !== false);
        if (postTestLocked) {
          data.modules = data.modules.map((m) =>
            m.key === "STANDARD_TEST"
              ? {
                  ...m,
                  isCompleted: false,
                  isLive: false,
                  isLocked: true,
                  completedAt: "Security Violation",
                  score: null,
                }
              : m,
          );
        }

        // The check-in wizard runs through a few client-only steps
        // (SECURE_CHECKIN -> CAMERA_VERIFIED -> ATTENDANCE_RECORDED) before a
        // backend attendance row exists. Keep that sub-state in sync; once the
        // row is there, module.isCompleted from the backend is authoritative.
        const attendanceDone =
          isAttendanceRecorded() ||
          params.flow === "ATTENDANCE_RECORDED" ||
          params.attendance === "completed" ||
          data.modules.some((m) => m.key === "ATTENDANCE" && m.isCompleted);

        if (attendanceDone) {
          setSessionFlowState("ATTENDANCE_RECORDED");
          data.flowState = "ATTENDANCE_RECORDED";
        } else if (
          params.flow === "CAMERA_VERIFIED" ||
          params.checkIn === "verified"
        ) {
          setSessionFlowState("CAMERA_VERIFIED");
          data.flowState = "CAMERA_VERIFIED";
        } else if (params.flow === "SECURE_CHECKIN") {
          setSessionFlowState("SECURE_CHECKIN");
          data.flowState = "SECURE_CHECKIN";
        }

        setSession(data);
        setNotAssigned(false);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setSession(null);
          setNotAssigned(true);
        } else if (mode !== "silent") {
          setError(
            err instanceof ApiError
              ? err.message
              : "Couldn't load your session.",
          );
        }
      } finally {
        if (mode === "refresh") setRefreshing(false);
        else if (mode === "load") setLoading(false);
      }
    },
    [token, params.attendance, params.checkIn, params.flow, params.postTest, params.score],
  );

  useFocusEffect(
    useCallback(() => {
      setActiveTab("home");
      if (
        params.violation === "locked" ||
        params.postTest === "security_locked"
      ) {
        setViolationLockedVisible(true);
      }
      loadSession();
    }, [loadSession, params.violation, params.postTest]),
  );

  // The trainer has closed the session - the app drops back to the "no active
  // session" screen. Backend-authoritative (session_service.get_current_session
  // stops sending the module timeline once conferenceStatus is Completed).
  const sessionClosed = session?.sessionClosed === true;

  // The trainer hasn't started the session yet - the whole timeline renders
  // dimmed and non-interactive, and every module falls back to "Please Wait".
  const notStarted = session != null && !session.started && !sessionClosed;

  // The trainer marked this trainee Absent - a hard eject. The whole screen
  // is blocked until (if) the trainer flips them back to Present.
  const ejected =
    session != null && session.started && session.attendanceStatus === "Absent";

  // Session live, trainer hasn't marked this trainee Present yet: the timeline
  // still renders (with LIVE badges) but every module comes back locked from
  // the backend - no full-screen block, just per-module lock cards.

  // Push channel: any trainer action on this session (start/stop a module,
  // mark/unmark this trainee, start/end the session) nudges us to refetch,
  // so the screen updates in real time.
  const { connected: liveConnected } = useLiveQuizChannel(
    session?.conferenceUid,
    token,
    () => loadSession("silent"),
  );

  const allModulesDone =
    session != null &&
    session.modules.length > 0 &&
    session.modules.every((module) => module.isCompleted);
  const shouldPoll = notAssigned || !allModulesDone;

  useEffect(() => {
    if (!shouldPoll) return;
    // The WebSocket is the real-time path; this poll is only a safety net for
    // a missed nudge / dropped socket - so back right off while it's connected.
    const intervalMs = liveConnected ? 30000 : 12000;
    const interval = setInterval(() => loadSession("silent"), intervalMs);
    return () => clearInterval(interval);
  }, [shouldPoll, loadSession, liveConnected]);

  // Attendance is "recorded" once the backend has the row (module.isCompleted)
  // or the local check-in wizard just finished. Reaching the Post Test / Live
  // Quiz at all means the trainee is already admitted + checked in.
  const attendanceRecorded =
    isAttendanceRecorded() ||
    session?.flowState === "ATTENDANCE_RECORDED" ||
    getSessionFlowState() === "ATTENDANCE_RECORDED" ||
    params.flow === "ATTENDANCE_RECORDED" ||
    params.attendance === "completed" ||
    (session?.modules.some((m) => m.key === "ATTENDANCE" && m.isCompleted) ?? false);

  // Auto-enter the Live Quiz room the moment the trainer makes it the live
  // module, so the trainee is on the "waiting" screen BEFORE the first
  // question is broadcast - otherwise Q1's timer (anchored to broadcast time)
  // has already run out by the time they tap "Enter Live Quiz". Q2+ are fine
  // because they're already in the room. One-shot per conference; the manual
  // button and Leave still work.
  useEffect(() => {
    const uid = session?.conferenceUid;
    if (!uid || sessionClosed || notStarted || !attendanceRecorded) return;
    if (autoEnteredLiveQuiz === uid) return;
    const liveQuiz = session?.modules.find(
      (m) => m.key === "LIVE_QUIZ" && m.isLive && !m.isCompleted,
    );
    if (!liveQuiz) return;
    autoEnteredLiveQuiz = uid;
    router.push({ pathname: "/live_quiz", params: { conferenceUid: uid } });
  }, [session, sessionClosed, notStarted, attendanceRecorded, router]);

  const currentFlow: SessionFlowState = attendanceRecorded
    ? "ATTENDANCE_RECORDED"
    : params.flow === "CAMERA_VERIFIED" ||
        params.checkIn === "verified" ||
        session?.flowState === "CAMERA_VERIFIED"
      ? "CAMERA_VERIFIED"
      : session?.flowState || getSessionFlowState() || "SECURE_CHECKIN";

  const activities: SessionActivityData[] = (session?.modules ?? []).map(
    (module) => {
      const isAttendance = module.key === "ATTENDANCE";
      // Recorded either locally (self-check-in flow) or by the backend - the
      // trainer marking this trainee Present also completes Attendance.
      const isAttendanceCompleted =
        isAttendance && (currentFlow === "ATTENDANCE_RECORDED" || module.isCompleted);

      // `module.isLive` from the backend is the ONLY source of truth for
      // whether a module is live - it's true only once the trainer has
      // started that module (conference.activeModuleId === module.key).
      // No module auto-goes-live off the trainee's own progress any more.
      // (Attendance also drops the instant it's recorded locally, before
      // the next poll catches up.)
      const isLiveModule = isAttendance
        ? module.isLive && !isAttendanceCompleted
        : module.isLive;

      return {
        id: module.key,
        key: module.key,
        startTime: module.time ?? "--",
        endTime: module.endTime ?? "",
        duration: module.duration ?? "--",
        type: module.name,
        title: "Session Activity",
        isLive: notStarted ? false : isLiveModule,
        isCompleted: isAttendance ? isAttendanceCompleted : module.isCompleted,
        isMissed: module.isMissed,
        // `isLocked` here is only the security-violation lock (that path
        // builds its own activities array). The admission gate is carried
        // by `lockReason` instead, so the module keeps its LIVE badge while
        // its action is blocked.
        isLocked: false,
        lockReason: module.lockReason ?? null,
        completedAt: module.completedAt,
        score: module.score,
        // Actual "Ran : 45m 3s" badge from the trainer's Start/End - the
        // backend computes it from the activity log; no placeholder.
        ranDuration: module.ranDuration ?? null,
        geoFencing: isAttendance ? session?.attendanceGeoFencing : undefined,
        securityCheckInCompleted: isAttendance
          ? currentFlow === "CAMERA_VERIFIED" ||
            currentFlow === "MARK_ATTENDANCE" ||
            currentFlow === "ACCESS_GRANTED" ||
            currentFlow === "ATTENDANCE_RECORDED"
          : undefined,
        attendanceState: isAttendance ? currentFlow : undefined,
        locationGateEnabled: !isAttendance && !!session?.attendanceGeoFencing,
        locationGateStatus: isAttendance
          ? undefined
          : moduleLocationStatus[`${session?.conferenceUid}:${module.key}`] ?? "idle",
      };
    },
  );

  const blurActiveElement = () => {
    if (typeof document !== "undefined") {
      (document.activeElement as HTMLElement)?.blur?.();
    }
  };

  const handleMarkAttendance = () => {
    if (!session) return;
    blurActiveElement();
    const attendanceModule = session.modules.find(
      (module) => module.key === "ATTENDANCE",
    );
    // Admission gate - the trainer hasn't marked this trainee present yet,
    // so there's nothing for them to do here.
    if (attendanceModule?.lockReason) return;

    if (currentFlow === "ATTENDANCE_RECORDED") {
      return;
    }

    if (currentFlow === "CAMERA_VERIFIED") {
      // Step 5: Mark Attendance button opens Attendance verification
      setSessionFlowState("MARK_ATTENDANCE");
      router.push({
        pathname: "/attendance",
        params: {
          conferenceUid: session.conferenceUid,
          title: session.title,
          location: session.location ?? "",
          date: session.date ?? "",
          time: attendanceModule?.time ?? "",
          endTime: attendanceModule?.endTime ?? "",
        },
      });
    } else {
      // Step 2 -> Step 3: Secure Check-In button opens Location Verification
      setSessionFlowState("LOCATION_VERIFIED");
      router.push({
        pathname: "/secure_checkin",
        params: {
          conferenceUid: session.conferenceUid,
          title: session.title,
          location: session.location ?? "",
          date: session.date ?? "",
          time: attendanceModule?.time ?? "",
          endTime: attendanceModule?.endTime ?? "",
          mode: "entry",
        },
      });
    }
  };

  // Non-attendance modules on a geofenced training: the trainee taps
  // "Check-In to Enter", we fetch their live GPS (no camera, unlike
  // Attendance) and re-run the same venue distance check the backend already
  // exposes for Attendance. Reusing `verifyLocation` here since it's keyed
  // only by conferenceUid, not by module - it was never actually
  // attendance-specific.
  const handleCheckInToModule = async (moduleKey: SessionModuleKey) => {
    if (!session?.conferenceUid || !token) return;
    const statusKey = `${session.conferenceUid}:${moduleKey}`;
    setModuleLocationStatus((prev) => ({ ...prev, [statusKey]: "checking" }));

    const { coords, status, error: permError } = await requestLocationWithRationale();

    if (status !== "granted" || !coords) {
      setModuleLocationStatus((prev) => ({ ...prev, [statusKey]: "idle" }));
      if (permError) {
        Alert.alert("Location required", permError);
      }
      return;
    }

    try {
      const result = await verifyLocation(token, session.conferenceUid, coords.latitude, coords.longitude);
      if (result.withinRadius === false) {
        const radius = result.radiusMeters ?? 100;
        const away =
          result.distanceMeters != null ? ` (about ${Math.round(result.distanceMeters)} m away)` : "";
        Alert.alert(
          "You're too far from the venue",
          `Please come within the venue radius of ${radius} m to enter this module.${
            away ? `\n\nYou're currently${away}.` : ""
          }`,
        );
        setModuleLocationStatus((prev) => ({ ...prev, [statusKey]: "idle" }));
        return;
      }
      setModuleLocationStatus((prev) => ({ ...prev, [statusKey]: "verified" }));
    } catch (err) {
      Alert.alert(
        "Couldn't verify your location",
        err instanceof ApiError ? err.message : "Please try again.",
      );
      setModuleLocationStatus((prev) => ({ ...prev, [statusKey]: "idle" }));
    }
  };

  const handleEnterLiveQuiz = () => {
    blurActiveElement();
    // Mark it entered so leaving the quiz doesn't get auto-routed straight back.
    if (session?.conferenceUid) autoEnteredLiveQuiz = session.conferenceUid;
    router.push({
      pathname: "/live_quiz",
      params: { conferenceUid: session?.conferenceUid ?? "" },
    });
  };

  const handleEnterPostTest = () => {
    blurActiveElement();
    const standardTest = session?.modules.find(
      (module) => module.key === "STANDARD_TEST",
    );
    if (!session || !standardTest?.assessmentSuiteUid) return;

    const sessionKey = `${session.conferenceUid}_${standardTest.assessmentSuiteUid}`;
    // A trainer unlock (backend `proctoringLocked === false`) overrides both a
    // stale in-memory lock and the nav param that first flagged the lockout.
    const backendUnlocked = session.proctoringLocked === false;
    if (
      !backendUnlocked &&
      (session.proctoringLocked === true ||
        isSessionLocked(sessionKey) ||
        isSessionLocked(session.conferenceUid) ||
        params.postTest === "security_locked")
    ) {
      setViolationLockedVisible(true);
      return;
    }

    router.push({
      pathname: "/post_test",
      params: {
        conferenceUid: session.conferenceUid,
        suiteUid: standardTest.assessmentSuiteUid,
      },
    });
  };

  const handleEnterSurvey = () => {
    blurActiveElement();
    const survey = session?.modules.find((module) => module.key === "SURVEY");
    if (!session || !survey?.assessmentSuiteUid) return;
    router.push({
      pathname: "/survey",
      params: {
        conferenceUid: session.conferenceUid,
        suiteUid: survey.assessmentSuiteUid,
      },
    });
  };

  const handleLogout = () => {
    logout();
    router.replace("/");
  };

  const handleTabSelect = (tab: TraineeTab) => {
    setActiveTab(tab);
    if (tab === "rank") {
      // Pass the session so the Rank page resolves this conference's Live Quiz
      // board directly - it stays reachable here even after the session ends.
      router.push({
        pathname: "/quiz_leaderboard",
        params: { conferenceUid: session?.conferenceUid ?? "" },
      });
    } else if (tab === "dashboard") {
      router.push("/trainee_dashboard");
    } else if (tab === "profile") {
      router.push("/profile");
    } else if (tab === "home") {
      // Already on the session timeline - just pull fresh state.
      loadSession("refresh");
    }
  };

  return {
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
    violationLockedVisible,
    setViolationLockedVisible,
    loadSession,
    handleMarkAttendance,
    handleCheckInToModule,
    handleEnterLiveQuiz,
    handleEnterPostTest,
    handleEnterSurvey,
    handleLogout,
    handleTabSelect,
    router,
  };
}
