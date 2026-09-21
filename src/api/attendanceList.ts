import { AdminFilters, adminFilterParams } from "./adminFilters";
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
  district: string | null;
  reportingManagerOfPromoter: string | null;
  attendanceStatus: string;
  markedAt: string | null;
  checkIn: string | null;
  checkOut: string | null;
  postTestScore: string | null;
  postTestScoreSummary: string | null;
  sessionTypeMethod: string | null;
  conferenceId: string | null;
  lastUpdates: string | null;
  updatedBy: string | null;
  updationOn: string | null;
  marked: boolean;
  // Tallies of this participant across all of this trainer's trainings - the
  // same numbers repeat on each of the participant's rows.
  trainerTrainingsTotal: number;
  trainerTrainingsPresent: number;
  trainerTrainingsPending: number;
};

/** `org` (admin accounts only) lists attendance across every trainer's trainings. */
export function fetchAttendanceList(token: string, org = false, filters?: AdminFilters) {
  const params = new URLSearchParams();
  if (org) params.set("org", "true");
  for (const [key, value] of adminFilterParams(filters)) params.set(key, value);
  const query = params.toString();
  return apiRequest<AttendanceListItem[]>(`/admin/attendance${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export { ApiError } from "./client";
