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
};

export type LiveQuizControls = {
  onBroadcast: (questionId: number) => void;
  onStopTimer: () => void;
  onLeaderboard: () => void;
  onLobby: () => void;
};

export type ProctoringStatus = {
  flags: number;
  maxFlags: number;
  // Already-formatted strike / unlock lines from the backend
  // (`attendance.theftRemarks`), newest first.
  logs: string[];
};

export type ParticipantStatus = "PRESENT" | "ABSENT" | "PENDING";

export type ParticipantItem = {
  id: string;
  name: string;
  employeeId: string;
  phone: string;
  attendeeType: "ASSIGNED" | "NOT ALLOCATED";
  status: ParticipantStatus;
  inTime: string;
  outTime: string;
  proctoring?: ProctoringStatus;
};
