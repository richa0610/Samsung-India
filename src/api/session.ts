import { USE_MOCK_DATA } from "@/config/dataSource";
import { apiRequest } from "./client";
import * as mock from "./mockService";

export type SessionModuleKey = "ATTENDANCE" | "STANDARD_TEST" | "LIVE_QUIZ" | "SURVEY";

// Field names mirror the /sessions/current response built from the
// `conference` table in the legacy database dump.
export type SessionModule = {
  key: SessionModuleKey;
  name: string;
  time: string | null;
  endTime: string | null;
  duration: string | null;
  isLive: boolean;
  isCompleted: boolean;
  isMissed: boolean;
  // Set on a post-attendance module until the trainee has checked in - the
  // module still shows its LIVE badge but the action is blocked, `lockReason`
  // says why. Attendance itself is never locked.
  isLocked?: boolean;
  lockReason?: string | null;
  completedAt: string | null;
  score: string | null;
  ranDuration?: string | null;
  assessmentSuiteUid: string | null;
};


export type SessionFlowState =
  | "JOINED"
  | "SECURE_CHECKIN"
  | "LOCATION_VERIFIED"
  | "CAMERA_VERIFIED"
  | "MARK_ATTENDANCE"
  | "ACCESS_GRANTED"
  | "ATTENDANCE_RECORDED";

export type AttendanceState = SessionFlowState;

export type CurrentSession = {
  conferenceUid: string;
  title: string;
  sessionType: string | null;
  date: string | null;
  location: string | null;
  trainerName: string | null;
  confirmationStatus: string;
  started: boolean;
  // True once this trainee has checked in (attendance recorded "Present").
  // The post-attendance modules stay locked until then.
  admitted?: boolean;
  // The trainee's own attendance row: null / "Joined" / "Present" / "Absent".
  // "Absent" is a hard eject - the app shows a full-screen block.
  attendanceStatus?: string | null;
  // On-device proctoring locked this trainee out of the post-test. Clears
  // when the trainer unlocks them from the Participant Master List.
  proctoringLocked?: boolean;
  // Company-level proctoring controls (admin-configurable per tenant) -
  // whether on-device proctoring should run at all, and how many warnings
  // it takes to lock a trainee out. See src/components/proctoring/violations.ts.
  liveProctoringEnabled?: boolean;
  proctoringMaxWarnings?: number;
  // The trainer has closed the session - drop back to the "no active session"
  // screen instead of the module timeline.
  sessionClosed?: boolean;
  startsAt: string | null;
  attendanceGeoFencing: boolean;
  securityCheckInCompleted?: boolean;
  attendanceState?: AttendanceState;
  flowState?: SessionFlowState;
  modules: SessionModule[];
};

export function getCurrentSession(token: string) {
  if (USE_MOCK_DATA) return mock.getCurrentSession(token);
  return apiRequest<CurrentSession>("/sessions/current", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// The training behind a shared QR code (samsungindia://join/<code>).
export type SessionJoinInfo = {
  conferenceUid: string;
  title: string;
  sessionType: string | null;
  date: string | null;
  location: string | null;
  trainerName: string | null;
  started: boolean;
  startsAt: string | null;
};

/** Public preview - no auth. Used by the join screen before login. */
export function getSessionJoinInfo(code: string) {
  return apiRequest<SessionJoinInfo>(`/sessions/join/${encodeURIComponent(code)}`);
}

/** Binds the logged-in trainee to the scanned training (and auto-approves
 *  a trainee who arrived via a trainer-shared QR). `viaRegistration` is set
 *  only by the scan-QR-then-register flow, so the trainer dashboard can tell
 *  a brand-new trainee (FRESH) from an existing one who logged in (UNASSIGNED). */
export function joinSession(code: string, token: string, viaRegistration = false) {
  const query = viaRegistration ? "?viaRegistration=true" : "";
  return apiRequest<SessionJoinInfo>(`/sessions/join/${encodeURIComponent(code)}${query}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

// --- Live Quiz (FFF): trainee view ----------------------------------------

export type LiveQuizState = "IDLE" | "WAITING" | "QUESTION_LIVE" | "LEADERBOARD" | "FINISHED" | string;

export type LiveQuizQuestion = {
  id: number;
  text: string;
  options: { id: string; text: string }[];
  order?: number;
  total?: number;
  timerSeconds?: number;
};

export type LiveQuizView = {
  state: LiveQuizState;
  conferenceUid: string;
  suiteUid: string | null;
  question: LiveQuizQuestion | null;
  timerEndsAt: number | null;
  // Server clock when this was sent (epoch ms) - for clock-skew-correct countdown.
  serverNowMs: number | null;
  alreadyAnswered: boolean;
};

export function getLiveQuizView(token: string, conferenceUid: string) {
  return apiRequest<LiveQuizView>(
    `/sessions/live-quiz?conferenceUid=${encodeURIComponent(conferenceUid)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
}

export type LiveAnswerResult = {
  accepted: boolean;
  correct?: boolean;
  correctOptionId?: string | null;
  explanation?: string | null;
};

export function submitLiveAnswer(
  token: string,
  conferenceUid: string,
  questionId: number,
  selectedOption: string | null,
) {
  return apiRequest<LiveAnswerResult>("/sessions/live-quiz/answer", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid, questionId, selectedOption }),
  });
}

/** Persist a post-test proctoring lockout onto the trainee's attendance row
 *  so the trainer's Participant Master List shows it and can unlock them. */
export function reportProctoringLock(
  token: string,
  conferenceUid: string,
  violationType: string,
  strikeNumber: number,
) {
  return apiRequest<{ locked: boolean }>("/sessions/proctoring-lock", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid, violationType, strikeNumber }),
  });
}

export type LiveReveal = {
  questionId: number;
  correctOptionId: string | null;
  explanation: string | null;
  yourOptionId: string | null;
};

export function revealLiveQuestion(token: string, conferenceUid: string, questionId: number) {
  return apiRequest<LiveReveal>(
    `/sessions/live-quiz/reveal?conferenceUid=${encodeURIComponent(conferenceUid)}&questionId=${questionId}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
}

// --- Live Quiz: end-of-quiz Assessment Map (read-only, before Final Submit) ---

export type LiveQuizQuestionStatus = "attempted" | "timed_out" | "skipped";

export type LiveQuizSummaryQuestion = {
  id: number;
  order: number;
  text: string;
  options: { id: string; text: string }[];
  status: LiveQuizQuestionStatus;
  yourOptionId: string | null;
  correctOptionId: string | null;
  explanation: string | null;
  responseMs: number | null;
};

export type LiveQuizSummary = {
  suiteUid: string | null;
  suiteTitle: string;
  totalQuestions: number;
  attemptedCount: number;
  skippedCount: number;
  timedOutCount: number;
  questions: LiveQuizSummaryQuestion[];
};

/** The calling trainee's per-question outcome map for a Live Quiz. */
export function getLiveQuizSummary(token: string, conferenceUid: string) {
  return apiRequest<LiveQuizSummary>(
    `/sessions/live-quiz/summary?conferenceUid=${encodeURIComponent(conferenceUid)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
}

/** A per-question timer ran out unanswered - records a blank answer so the
 *  Assessment Map can tell "timed out" from "skipped". Fire-and-forget. */
export function reportLiveQuizTimeout(token: string, conferenceUid: string, questionId: number) {
  return apiRequest<{ accepted: boolean }>("/sessions/live-quiz/timeout", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid, questionId }),
  });
}

export type LiveQuizSubmitResult = {
  submitted: boolean;
  totalScore: number;
  maxScore: number;
  percentage: number;
  correctCount: number;
  totalQuestions: number;
};

export function submitLiveQuiz(token: string, conferenceUid: string) {
  return apiRequest<LiveQuizSubmitResult>(
    `/sessions/live-quiz/submit?conferenceUid=${encodeURIComponent(conferenceUid)}`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } },
  );
}

export type LiveQuizRankRow = {
  rank: number;
  traineeUid: string;
  name: string;
  score: number;
  maxScore: number;
  percentage: number;
  totalResponseMs: number;
  isYou: boolean;
};

export type LiveQuizResults = {
  // "in_progress" | "submitted" | "ranked"
  state: string;
  finished: boolean;
  you: LiveQuizRankRow | null;
  correctCount: number;
  totalQuestions: number;
  durationSeconds: number;
  leaderboard: LiveQuizRankRow[];
};

export function getLiveQuizResults(token: string, conferenceUid: string) {
  return apiRequest<LiveQuizResults>(
    `/sessions/live-quiz/results?conferenceUid=${encodeURIComponent(conferenceUid)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
}

export type SessionHistoryItem = {
  conferenceUid: string;
  title: string;
  date: string | null;
  trainerName: string | null;
  attendanceStatus: string | null;
  score: string | null;
  passed: boolean | null;
};

// --- Trainee Dashboard (GET /sessions/dashboard) -------------------------
// Every field is derived from real attendance / assessment_results rows.

export type DashboardMetrics = {
  totalTrainings: number;
  present: number;
  absent: number;
  scheduled: number;
};

export type DashboardPerformance = {
  percentage: number;
  totalScore: number;
  maxScore: number;
  // (avg % last 30 days) - (avg % before). null when there isn't data on both
  // sides to compare - the "points this period" line is hidden then.
  periodGain: number | null;
};

export type DashboardRanking = {
  globalRank: number | null;
  globalTotal: number;
  globalPercentile: number | null;
  stateRank: number | null;
  stateTotal: number;
  statePercentile: number | null;
  stateName: string | null;
};

export type DashboardTrainingRow = {
  conferenceUid: string;
  title: string;
  date: string | null;
  // Raw "YYYY-MM-DD" - for date-range filtering (Training History screen).
  rawDate: string | null;
  day: string | null;
  // The trainee's outcome for this training.
  status: "Completed" | "Ongoing" | "Scheduled" | "Missed" | "Absent";
  postTestScore: string | null;
  quizScore: string | null;
  rank: string | null;
  rankScope: string | null;
};

export type TraineeDashboard = {
  conferenceUid: string | null;
  hasActiveSession: boolean;
  metrics: DashboardMetrics;
  performance: DashboardPerformance;
  ranking: DashboardRanking;
  trainings: DashboardTrainingRow[];
};

export function getTraineeDashboard(token: string, limit = 10) {
  return apiRequest<TraineeDashboard>(`/sessions/dashboard?limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getSessionHistory(token: string) {
  if (USE_MOCK_DATA) return mock.getSessionHistory(token);
  return apiRequest<SessionHistoryItem[]>("/sessions/history", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// Pure client-side navigation state (not backed by any endpoint, real or
// mock) - always the same implementation regardless of USE_MOCK_DATA.
export {
  setSecurityCheckInCompleted,
  getAttendanceState,
  setAttendanceState,
  getSessionFlowState,
  setSessionFlowState,
  resetSessionFlowState,
  isAttendanceRecorded,
  setPendingCheckIn,
  getPendingCheckIn,
  clearPendingCheckIn,
} from "@/api/mockService";
export type { PendingCheckIn } from "@/api/mockService";
export { ApiError } from "@/api/client";

