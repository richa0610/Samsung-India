/**
 * mockService.ts — All mock API implementations for the frontend-only demo.
 *
 * Every function maintains the SAME TypeScript signature as its real counterpart
 * so api/* files can simply re-export from here without any call-site changes.
 *
 * Mutable module-level state persists within a single app session (resets on restart).
 */

import {
  DEMO_ADMIN_SESSION_ADMIN,
  DEMO_ADMIN_SESSION_TRAINER,
  DEMO_ASSESSMENT_QUESTIONS,
  DEMO_AUTH_SESSION,
  DEMO_CURRENT_SESSION,
  DEMO_SESSION_HISTORY,
  DEMO_SURVEY_QUESTIONS,
  DEMO_TRAINEE,
  DEMO_TRAINER_PROFILE,
} from "@/data/mockData";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const delay = (ms = 650) => new Promise<void>((r) => setTimeout(r, ms));

// ─── Mutable in-memory state (module-level, resets on app restart) ─────────────
let _trainee = { ...DEMO_TRAINEE };
let _trainerProfile = { ...DEMO_TRAINER_PROFILE };

// ─── Admin Auth ───────────────────────────────────────────────────────────────
export async function loginAdmin(username: string, _password: string) {
  await delay();
  return username.trim().toLowerCase() === "admin"
    ? { ...DEMO_ADMIN_SESSION_ADMIN }
    : { ...DEMO_ADMIN_SESSION_TRAINER };
}

// ─── Trainee Auth ─────────────────────────────────────────────────────────────
export async function registerTrainee(payload: {
  name: string;
  phone: string;
  email: string;
  gender?: string;
  designation?: string;
  employee_id?: string;
  supervisorName?: string;
  state?: string;
  district?: string;
}) {
  await delay();
  _trainee = {
    ..._trainee,
    name: payload.name,
    phone: Number(payload.phone) || _trainee.phone,
    email: payload.email,
    gender: payload.gender ?? null,
    designation: payload.designation ?? null,
    employee_id: payload.employee_id ?? null,
    supervisorName: payload.supervisorName ?? null,
    state: payload.state ?? null,
    district: payload.district ?? null,
  };
  return { ..._trainee };
}

export async function loginTrainee(_phone: string) {
  await delay();
  return { ...DEMO_AUTH_SESSION, trainee: { ..._trainee } };
}

export async function updateTrainee(
  _token: string,
  payload: {
    name?: string;
    phone?: string;
    email?: string;
    gender?: string;
    designation?: string;
    employee_id?: string;
    supervisorName?: string;
    state?: string;
    district?: string;
  },
) {
  await delay();
  if (payload.name !== undefined) _trainee.name = payload.name;
  if (payload.phone !== undefined)
    _trainee.phone = Number(payload.phone) || _trainee.phone;
  if (payload.email !== undefined) _trainee.email = payload.email;
  if (payload.gender !== undefined) _trainee.gender = payload.gender || null;
  if (payload.designation !== undefined)
    _trainee.designation = payload.designation || null;
  if (payload.employee_id !== undefined)
    _trainee.employee_id = payload.employee_id || null;
  if (payload.supervisorName !== undefined)
    _trainee.supervisorName = payload.supervisorName || null;
  if (payload.state !== undefined) _trainee.state = payload.state || null;
  if (payload.district !== undefined)
    _trainee.district = payload.district || null;
  return {
    access_token: "demo-access-token-trainee",
    token_type: "bearer",
    trainee: { ..._trainee },
  };
}

export async function uploadTraineePhoto(
  _token: string,
  image: { uri: string; name: string; type: string },
) {
  await delay(1200);
  _trainee = { ..._trainee, profilePhoto: image.uri };
  return { ..._trainee };
}

// ─── Trainer Profile ───────────────────────────────────────────────────────────
export async function fetchTrainerProfile(_token: string) {
  await delay();
  return { ..._trainerProfile };
}

export async function updateTrainerProfile(_token: string, payload: Partial<typeof DEMO_TRAINER_PROFILE>) {
  await delay();
  _trainerProfile = { ..._trainerProfile, ...payload };
  return { ..._trainerProfile };
}

export async function uploadTrainerPhoto(
  _token: string,
  image: { uri: string; name: string; type: string },
) {
  await delay(1200);
  _trainerProfile = { ..._trainerProfile, profilePicture: image.uri };
  return { ..._trainerProfile };
}

// ─── Session ──────────────────────────────────────────────────────────────────
export type SessionFlowState =
  | "JOINED"
  | "SECURE_CHECKIN"
  | "LOCATION_VERIFIED"
  | "CAMERA_VERIFIED"
  | "MARK_ATTENDANCE"
  | "ACCESS_GRANTED"
  | "ATTENDANCE_RECORDED";

export type AttendanceState = SessionFlowState;

let _flowState: SessionFlowState = "JOINED";
let _attendanceRecorded = false;
let _currentSession = {
  ...DEMO_CURRENT_SESSION,
  modules: DEMO_CURRENT_SESSION.modules.map((m) => ({ ...m })),
};

export function isAttendanceRecorded(): boolean {
  return _attendanceRecorded || _flowState === "ATTENDANCE_RECORDED";
}

export function getSessionFlowState(): SessionFlowState {
  if (_attendanceRecorded) {
    return "ATTENDANCE_RECORDED";
  }
  return _flowState;
}

export function setSessionFlowState(state: SessionFlowState) {
  if (_attendanceRecorded && state !== "ATTENDANCE_RECORDED") {
    // Attendance was already recorded — keep it recorded for all tests!
    _flowState = "ATTENDANCE_RECORDED";
    return;
  }

  _flowState = state;

  if (state === "ATTENDANCE_RECORDED") {
    _attendanceRecorded = true;
    const att = _currentSession.modules.find((m) => m.key === "ATTENDANCE");
    if (att) {
      att.isCompleted = true;
      att.isLive = false;
      att.completedAt = att.completedAt ?? "10:25";
      att.ranDuration = att.ranDuration ?? "Ran : 45m 3s";
    }
    const quiz = _currentSession.modules.find((m) => m.key === "LIVE_QUIZ");
    if (quiz) {
      quiz.isLive = true;
      quiz.isCompleted = false;
    }
    const postTest = _currentSession.modules.find((m) => m.key === "STANDARD_TEST");
    if (postTest) {
      postTest.isLive = false;
      postTest.isCompleted = false;
    }
    const survey = _currentSession.modules.find((m) => m.key === "SURVEY");
    if (survey) {
      survey.isLive = false;
      survey.isCompleted = false;
    }
  }
}

export function resetSessionFlowState() {
  _flowState = "JOINED";
  _attendanceRecorded = false;
  const att = _currentSession.modules.find((m) => m.key === "ATTENDANCE");
  if (att) {
    att.isCompleted = false;
    att.isLive = true;
    att.completedAt = null;
    att.ranDuration = null;
  }
  const quiz = _currentSession.modules.find((m) => m.key === "LIVE_QUIZ");
  if (quiz) {
    quiz.isLive = false;
    quiz.isCompleted = false;
  }
}

export function getAttendanceState(): AttendanceState {
  return getSessionFlowState();
}

export function setAttendanceState(state: AttendanceState) {
  setSessionFlowState(state);
}

// Location + face photo captured on the Secure Check-In screen, held here
// until the "Mark Attendance" step submits them to /attendance/check-in/secure
// (a geofenced session needs the coordinates at submit time; the plain
// /attendance/check-in has none and is refused by the backend).
export type PendingCheckIn = { latitude: number; longitude: number; photoUri: string };
let _pendingCheckIn: PendingCheckIn | null = null;

export function setPendingCheckIn(pending: PendingCheckIn) {
  _pendingCheckIn = pending;
}
export function getPendingCheckIn(): PendingCheckIn | null {
  return _pendingCheckIn;
}
export function clearPendingCheckIn() {
  _pendingCheckIn = null;
}

export async function setSecurityCheckInCompleted(completed: boolean) {
  if (
    completed &&
    (_flowState === "JOINED" ||
      _flowState === "SECURE_CHECKIN" ||
      _flowState === "LOCATION_VERIFIED")
  ) {
    setSessionFlowState("CAMERA_VERIFIED");
  }
}

export async function getCurrentSession(_token: string) {
  await delay();

  if (_attendanceRecorded) {
    _flowState = "ATTENDANCE_RECORDED";
    const att = _currentSession.modules.find((m) => m.key === "ATTENDANCE");
    if (att) {
      att.isCompleted = true;
      att.isLive = false;
      att.completedAt = att.completedAt ?? "10:25";
      att.ranDuration = att.ranDuration ?? "Ran : 45m 3s";
    }
  }

  const isSecurityDone =
    _attendanceRecorded ||
    _flowState === "CAMERA_VERIFIED" ||
    _flowState === "MARK_ATTENDANCE" ||
    _flowState === "ACCESS_GRANTED" ||
    _flowState === "ATTENDANCE_RECORDED";

  return {
    ..._currentSession,
    flowState: _flowState,
    attendanceState: _flowState,
    securityCheckInCompleted: isSecurityDone,
    modules: _currentSession.modules.map((m) => ({ ...m })),
  };
}

export async function getSessionHistory(_token: string) {
  await delay();
  return DEMO_SESSION_HISTORY.map((h) => ({ ...h }));
}

// ─── Assessment Questions & Submit ────────────────────────────────────────────
export async function getAssessmentQuestions(_token: string, suiteUid: string) {
  await delay();
  const isSurvey = suiteUid.includes("survey");
  const isQuiz = suiteUid.includes("quiz");
  const questions = isSurvey
    ? DEMO_SURVEY_QUESTIONS
    : isQuiz
      ? DEMO_ASSESSMENT_QUESTIONS.slice(0, 4)
      : DEMO_ASSESSMENT_QUESTIONS;
  const title = isSurvey
    ? "SECs Feedback | June\nClassroom Training Sessions"
    : isQuiz
      ? "Galaxy AI Live Quiz"
      : "Samsung Galaxy S26 Post Test";

  return {
    title,
    testTime: isSurvey ? null : isQuiz ? "2" : "30",
    questions: questions.map((q) => ({ ...q, options: [...q.options] })),
  };
}

export async function submitAssessment(
  _token: string,
  suiteUid: string,
  _conferenceUid: string,
  answers: { questionId: number; selectedOption: string | null }[],
) {
  await delay(900);
  const isSurvey = suiteUid.includes("survey");
  const isQuiz = suiteUid.includes("quiz");
  const isPostTest = !isSurvey && !isQuiz;

  const questions = isSurvey
    ? DEMO_SURVEY_QUESTIONS
    : isQuiz
      ? DEMO_ASSESSMENT_QUESTIONS.slice(0, 4)
      : DEMO_ASSESSMENT_QUESTIONS;
  const totalQuestions = answers.length || (isQuiz ? 4 : isSurvey ? 4 : 15);
  let correctCount = 0;
  answers.forEach((ans, idx) => {
    const q =
      questions.find((item) => item.id === ans.questionId) ?? questions[idx];
    const correctAnswer = (q as { correctAnswer?: string | null })
      ?.correctAnswer;
    if (q && ans.selectedOption && ans.selectedOption === correctAnswer) {
      correctCount++;
    }
  });

  if (answers.length === 0) {
    correctCount = isQuiz ? 3 : 12;
  }

  const scoreStr = isSurvey ? null : `${correctCount}/${totalQuestions}`;

  _currentSession = {
    ..._currentSession,
    modules: _currentSession.modules.map((m) => {
      if (isQuiz && m.key === "LIVE_QUIZ") {
        return {
          ...m,
          isCompleted: true,
          isLive: false,
          score: scoreStr ?? "9/15",
          completedAt: "Completed successfully",
          ranDuration: "Ran : 1h 55m",
        };
      }
      if (isQuiz && m.key === "STANDARD_TEST") {
        return {
          ...m,
          isLive: true,
        };
      }
      if (isPostTest && m.key === "LIVE_QUIZ") {
        return {
          ...m,
          isCompleted: true,
          isLive: false,
          score: m.score ?? "9/15",
          completedAt: "Completed successfully",
          ranDuration: m.ranDuration ?? "Ran : 1h 55m",
        };
      }
      if (isPostTest && m.key === "STANDARD_TEST") {
        return {
          ...m,
          isCompleted: true,
          isLive: false,
          score: scoreStr ?? "12/15",
          completedAt: "Completed successfully",
          ranDuration: "Ran : 1h 50m",
        };
      }
      if (isPostTest && m.key === "SURVEY") {
        return {
          ...m,
          isLive: true,
          isCompleted: false,
        };
      }
      if (isSurvey && m.key === "SURVEY") {
        return {
          ...m,
          isCompleted: true,
          isLive: false,
          completedAt: "Completed successfully",
          ranDuration: "Ran : 25m",
        };
      }
      return m;
    }),
  };

  return {
    totalScore: correctCount,
    maxScore: totalQuestions,
    percentage: Math.round((correctCount / totalQuestions) * 100),
    correctCount,
    totalQuestions,
  };
}

/**
 * Terminates a Post Test due to a security violation.
 * Marks the test as locked — does NOT complete it successfully.
 * Survey remains Upcoming (not unlocked).
 */
export async function terminateAssessmentWithViolation(
  _token: string,
  suiteUid: string,
  _conferenceUid: string,
  violationType: string,
  answers: { questionId: number; selectedOption: string | null }[],
) {
  await delay(400);
  const isPostTest = !suiteUid.includes("survey") && !suiteUid.includes("quiz");
  if (!isPostTest) return { locked: false };

  _currentSession = {
    ..._currentSession,
    modules: _currentSession.modules.map((m) => {
      if (m.key === "ATTENDANCE") {
        return {
          ...m,
          isCompleted: true,
          isLive: false,
          completedAt: m.completedAt ?? "10:25",
          ranDuration: m.ranDuration ?? "Ran : 45m 3s",
        };
      }
      if (m.key === "LIVE_QUIZ") {
        return {
          ...m,
          isCompleted: true,
          isLive: false,
          score: m.score ?? "9/15",
          completedAt: "Completed successfully",
          ranDuration: m.ranDuration ?? "Ran : 1h 55m",
        };
      }
      if (m.key === "STANDARD_TEST") {
        return {
          ...m,
          isCompleted: false,
          isLive: false,
          isLocked: true,
          completedAt: `Security Violation: ${violationType}`,
          score: null,
          ranDuration: null,
        };
      }
      // Survey stays Upcoming — not unlocked by a violated post test
      return m;
    }),
  };

  return { locked: true, violationType, attemptedCount: answers.length };
}

