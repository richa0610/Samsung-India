import { AdminFilters, adminFilterParams } from "./adminFilters";
import { apiRequest } from "./client";
import type { PageMeta } from "./training";

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

export type AttendanceMode = "all" | "pending" | "confirmed";

export type AttendancePage = PageMeta & {
  items: AttendanceListItem[];
};

/** Server sort keys the paged list understands (see GET /admin/attendance/page). */
export type AttendanceSortKey =
  | "markedAt"
  | "conferenceDate"
  | "region"
  | "product"
  | "session"
  | "audienceType"
  | "trainerName"
  | "trainerHoId"
  | "participantHoId"
  | "participantName"
  | "phone"
  | "state"
  | "district"
  | "reportingManagerOfPromoter"
  | "attendanceStatus"
  | "checkIn"
  | "checkOut"
  | "attendanceId"
  | "conferenceId";

/** One page of the admin org-wide attendance list. The server does the mode split,
 *  filtering, searching, sorting and paging (admin accounts only). */
export function fetchAttendancePage(
  token: string,
  options: {
    mode: AttendanceMode;
    filters?: AdminFilters;
    q?: string;
    sort?: AttendanceSortKey;
    dir?: "asc" | "desc";
    /** 1-based page number. */
    page?: number;
    /** "The rows after this one" - used to walk every page for export. */
    cursor?: string | null;
    limit?: number;
    /** Aborts the request when a newer one supersedes it. */
    signal?: AbortSignal;
  },
) {
  const params = new URLSearchParams();
  params.set("mode", options.mode);
  if (options.q?.trim()) params.set("q", options.q.trim());
  if (options.sort) params.set("sort", options.sort);
  if (options.dir) params.set("dir", options.dir);
  if (options.page && options.page > 1) params.set("page", String(options.page));
  if (options.cursor) params.set("cursor", options.cursor);
  if (options.limit) params.set("limit", String(options.limit));
  for (const [key, value] of adminFilterParams(options.filters)) params.set(key, value);
  return apiRequest<AttendancePage>(`/admin/attendance/page?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
    signal: options.signal,
  });
}

export { ApiError } from "./client";
