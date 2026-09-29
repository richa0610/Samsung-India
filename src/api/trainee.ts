import type { NewTraineeRecord } from "@/data/mockData";
import { apiRequest } from "./client";
import type { PageMeta } from "./training";

export type NewTraineeInput = Omit<NewTraineeRecord, "registeredAt" | "approvalStatus" | "updatedBy" | "updationOn" | "timestamp">;
export type TraineeListItem = NewTraineeRecord;

export function registerNewTrainee(token: string, payload: NewTraineeInput) {
  return apiRequest<NewTraineeRecord>("/admin/trainees", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export type TraineeSortKey =
  | "timestamp"
  | "traineeUid"
  | "name"
  | "trainerName"
  | "supervisorName"
  | "district"
  | "updatedBy"
  | "status";

export type TraineePage = PageMeta & {
  items: TraineeListItem[];
};

/** One page of the Trainee / Pending Trainee list. The server authorizes the rows
 *  (admin grant, or a trainer's assigned / rostered trainees), searches, sorts and pages. */
export function fetchTraineesPage(
  token: string,
  options: {
    mode: "all" | "pending";
    q?: string;
    sort?: TraineeSortKey;
    dir?: "asc" | "desc";
    cursor?: string | null;
    page?: number;
    limit?: number;
  },
) {
  const params = new URLSearchParams();
  params.set("mode", options.mode);
  if (options.page && options.page > 1) params.set("page", String(options.page));
  if (options.q?.trim()) params.set("q", options.q.trim());
  if (options.sort) params.set("sort", options.sort);
  if (options.dir) params.set("dir", options.dir);
  if (options.cursor) params.set("cursor", options.cursor);
  if (options.limit) params.set("limit", String(options.limit));
  return apiRequest<TraineePage>(`/admin/trainees/page?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export { ApiError } from "./client";
