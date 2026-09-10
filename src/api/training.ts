import { SelectOption } from "@/components/ui/SearchableSelect";
import { apiRequest, apiUpload } from "./client";
// All types are preserved — they are used extensively across screens.

export type ModuleConfig = {
  category?: string;
  assessmentSuiteUid?: string;
  questionCount?: number;
  startTime?: string;
  endTime?: string;
  checkIn: boolean;
  unlockCondition?: string;
};

export type AssessmentSuiteOut = {
  assessmentSuiteUid: string;
  category: string;
  name: string;
  noOfQuestion: number;
};

export type AttendanceConfig = {
  checkInOpens?: string;
  checkOutCloses?: string;
  geoFencing: boolean;
  /** Metres from the venue a trainee may still check in (geoFencing on). */
  geoRadius?: number;
};

export type SessionFlowConfig = {
  attendance?: AttendanceConfig;
  standardTest?: ModuleConfig;
  liveQuiz?: ModuleConfig;
  survey?: ModuleConfig;
};

export type TrainingCreatePayload = {
  zone?: string;
  region?: string;
  company?: string;
  requestedBy?: string;

  trainerEmployeeId?: string;
  trainerName?: string;

  state?: string;
  district?: string;
  venue?: string;

  isResidential: boolean;
  conferenceDate: string;
  conferenceTime: string;
  trainingEndDate?: string;
  trainingHub?: string;
  audience?: string;
  sessionType?: string;
  trainingType?: string;
  batchSize?: string;

  sessionFlow?: SessionFlowConfig;
  checklist?: string[];
};

export type TrainingOut = {
  conferenceUid: string;
  conferenceStatus: string;
  status: string;
};

export type TrainingAgendaItem = {
  conferenceUid: string;
  title: string;
  trainerName: string | null;
  conferenceDate: string | null;
  conferenceTime: string | null;
  conferenceStatus: string;
  approvalStatus: string;
  location: string | null;
  batchSize: string | null;
  trainingType: string | null;
  state: string | null;
  trainingHub: string | null;
  traineeCount?: number;
  hoid: string | null;
  venueName: string | null;
  district: string | null;
  updatedBy: string | null;
  updationOn: string | null;
  timestamp: string | null;
};

export type TrainerAgendaResponse = {
  trainings: TrainingAgendaItem[];
  totalTrainees: number;
  totalSessions: number;
  completed: number;
  pending: number;
  executedPercentage: number;
  pendingPercentage: number;
  recentCompleted: TrainingAgendaItem[];
};

export type AudienceBreakdown = {
  total: number;
  present: number;
  absent: number;
  // Joined / on the list but not yet marked Present or Absent.
  notMarked: number;
  // On this trainer's roster vs. walked-in / joined by QR.
  assigned: number;
  unassigned: number;
  // First-timers - no earlier Present attendance in any other session.
  fresh: number;
};

export type AssessmentSummary = {
  pass: number;
  fail: number;
  totalAttempts: number;
};

export type TopPerformer = {
  traineeUid: string;
  name: string;
  score: number;
  maxScore: number;
  percentage: number;
};

export type SessionHeroStat = {
  moduleKey: string; // "LIVE_QUIZ" | "STANDARD_TEST"
  label: string;
  participants: number;
  averagePercent: number;
  bestPercent: number;
  topName: string | null;
};

export type TraineeRow = {
  traineeUid: string;
  name: string;
  employeeId: string | null;
  phone: number | null;
  audienceType: string;
  status: string; // "Present" | "Pending" | "Absent" | "Attempted"
  markedOn: string | null;
  checkOutTime: string | null;
  score: string | null;
  profilePhoto: string | null;
  // On-device proctoring lockout (post-test). Drives the red "LOCKED" pill +
  // the trainer's unlock control on the Participant Master List.
  isLocked: boolean;
  proctoringStrikes: number;
  proctoringMaxStrikes: number;
  proctoringLogs: string[];
};

export type ExecutionFlowStatus = "Pending" | "Running" | "Completed";

export type ExecutionFlowItem = {
  moduleKey: string;
  label: string;
  status: ExecutionFlowStatus;
  startedAt: string | null;
  endedAt: string | null;
  elapsedSeconds: number | null;
  assignedMinutes: number | null;
  // Backend says this module may be started now (session live, nothing else
  // running, every earlier module finished). Drives the per-row Start button.
  canStart: boolean;
  // Backend says this finished module may be re-run now (session live,
  // nothing else running). Drives the per-row Restart button.
  canRestart: boolean;
};

export type AuditLogEntry = {
  moduleKey: string;
  label: string;
  runNumber: number;
  startedAt: string | null;
  endedAt: string | null;
  elapsedSeconds: number | null;
  isRunning: boolean;
  startedBy: string | null;
  /** Free-text detail for a non-module event (e.g. a late-start override
   *  reason). null for ordinary module runs. */
  note: string | null;
};

export type LiveStudioQuestion = {
  id: number;
  order: number;
  text: string;
  timerSeconds: number;
  points: number;
  responseCount: number;
  isActive: boolean;
};

export type LiveStudio = {
  suiteUid: string;
  suiteTitle: string;
  state: "IDLE" | "WAITING" | "QUESTION_LIVE" | "LEADERBOARD" | "FINISHED" | string;
  activeQuestionId: number | null;
  timerEndsAt: number | null;
  // Server clock when this was sent (epoch ms) - for clock-skew-correct countdown.
  serverNowMs: number | null;
  participants: number;
  totalResponses: number;
  questions: LiveStudioQuestion[];
};

export type SessionDashboard = {
  conferenceUid: string;
  title: string;
  trainingType: string | null;
  conferenceDate: string | null;
  conferenceTime: string | null;
  trainerName: string | null;
  location: string | null;
  conferenceStatus: string;
  approvalStatus: string;
  activeModuleId: string | null;
  activeModuleQuestionCount: number | null;
  actualStartedAt: string | null;
  actualEndedAt: string | null;
  runtimeSeconds: number | null;
  audience: AudienceBreakdown;
  assessment: AssessmentSummary;
  topPerformers: TopPerformer[];
  trainees: TraineeRow[];
  executionFlow: ExecutionFlowItem[];
  auditLog: AuditLogEntry[];
  sessionHeroes: SessionHeroStat[];
  // Present only while LIVE_QUIZ is the active module.
  liveStudio: LiveStudio | null;
};

export function createTraining(token: string, payload: TrainingCreatePayload) {
  return apiRequest<TrainingOut>("/admin/trainings", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function fetchTrainerAgenda(token: string, range?: { start?: string; end?: string; all?: boolean }) {
  const params = new URLSearchParams();
  if (range?.start) params.set("start", range.start);
  if (range?.end) params.set("end", range.end);
  if (range?.all) params.set("all_sessions", "true");
  const query = params.toString();
  return apiRequest<TrainerAgendaResponse>(`/admin/trainings${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchSessionDashboard(token: string, conferenceUid: string) {
  return apiRequest<SessionDashboard>(`/admin/trainings/${encodeURIComponent(conferenceUid)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export type SessionReportParticipant = {
  userId: string;
  name: string;
  role: string;
  checkIn: string | null;
  checkOut: string | null;
  score: string | null;
};

export type SessionReport = {
  summary: {
    conferenceId: string;
    sessionName: string;
    date: string | null;
    state: string | null;
    schedule: string | null;
    duration: string | null;
    venueLink: string | null;
  };
  standardTest: SessionReportParticipant[];
  liveQuiz: SessionReportParticipant[];
};

export function fetchSessionReport(token: string, conferenceUid: string) {
  return apiRequest<SessionReport>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/report`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
}

export type StartTrainingLocation = {
  /** The trainer's own GPS at start - checked against the venue geofence. */
  latitude?: number;
  longitude?: number;
  /** Set only when the trainer corrects the venue location from the
   *  "you're not at the venue" prompt - persisted to the venue + conference. */
  venueLatitude?: number;
  venueLongitude?: number;
};

export function startTraining(
  token: string,
  conferenceUid: string,
  photo: { uri: string; name: string; type: string },
  location?: StartTrainingLocation,
  /** Reason for starting after the scheduled time - required by the backend
   *  (409 LATE_START) once the start time has passed, recorded on the
   *  activity log. */
  lateStartReason?: string,
) {
  const formData = new FormData();
  formData.append("photo", { uri: photo.uri, name: photo.name, type: photo.type } as unknown as Blob);
  const fields: [keyof StartTrainingLocation, number | undefined][] = [
    ["latitude", location?.latitude],
    ["longitude", location?.longitude],
    ["venueLatitude", location?.venueLatitude],
    ["venueLongitude", location?.venueLongitude],
  ];
  for (const [key, value] of fields) {
    if (value != null) formData.append(key, String(value));
  }
  if (lateStartReason?.trim()) formData.append("lateStartReason", lateStartReason.trim());
  return apiUpload<TrainingOut>(`/admin/trainings/${encodeURIComponent(conferenceUid)}/start`, formData, token);
}

export type UploadFile = { uri: string; name: string; type: string };

// Ending a session is a Security Check-Out: the trainer's face photo + the
// signed attendance sheet (PDF or image) are both required.
export function endTraining(
  token: string,
  conferenceUid: string,
  photo: UploadFile,
  attendanceSheet: UploadFile,
) {
  const formData = new FormData();
  formData.append("photo", { uri: photo.uri, name: photo.name, type: photo.type } as unknown as Blob);
  formData.append(
    "attendanceSheet",
    { uri: attendanceSheet.uri, name: attendanceSheet.name, type: attendanceSheet.type } as unknown as Blob,
  );
  return apiUpload<TrainingOut>(`/admin/trainings/${encodeURIComponent(conferenceUid)}/end`, formData, token);
}

// Manually opens one module. The trainer walks the flow forward one Start
// at a time - the backend rejects a start that's out of sequence or while
// another module is still live.
export function startModule(token: string, conferenceUid: string, moduleKey: string) {
  return apiRequest<TrainingOut>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/modules/${encodeURIComponent(moduleKey)}/start`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } },
  );
}

// Force-ends the currently live module without opening the next one. Never
// ends the session (only endTraining does that).
export function stopActiveModule(token: string, conferenceUid: string) {
  return apiRequest<TrainingOut>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/modules/stop-active`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } },
  );
}

// Re-runs a finished module. The backend rejects it while another module is
// still live.
export function restartModule(token: string, conferenceUid: string, moduleKey: string) {
  return apiRequest<TrainingOut>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/modules/${encodeURIComponent(moduleKey)}/restart`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } },
  );
}

// --- Live Quiz (FFF) broadcast console --------------------------------------

function liveQuizAction(token: string, conferenceUid: string, action: string, body?: unknown) {
  return apiRequest<SessionDashboard>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/live-quiz/${action}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: body === undefined ? undefined : JSON.stringify(body),
    },
  );
}

export function broadcastLiveQuestion(token: string, conferenceUid: string, questionId: number) {
  return liveQuizAction(token, conferenceUid, "broadcast", { questionId });
}

export function stopLiveTimer(token: string, conferenceUid: string) {
  return liveQuizAction(token, conferenceUid, "stop-timer");
}

export function showLiveLeaderboard(token: string, conferenceUid: string) {
  return liveQuizAction(token, conferenceUid, "leaderboard");
}

export function showLiveLobby(token: string, conferenceUid: string) {
  return liveQuizAction(token, conferenceUid, "lobby");
}

export function finishLiveQuiz(token: string, conferenceUid: string) {
  return liveQuizAction(token, conferenceUid, "finish");
}

export function markAttendance(
  token: string,
  conferenceUid: string,
  traineeUid: string,
  // Trainer confirming (Present) or overriding (Absent) a trainee's
  // attendance on the Participant Master List. "Absent" is a hard eject.
  status: "Present" | "Absent",
  reason: string,
) {
  return apiRequest<SessionDashboard>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/attendance/${encodeURIComponent(traineeUid)}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ status, reason }),
    }
  );
}

export function resetAttendance(token: string, conferenceUid: string, traineeUid: string) {
  return apiRequest<SessionDashboard>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/attendance/${encodeURIComponent(traineeUid)}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }
  );
}

/** Clear a trainee's on-device proctoring lockout from the Participant Master
 *  List - the trainer must give a reason (audit-logged). */
export function unlockProctoring(
  token: string,
  conferenceUid: string,
  traineeUid: string,
  reason: string,
) {
  return apiRequest<SessionDashboard>(
    `/admin/trainings/${encodeURIComponent(conferenceUid)}/attendance/${encodeURIComponent(traineeUid)}/unlock`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ reason }),
    }
  );
}

export function fetchAssessmentSuites(token: string) {
  return apiRequest<AssessmentSuiteOut[]>("/admin/assessment-suites", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchTrainerName(token: string, username: string) {
  return apiRequest<{ username: string; name: string }>(
    `/admin/trainers/${encodeURIComponent(username)}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
}

export function fetchTrainers(token: string, company?: string) {
  const query = company ? `?company=${encodeURIComponent(company)}` : "";
  return apiRequest<SelectOption[]>(`/admin/trainers${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchVenues(token: string, district?: string) {
  const query = district ? `?district=${encodeURIComponent(district)}` : "";
  return apiRequest<SelectOption[]>(`/admin/venues${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchChecklistItems(token: string) {
  return apiRequest<SelectOption[]>("/admin/checklist-items", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchTrainingHubs(token: string) {
  return apiRequest<SelectOption[]>("/admin/training-hubs", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchAudiences(token: string) {
  return apiRequest<SelectOption[]>("/admin/audiences", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchSessionTypes(token: string) {
  return apiRequest<SelectOption[]>("/admin/session-types", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchTrainingTypes(token: string) {
  return apiRequest<SelectOption[]>("/admin/training-types", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function fetchRequestedByOptions(token: string) {
  return apiRequest<SelectOption[]>("/admin/requested-by-options", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export type PendingSessionItem = {
  conferenceUid: string;
  title: string;
  trainerName: string | null;
  conferenceDate: string | null;
  conferenceTime: string | null;
  status: string;
};

export function fetchPendingTrainings(token: string) {
  return apiRequest<PendingSessionItem[]>("/admin/trainings/pending", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function approveTraining(token: string, conferenceUid: string) {
  return apiRequest<TrainingOut>(`/admin/trainings/${encodeURIComponent(conferenceUid)}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function rejectTraining(token: string, conferenceUid: string) {
  return apiRequest<TrainingOut>(`/admin/trainings/${encodeURIComponent(conferenceUid)}/reject`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export type QuestionOption = { id: string; text: string };

export type QuestionOut = {
  id: number;
  question: string;
  questionType: string;
  options: QuestionOption[];
  correctAnswer: string | null;
  points: number;
  timerSeconds: number | null;
  explanation: string | null;
  sortOrder: number;
};

export type QuestionCreatePayload = {
  question: string;
  questionType?: string;
  options?: QuestionOption[];
  correctAnswer?: string;
  points?: number;
  timerSeconds?: number;
  explanation?: string;
};

export type AssessmentSuiteDetail = {
  assessmentSuiteUid: string;
  title: string;
  description: string | null;
  category: string;
  testTime: string | null;
  type: string;
  noOfQuestion: number;
  questions: QuestionOut[];
};

export type AssessmentSuiteCreatePayload = {
  title: string;
  description?: string;
  category: string;
  testTime?: string;
  type?: string;
};

export function createAssessmentSuite(token: string, payload: AssessmentSuiteCreatePayload) {
  return apiRequest<AssessmentSuiteDetail>("/admin/assessment-suites", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function fetchAssessmentSuiteDetail(token: string, suiteUid: string) {
  return apiRequest<AssessmentSuiteDetail>(`/admin/assessment-suites/${encodeURIComponent(suiteUid)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function addAssessmentQuestion(token: string, suiteUid: string, payload: QuestionCreatePayload) {
  return apiRequest<AssessmentSuiteDetail>(`/admin/assessment-suites/${encodeURIComponent(suiteUid)}/questions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function deleteAssessmentQuestion(token: string, suiteUid: string, questionId: number) {
  return apiRequest<AssessmentSuiteDetail>(
    `/admin/assessment-suites/${encodeURIComponent(suiteUid)}/questions/${questionId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }
  );
}

export { ApiError } from "./client";
