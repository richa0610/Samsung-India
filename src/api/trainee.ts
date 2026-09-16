import type { NewTraineeRecord } from "@/data/mockData";
import { apiRequest } from "./client";

export type NewTraineeInput = Omit<NewTraineeRecord, "registeredAt" | "approvalStatus" | "updatedBy" | "updationOn" | "timestamp">;
export type TraineeListItem = NewTraineeRecord;

export function registerNewTrainee(token: string, payload: NewTraineeInput) {
  return apiRequest<NewTraineeRecord>("/admin/trainees", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export function fetchTraineeList(token: string) {
  return apiRequest<TraineeListItem[]>("/admin/trainees", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export { ApiError } from "./client";
