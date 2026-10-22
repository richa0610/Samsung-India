import type { ParticipantModuleProgress } from "@/api/training";

export type TopPerformer = {
  id: string;
  name: string;
  score: number;
  maxScore: number;
  percentage: number;
};

export type LiveStudioQuestion = {
  id: number;
  qNumber: string;
  timerSecs: number;
  questionText: string;
  points: number;
  responseCount: number;
  isActive: boolean;
  /** Already went live and is over. */
  wasBroadcast?: boolean;
};

export type LiveQuizControls = {
  onBroadcast: (questionId: number) => void;
  onStopTimer: () => void;
  onLeaderboard: () => void;
  onLobby: () => void;
  broadcastingQuestionId?: number | null;
  stoppingTimer?: boolean;
  showingLeaderboard?: boolean;
  showingLobby?: boolean;
};

export type ProctoringStatus = {
  flags: number;
  maxFlags: number;
  // Already-formatted strike / unlock lines from the backend
  // (`attendance.theftRemarks`), newest first.
  logs: string[];
  /** Times a trainer already unlocked them in this training, and the most allowed - once equal,
   *  the server refuses another unlock. */
  unlocksUsed: number;
  maxUnlocks: number;
};

export type ParticipantStatus = "PRESENT" | "ABSENT" | "NOT_MARKED";

export type ParticipantItem = {
  id: string;
  name: string;
  employeeId: string;
  phone: string;
  /** How they reached the session - shown as ASN / UASN / FRESH under the phone number. */
  attendeeType: "ASSIGNED" | "UNASSIGNED" | "FRESH";
  status: ParticipantStatus;
  /** "Attendance" once marked Present, else "Not Started". */
  stage: string;
  stageModules: ParticipantModuleProgress[];
  inTime: string;
  outTime: string;
  /** Latest Post Test score ("95%"), or null before they've submitted one. */
  score: string | null;
  /** Green when it passes, red when it doesn't; null without a score. */
  scorePassed: boolean | null;
  proctoring?: ProctoringStatus;
  /** Times a trainer has unlocked them in this training, and the most allowed - locked or not. */
  unlocks?: { used: number; max: number };
};
