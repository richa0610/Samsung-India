import { USE_MOCK_DATA } from "@/config/dataSource";
import { apiRequest, apiUpload } from "./client";
import * as mock from "./mockService";

// Field names mirror the `trainee` table from the legacy database dump.
export type Trainee = {
  id: number;
  traineeUid: string;
  name: string;
  phone: number;
  email: string;
  gender: string | null;
  designation: string | null;
  employee_id: string | null;
  supervisorName: string | null;
  state: string | null;
  district: string | null;
  profilePhoto: string | null;
  status: string;
  workZone?: string | null;
  departmentSupport?: string | null;
  department?: string | null;
  sessionCode?: string | null;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  trainee: Trainee;
};

export type RegisterPayload = {
  name: string;
  phone: string;
  email: string;
  gender?: string;
  designation?: string;
  employee_id?: string;
  supervisorName?: string;
  state?: string;
  district?: string;
};

export function registerTrainee(payload: RegisterPayload) {
  if (USE_MOCK_DATA) return mock.registerTrainee(payload);
  return apiRequest<Trainee>("/trainees/register", {
    method: "POST",
    body: JSON.stringify({ ...payload, phone: Number(payload.phone) }),
  });
}

export function loginTrainee(phone: string) {
  if (USE_MOCK_DATA) return mock.loginTrainee(phone);
  return apiRequest<AuthSession>("/trainees/login", {
    method: "POST",
    body: JSON.stringify({ phone: Number(phone) }),
  });
}

export type UpdateProfilePayload = Partial<{
  name: string;
  phone: string;
  email: string;
  gender: string;
  designation: string;
  employee_id: string;
  supervisorName: string;
  state: string;
  district: string;
}>;

export function updateTrainee(token: string, payload: UpdateProfilePayload) {
  if (USE_MOCK_DATA) return mock.updateTrainee(token, payload);
  return apiRequest<AuthSession>("/trainees/me", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      ...payload,
      phone: payload.phone ? Number(payload.phone) : undefined,
    }),
  });
}

export type PickedImage = {
  uri: string;
  name: string;
  type: string;
};

export function uploadTraineePhoto(token: string, image: PickedImage) {
  if (USE_MOCK_DATA) return mock.uploadTraineePhoto(token, image);
  const formData = new FormData();
  formData.append("file", {
    uri: image.uri,
    name: image.name,
    type: image.type,
  } as unknown as Blob);

  return apiUpload<Trainee>("/trainees/me/photo", formData, token);
}

export { ApiError } from "./client";
