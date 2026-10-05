import type { NewTraineeRecord } from "@/data/mockData";
import type { PickedImage } from "./auth";
import { apiRequest, apiUpload } from "./client";
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

/** The New Trainee form's profile photo, sent as a file once the trainee is registered. */
export function uploadNewTraineePhoto(token: string, traineeUid: string, image: PickedImage) {
  const formData = new FormData();
  formData.append("file", { uri: image.uri, name: image.name, type: image.type } as unknown as Blob);
  return apiUpload<NewTraineeRecord>(`/admin/trainees/${encodeURIComponent(traineeUid)}/photo`, formData, token);
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
    /** Registration date range, "YYYY-MM-DD" inclusive (empty = open-ended). */
    start?: string;
    end?: string;
    /** Aborts the request when a newer one replaces it. */
    signal?: AbortSignal;
  },
) {
  const params = new URLSearchParams();
  params.set("mode", options.mode);
  if (options.start) params.set("start", options.start);
  if (options.end) params.set("end", options.end);
  if (options.page && options.page > 1) params.set("page", String(options.page));
  if (options.q?.trim()) params.set("q", options.q.trim());
  if (options.sort) params.set("sort", options.sort);
  if (options.dir) params.set("dir", options.dir);
  if (options.cursor) params.set("cursor", options.cursor);
  if (options.limit) params.set("limit", String(options.limit));
  return apiRequest<TraineePage>(`/admin/trainees/page?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
    signal: options.signal,
  });
}

export { ApiError } from "./client";
