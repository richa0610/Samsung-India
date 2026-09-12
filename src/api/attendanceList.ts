import { apiRequest } from "./client";

export type AttendanceListItem = {
  attendanceId: string;
  region: string | null;
  product: string | null;
  session: string | null;
  audienceType: string | null;
  conferenceDate: string | null;
  trainerName: string | null;
  trainerHoId: string | null;
  participantHoId: string | null;
  participantName: string;
  phone: string | null;
  state: string | null;
  location: string | null;
  reportingManagerOfPromoter: string | null;
  attendanceStatus: string;
  checkIn: string | null;
  checkOut: string | null;
  postTestScore: string | null;
  postTestScoreSummary: string | null;
  sessionTypeMethod: string | null;
  conferenceId: string | null;
  lastUpdates: string | null;
  marked: boolean;
  // Tallies of this participant across all of this trainer's trainings - the
  // same numbers repeat on each of the participant's rows.
  trainerTrainingsTotal: number;
  trainerTrainingsPresent: number;
  trainerTrainingsPending: number;
};

export function fetchAttendanceList(token: string) {
  return apiRequest<AttendanceListItem[]>("/admin/attendance", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export { ApiError } from "./client";
